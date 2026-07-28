"""
Phần lõi tích hợp dành cho Role 4.

Cách dùng:
- Copy các helper cần thiết vào src/app.py, hoặc import file này.
- Provider cần có method: generate(prompt: str, system_prompt: str) -> str.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any

from prompts import MAX_ITERATIONS, REACT_SYSTEM_PROMPT, TIMEOUT_SECONDS
from tools import AVAILABLE_TOOLS


_ACTION_PATTERN = re.compile(
    r"Action:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n"
    r"Action Input:\s*(\{.*\})\s*$",
    flags=re.DOTALL,
)

_FINAL_PATTERN = re.compile(
    r"Final Answer:\s*(.+)$",
    flags=re.DOTALL,
)


def parse_action(response: str) -> tuple[str, dict[str, Any]] | None:
    """Parse Action và Action Input JSON từ output của LLM."""
    match = _ACTION_PATTERN.search(response.strip())
    if match is None:
        return None

    tool_name = match.group(1).strip()
    try:
        arguments = json.loads(match.group(2))
    except json.JSONDecodeError:
        return None

    if not isinstance(arguments, dict):
        return None
    return tool_name, arguments


def parse_final_answer(response: str) -> str | None:
    """Lấy Final Answer nếu LLM đã kết thúc."""
    match = _FINAL_PATTERN.search(response.strip())
    if match is None:
        return None
    answer = match.group(1).strip()
    return answer or None


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> str:
    """Dispatch tool qua AVAILABLE_TOOLS với timeout và lỗi an toàn."""
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        return (
            "LỖI: Tool không tồn tại. Tool hợp lệ: "
            + ", ".join(AVAILABLE_TOOLS)
        )

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(tool, **arguments)
            result = future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        return f"LỖI HỆ THỐNG: Tool vượt quá timeout {timeout_seconds} giây."
    except TypeError as exc:
        return f"LỖI THAM SỐ: {exc}"
    except Exception:
        return "LỖI HỆ THỐNG: Không thể thực thi tool."

    if not isinstance(result, str):
        return "LỖI HỆ THỐNG: Tool không trả về chuỗi."
    return result


def build_llm_input(user_query: str, scratchpad: list[str]) -> str:
    """Ghép câu hỏi và trace ReAct thành prompt cho lượt kế tiếp."""
    parts = [f"User Query: {user_query}"]
    if scratchpad:
        parts.append("ReAct Trace hiện tại:")
        parts.extend(scratchpad)
    parts.append(
        "Hãy tạo bước tiếp theo theo đúng định dạng trong system prompt."
    )
    return "\n\n".join(parts)


def run_react_agent(user_query: str, provider) -> str:
    """Chạy vòng lặp ReAct thật: LLM -> Action -> Tool -> Observation -> LLM."""
    scratchpad: list[str] = []
    seen_calls: set[str] = set()

    for step in range(1, MAX_ITERATIONS + 1):
        llm_input = build_llm_input(user_query, scratchpad)
        response = provider.generate(
            llm_input,
            system_prompt=REACT_SYSTEM_PROMPT,
        )

        print(f"\n--- ReAct Step {step}/{MAX_ITERATIONS} ---")
        print(response)

        final_answer = parse_final_answer(response)
        if final_answer is not None:
            print(f"\nFinal Answer: {final_answer}")
            return final_answer

        parsed = parse_action(response)
        if parsed is None:
            observation = (
                "LỖI THAM SỐ: Phản hồi phải chứa Action và Action Input "
                "là JSON object hợp lệ, hoặc Final Answer."
            )
            scratchpad.extend([response, f"Observation: {observation}"])
            continue

        tool_name, arguments = parsed
        call_key = json.dumps(
            {"tool": tool_name, "arguments": arguments},
            ensure_ascii=False,
            sort_keys=True,
        )
        if call_key in seen_calls:
            observation = (
                "LỖI THAM SỐ: Không được lặp lại cùng tool với cùng "
                "Action Input khi Observation không đổi."
            )
        else:
            seen_calls.add(call_key)
            observation = execute_tool(tool_name, arguments)

        print(f"Observation: {observation}")
        scratchpad.extend([response, f"Observation: {observation}"])

    fallback = (
        f"Agent đã dừng an toàn sau {MAX_ITERATIONS} bước mà chưa tạo được "
        "Final Answer. Vui lòng diễn đạt rõ hơn mục tiêu hoặc kỹ năng hiện có."
    )
    print(fallback)
    return fallback
