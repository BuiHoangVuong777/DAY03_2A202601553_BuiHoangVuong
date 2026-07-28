"""
🚀 CORE AGENT APP (Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + LLM Provider.
LLM Provider trả về LangChain ChatModel (gọi .invoke() để sử dụng).
"""

import json
import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, search_ai_courses, get_ai_course_detail
from tools import check_course_readiness, get_learning_track, filter_courses_by_constraints
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_query(tc: dict) -> str:
    """Chuyển test case dạng {input: {...}} thành câu hỏi tự nhiên cho LLM."""
    inp = tc["input"]
    return (
        f"Mình {inp['level']}, "
        f"muốn {inp['goal']}, "
        f"thời gian rảnh {inp['free_time']}, "
        f"ngân sách {inp['budget']}."
    )


def run_baseline_chatbot(user_query: str, llm):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    Gọi LangChain ChatModel.invoke() với system_prompt + user_query.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()[:120]}...")

    messages = [
        SystemMessage(content=CHATBOT_BASELINE_PROMPT),
        HumanMessage(content=user_query),
    ]
    response = llm.invoke(messages)
    print(f"🤖 Chatbot trả lời:\n{response.content}")


def run_react_agent(user_query: str, llm):
    """
    Dựng vòng lặp ReAct Agent (Thought → Action → Observation) có Guardrails.
    ⚠️  Hiện tại là MOCK — mô phỏng Thought/Action/Observation bằng script cố định.
        Sẽ thay bằng ReAct loop thực sự (gọi LLM → parse → dispatch tool) ở bước sau.
    """
    print(f"\n🤖 [REACT AGENT — MOCK] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {REACT_SYSTEM_PROMPT.strip()[:120]}...")

    step = 0
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        if step == 1:
            # Mô phỏng LLM suy luận: cần tìm lộ trình học phù hợp
            print("🧠 Thought: Người dùng muốn học Python nền tảng, cần tìm lộ trình.")
            print("🛠️ Action: get_learning_track['python nền tảng']")

            obs = get_learning_track("python nền tảng")
            print(f"👁️ Observation:\n{obs}")

        elif step == 2:
            # Mô phỏng LLM đã có đủ thông tin từ Observation → trả lời
            print("🧠 Thought: Đã có lộ trình học, giờ tôi có thể tư vấn cho người dùng.")
            print(
                "🏁 Final Answer: Dựa trên hồ sơ của bạn, bạn nên bắt đầu từ Python nền tảng. "
                "Lộ trình gồm PY101 → PY102. Hãy bắt đầu với khóa PY101 (Python nhập môn) "
                "vì bạn chưa biết gì và ngân sách thấp."
            )
            break

    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn {MAX_ITERATIONS} bước. Ngắt an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo LangChain ChatModel qua get_llm_provider
    try:
        llm = get_llm_provider()
    except ValueError as e:
        print(f"\n⚠️  Chưa cấu hình API key: {e}")
        print("💡 Thiết lập trong file .env (xem .env.example), hoặc chạy:")
        print('   export LLM_PROVIDER="openai" && export OPENAI_API_KEY="sk-..."')
        sys.exit(1)

    model_id = getattr(llm, "model_name", None) or getattr(llm, "model", "?")
    provider_name = getattr(llm, "_provider_name", "?")
    print(f"🔌 Provider   : {provider_name}")
    print(f"🤖 ChatModel  : {llm.__class__.__name__}")
    print(f"🔧 Model      : {model_id}")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases")

    # Chọn test case đầu tiên để demo
    sample_tc = tests[0]
    sample_query = _build_query(sample_tc)
    print(f"📋 Test case : {sample_tc['id']}")
    print(f"👤 Query     : {sample_query}\n")

    print("─── DEMO 1: CHATBOT BASELINE (không có Tools) ───")
    run_baseline_chatbot(sample_query, llm)

    print("\n─── DEMO 2: REACT AGENT (có Tools — MOCK) ───")
    run_react_agent(sample_query, llm)
