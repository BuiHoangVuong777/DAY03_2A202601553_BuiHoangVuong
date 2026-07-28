"""
🌐 WEB SERVER cho ReAct Agent (Lab 3: Chatbot vs ReAct Agent)
FastAPI + SSE streaming, tái sử dụng trực tiếp run_react_agent() từ src/app.py.

Chạy:
    uvicorn server:app --reload --port 8000
Mở:
    http://localhost:8000

Endpoints:
    GET  /            -> index.html (chat UI)
    GET  /api/status  -> thông tin provider/model + trạng thái session
    GET  /api/chat    -> SSE stream các event của ReAct loop (message=<query>)
    POST /api/reset   -> xóa lịch sử hội thoại, bắt đầu session mới
"""

import json
import os
import sys
import threading

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from starlette.background import BackgroundTask

# ----------------------------------------------------------------------------
# Import agent core từ src/
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

load_dotenv(os.path.join(BASE_DIR, ".env"))

from app import MAX_ITERATIONS, _init_messages, run_react_agent  # noqa: E402
from providers import get_llm_provider  # noqa: E402

app = FastAPI(title="VinUni Course Agent - Lab 3")

# ----------------------------------------------------------------------------
# Session state (single-user demo — giống vòng lặp CLI trong src/app.py)
# ----------------------------------------------------------------------------
_state = {
    "llm": None,
    "messages": None,
    "step_offset": 0,
    "turn": 0,
    "init_error": None,
    "busy": False,  # đang có 1 turn ReAct chạy dở hay không
}
_lock = threading.Lock()  # mutex ngắn, chỉ bảo vệ việc đọc/ghi _state


def _get_llm():
    """
    Khởi tạo LLM lazily (giống __main__ của app.py).
    Nếu lần trước lỗi (vd: thiếu API key) thì lần gọi sau vẫn thử lại,
    để sửa .env xong chỉ cần refresh trang, không phải restart server.
    """
    if _state["llm"] is None:
        try:
            _state["llm"] = get_llm_provider()
            _state["messages"] = _init_messages()
            _state["init_error"] = None
        except Exception as e:  # thiếu API key, v.v.
            _state["init_error"] = str(e)
    return _state["llm"]


def _sse(payload: dict) -> str:
    """Đóng gói 1 event thành 1 frame Server-Sent Events."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/status")
def status():
    llm = _get_llm()
    if llm is None:
        return {
            "ok": False,
            "error": _state["init_error"],
        }
    return {
        "ok": True,
        "provider": getattr(llm, "_provider_name", "?"),
        "model": getattr(llm, "model_name", None) or getattr(llm, "model", "?"),
        "turn": _state["turn"],
        "history_messages": len(_state["messages"] or []),
        "max_iterations": MAX_ITERATIONS,
    }


@app.post("/api/reset")
def reset():
    with _lock:
        # Turn đang chạy (nếu có) giữ tham chiếu tới list messages CŨ,
        # nên gán list mới ở đây là an toàn, không cần chờ nó kết thúc.
        _state["messages"] = _init_messages()
        _state["step_offset"] = 0
        _state["turn"] = 0
    return {"ok": True}


@app.get("/api/chat")
def chat(message: str = Query(..., min_length=1)):
    llm = _get_llm()
    if llm is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": f"Chưa cấu hình LLM provider: {_state['init_error']}. "
                "Thiết lập LLM_PROVIDER và API key trong file .env ở thư mục gốc."
            },
        )

    # Chặn 2 turn chạy song song (state hội thoại chỉ có 1 session)
    with _lock:
        if _state["busy"]:
            return JSONResponse(
                status_code=409,
                content={"error": "Agent đang xử lý một câu hỏi khác. Vui lòng đợi."},
            )
        _state["busy"] = True
        _state["turn"] += 1
        turn = _state["turn"]
        messages = _state["messages"]
        step_offset = _state["step_offset"]

    def _release():
        """Idempotent — gọi được nhiều lần mà không lỗi."""
        with _lock:
            _state["busy"] = False

    def event_stream():
        steps_used = 0
        try:
            yield _sse({"type": "turn_start", "turn": turn})

            # ReAct loop — yield từng event ngay khi xảy ra (stream thật)
            for event in run_react_agent(message, llm, messages, step_offset):
                step = event.get("step")
                if isinstance(step, int):
                    steps_used = max(steps_used, step - step_offset)
                yield _sse(event)

            yield _sse({"type": "done", "turn": turn})
        except Exception as e:
            yield _sse({"type": "error", "step": None, "content": f"Server error: {e}"})
            yield _sse({"type": "done", "turn": turn})
        finally:
            # Giữ đánh số step liên tục theo số bước thực tế của turn.
            with _lock:
                _state["step_offset"] += max(steps_used, 1)
            _release()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        # Chốt chặn: nếu client ngắt kết nối trước khi generator kịp chạy,
        # busy vẫn được gỡ, tránh server kẹt 409 vĩnh viễn.
        background=BackgroundTask(_release),
    )


if __name__ == "__main__":
    import uvicorn

    # Mặc định 127.0.0.1: uvicorn sẽ in ra link bấm vào được ngay.
    # (Đừng mở http://0.0.0.0:8000 trên trình duyệt — Chrome báo ERR_ADDRESS_INVALID.
    #  0.0.0.0 chỉ là địa chỉ server LẮNG NGHE, không phải địa chỉ để truy cập.)
    # Muốn máy khác trong cùng mạng LAN vào được: set HOST=0.0.0.0 rồi truy cập
    # bằng IP thật của máy này (vd: http://192.168.1.5:8000).
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print(f"\n🌐 Mở trình duyệt tại: http://localhost:{port}\n")
    uvicorn.run("server:app", host=host, port=port, reload=True)
