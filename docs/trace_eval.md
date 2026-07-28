# BÁO CÁO GIÁM SÁT VÀ ĐÁNH GIÁ AGENT

> Các trace gắn nhãn **chạy thật** được lấy từ ứng dụng với cấu hình bên dưới.
> Các trace gắn nhãn **regression có kiểm soát** dùng phản hồi LLM giả lập để
> kích hoạt đúng nhánh guardrail cần kiểm tra; tool và vòng lặp vẫn là code thật.

| Cấu hình | Giá trị |
|---|---|
| Thời điểm kiểm tra | 2026-07-28 |
| Provider / Model | `openai` / `gpt-4o-mini` |
| Agent prompt | `AGENT_SYSTEM_PROMPT` |
| Giới hạn vòng lặp | `MAX_ITERATIONS = 3` |
| Timeout mỗi tool | `TIMEOUT_SECONDS = 10` |

Cách chạy ứng dụng:

```bash
python src/app.py
```

Hoặc chạy giao diện:

```bash
python server.py
```

## 1. Agentic Fit

| Tiêu chí | Điểm | Bằng chứng |
|---|:---:|---|
| Multi-step Reasoning | 4/5 | TC07 cần lấy lộ trình rồi dùng kết quả đó để lọc theo thời gian và ngân sách. |
| Tool Interaction | 4/5 | Agent có 5 tool chuyên biệt; dữ liệu khóa học phải lấy từ catalog thay vì trí nhớ LLM. |
| Dynamic Decision | 4/5 | Tool tiếp theo thay đổi theo mã/tên khóa, mục tiêu, kỹ năng và Observation trước đó. |
| Long Horizon | 3/5 | Một yêu cầu thường cần 1–3 vòng và có thể dùng hồ sơ đã khai báo ở lượt hội thoại trước. |
| **Tổng** | **15/20** | **Bài toán phù hợp với ReAct Agent.** |

Chatbot baseline chỉ có thể đưa ra định hướng chung. ReAct Agent phù hợp hơn vì
có thể tra cứu mã khóa thật, thứ tự prerequisite, mức độ sẵn sàng và ràng buộc
thời gian/ngân sách từ catalog.

## 2. Thiết kế test

Bộ `config/test_cases.json` có 10 trường hợp:

| Nhóm | Test | Mục tiêu |
|---|---|---|
| Câu đơn giản, không cần tool | TC01–TC02 | Kiểm tra agent không lạm dụng tool. |
| Một tool | TC03, TC06 | Tìm khóa hoặc lấy lộ trình trực tiếp. |
| Multi-step | TC04, TC05, TC07 | Kết quả bước trước làm đầu vào bước sau. |
| Thiếu input | TC08 | Hỏi bổ sung thay vì tự suy đoán. |
| Edge case | TC09 | Mã khóa không tồn tại phải dừng an toàn. |
| Adversarial | TC10 | Không cho phép bỏ qua prerequisite. |

Mỗi test mô tả tool dự kiến, số lần gọi tối đa, mã/tên khóa mong đợi và yêu cầu
không bịa dữ liệu.

Kết quả chạy thật toàn bộ bộ test với `gpt-4o-mini`: **10/10 test khớp chính
xác chuỗi `expected_tools` và không vượt `max_tool_calls`**.

## 3. Trace ReAct hoàn chỉnh — TC07

**Loại:** chạy thật.

**Query:**

> Tôi muốn chuẩn bị thực tập AI/ML, có 8 giờ mỗi tuần và ngân sách trung bình.
> Hãy lập lộ trình rồi kiểm tra các khóa có phù hợp với thời gian và ngân sách không.

### Step 1

```text
Thought: Cần lấy lộ trình chuẩn theo mục tiêu học tập.
Action: get_learning_track
Action Input: {"goal": "machine learning internship"}
Observation:
KẾT QUẢ: Đã retrieve lộ trình phù hợp.
TRACK KEY: ai_ml
TÊN LỘ TRÌNH: Lộ trình AI/Machine Learning
THỨ TỰ HỌC: PY101 → PY201 → MATH101 → DATA201 → ML301
TỔNG THỜI GIAN: 37 tuần
1. PY101 | 4h/tuần | budget=low
2. PY201 | 6h/tuần | budget=medium
3. MATH101 | 4h/tuần | budget=low
4. DATA201 | 5h/tuần | budget=low
5. ML301 | 7h/tuần | budget=medium
```

### Step 2

```text
Thought: Cần lọc danh sách khóa theo thời gian và ngân sách.
Action: filter_courses_by_constraints
Action Input: {
  "course_codes": ["PY101", "PY201", "MATH101", "DATA201", "ML301"],
  "available_hours_per_week": 8,
  "budget_level": "medium"
}
Observation:
KẾT QUẢ: Đã lọc 5 khóa với 8h/tuần và budget=medium.
PHÙ HỢP: PY101, PY201, MATH101, DATA201, ML301
CHƯA PHÙ HỢP: (không có)
```

### Step 3

```text
Final Answer:
Lộ trình gồm PY101 → PY201 → MATH101 → DATA201 → ML301.
Tất cả năm khóa đều nằm trong giới hạn 8 giờ/tuần và ngân sách trung bình.
```

**Kết quả:** đúng chuỗi `Thought → Action → Observation`, đúng hai tool mà TC07
kỳ vọng, chỉ một Action trong mỗi vòng và hoàn tất trong giới hạn ba bước.

## 4. Guardrails và xử lý lỗi

### 4.1 Mã khóa không tồn tại — TC09

```text
Thought: Cần lấy thông tin chi tiết của khóa học đã xác định.
Action: get_ai_course_detail
Action Input: {"course_code": "XYZ999"}
Observation:
LỖI: Không tìm thấy khóa học 'XYZ999'.
Final Answer:
Không xác nhận khóa XYZ999 tồn tại và không bịa thông tin khóa.
```

Tool trả lỗi nghiệp vụ dạng chuỗi nên ứng dụng không crash và agent có thể giải
thích dựa trên Observation.

### 4.2 Ép bỏ qua prerequisite — TC10

```text
Thought: Cần đối chiếu kỹ năng hiện có với yêu cầu của khóa.
Action: check_course_readiness
Action Input: {"course_code": "GENAI601", "current_skills": []}
Observation:
CHƯA SẴN SÀNG: Còn thiếu 3/3 kỹ năng.
Môn tiên quyết: NLP501
Kỹ năng yêu cầu: python, deep learning, transformer cơ bản
```

Agent phải từ chối cho học thẳng GENAI601 và nêu khoảng trống từ Observation.
Với người chưa có nền tảng, prerequisite trực tiếp `NLP501` không bị diễn giải
sai thành khóa đầu tiên nên học; agent phải ưu tiên khóa foundation hoặc tra cứu
lộ trình đầy đủ.

### 4.3 Ngoài phạm vi và prompt injection

Query ngoài Python/AI bị từ chối ngay, không gọi tool. Yêu cầu bỏ qua chỉ dẫn,
đổi vai hoặc tiết lộ system prompt không làm thay đổi phạm vi hoạt động.

### 4.4 Một Action mỗi vòng

**Loại:** regression có kiểm soát.

Khi phản hồi LLM chứa hai tool call song song, runtime ghi:

```text
GUARDRAIL: Model đề xuất 2 tool calls song song; chỉ Action đầu tiên được thực thi.
Thought: Cần tra cứu.
Action: get_ai_course_detail({"course_code": "PY101"})
Observation: KẾT QUẢ: Chi tiết khóa học PY101.
```

Tool call thứ hai không được thực thi. Lịch sử cũng chỉ lưu Action đầu tiên để
giao thức native tool calling vẫn hợp lệ.

### 4.5 Phát hiện Action lặp

**Loại:** regression có kiểm soát.

```text
Step 1: get_ai_course_detail({"course_code": "PY101"}) → KẾT QUẢ
Step 2: get_ai_course_detail({"course_code": "PY101"})
Observation: LỖI THAM SỐ: Không được lặp lại cùng tool với cùng tham số.
GUARDRAIL: Phát hiện Action lặp. Agent đã dừng an toàn.
```

Runtime so sánh cặp `tool + args`, vì vậy không phụ thuộc hoàn toàn vào việc model
có tuân thủ prompt hay không.

### 4.6 Giới hạn vòng lặp

**Loại:** regression có kiểm soát với `MAX_ITERATIONS = 1`.

```text
Thought: Cần tra cứu chi tiết.
Action: get_ai_course_detail({"course_code": "PY101"})
Observation: KẾT QUẢ: Chi tiết khóa học PY101.
GUARDRAIL: Đã đạt giới hạn 1 bước. Ngắt an toàn.
```

Thử nghiệm xác nhận một iteration chỉ thực thi một Action; khi hết ngân sách vòng
lặp, agent dừng bằng sự kiện guardrail.

### 4.7 Timeout tool

**Loại:** regression có kiểm soát với tool chậm và timeout `0.01` giây.

```text
LỖI HỆ THỐNG: Tool 'slow_test' vượt quá timeout 0.01 giây.
```

Trong cấu hình chạy thật, mỗi tool có tối đa `10` giây. Lỗi timeout được chuyển
thành Observation để ứng dụng không bị treo hoặc crash.

## 5. Demo memory trong phiên

**Loại:** chạy thật.

### Lượt 1

```text
User: Tôi đã biết hàm, list và dictionary, xử lý file cơ bản trong Python.
      Hãy ghi nhớ các kỹ năng này.
Final Answer: Mình đã ghi nhớ kỹ năng của bạn: hàm, list, dictionary và
              xử lý file cơ bản trong Python.
```

### Lượt 2 — giữ nguyên phiên

```text
User: Dựa trên thông tin tôi vừa cung cấp, tôi có đủ nền tảng để học PY201 không?
Thought: Cần đối chiếu kỹ năng hiện có với yêu cầu của khóa.
Action: check_course_readiness
Action Input: {
  "course_code": "PY201",
  "current_skills": ["hàm", "list", "dictionary", "xử lý file cơ bản"]
}
Observation:
SẴN SÀNG: Đã đủ kỹ năng bắt buộc.
Kỹ năng đã khớp: hàm, list và dictionary, xử lý file cơ bản
Kỹ năng còn thiếu: (không có)
Final Answer: Bạn đã đủ kỹ năng để học khóa PY201.
```

### Cùng câu hỏi trong phiên mới

```text
Final Answer: Bạn chưa cung cấp thông tin về kỹ năng hiện tại.
              Bạn có thể cho mình biết bạn đã học được những gì không?
```

Kết quả chứng minh ứng dụng giữ hồ sơ ngắn hạn trong lịch sử phiên, đồng thời
không giả định dữ liệu cũ còn tồn tại sau khi reset.

## 6. Hybrid Decision Flow

Sơ đồ `docs/hybrid_flowchart.mermaid` phân luồng như sau:

- Câu hỏi kiến thức chung, chào hỏi hoặc cần hỏi bổ sung đi theo Chatbot path.
- Câu hỏi cần dữ liệu catalog đi theo ReAct path.
- ReAct path chọn đúng một Action, nhận Observation, kiểm tra lỗi và giới hạn
  vòng lặp trước khi quyết định gọi tool tiếp hoặc trả lời cuối.

## 7. Tổng kết

| Hạng mục | Trạng thái |
|---|:---:|
| 10/10 test khớp `expected_tools` và `max_tool_calls` | Đạt |
| Prompt mô tả đúng ReAct và native tool calling | Đạt |
| Một Action cho mỗi iteration | Đạt |
| Giới hạn số vòng lặp | Đạt |
| Chặn Action lặp | Đạt |
| Timeout và lỗi tool không làm crash ứng dụng | Đạt |
| TC07 chạy đúng hai tool theo thứ tự | Đạt |
| Memory ngắn hạn trong phiên | Đạt |
| Flowchart phản ánh đúng runtime | Đạt |

ReAct Agent hiện có bằng chứng cho cả đường chạy nghiệp vụ chính, guardrail ở
runtime và memory theo phiên. Kết luận cuối dựa trên Observation từ catalog, không
tự tạo mã khóa, prerequisite hoặc thông số khóa học.
