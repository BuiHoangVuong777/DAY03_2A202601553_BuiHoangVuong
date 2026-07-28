# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)

*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1–5) | Lý do đánh giá |
|---|:---:|---|
| 🧠 **Multi-step Reasoning** | **4/5** | Hệ thống phải phân tích nhiều thông tin đầu vào như trình độ hiện tại, mục tiêu học tập, thời gian có thể học mỗi tuần, ngân sách, kỹ năng đã có và các khóa đã hoàn thành. Sau đó, hệ thống mới có thể tìm và đề xuất khóa học phù hợp. |
| 🛠️ **Tool Interaction** | **4/5** | Agent cần gọi các công cụ như `search_courses` để tìm khóa học và `get_course_details` để lấy thông tin chi tiết. Nếu chỉ dùng kiến thức của LLM, hệ thống có thể đưa ra thông tin không đúng với course catalog. |
| 🔀 **Dynamic Decision** | **4/5** | Kết quả tư vấn thay đổi tùy theo hồ sơ của từng sinh viên. Kết quả tìm kiếm ở bước trước quyết định khóa học cần kiểm tra ở bước sau. |
| ⏳ **Long Horizon** | **3/5** | Quy trình thường gồm khoảng 2–4 bước: phân tích nhu cầu, tìm khóa học, kiểm tra chi tiết và đưa ra tư vấn. |
| **TỔNG ĐIỂM FIT** | **15/20** | **KẾT LUẬN: BÀI TOÁN RẤT PHÙ HỢP ĐỂ SỬ DỤNG REACT AGENT.** |

### Kết luận đánh giá

Bài toán tư vấn khóa học không nên chỉ sử dụng Chatbot Baseline vì câu trả lời cần dựa trên dữ liệu cụ thể trong course catalog. ReAct Agent phù hợp hơn vì có thể suy luận từ hồ sơ sinh viên, gọi công cụ tra cứu và đưa ra đề xuất có căn cứ.

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

### Câu hỏi

“Mình chưa biết gì, muốn học nền tảng, thời gian rảnh ít, ngân sách thấp.”

### 🤖 Chatbot Baseline

**System Prompt:**

> Bạn là Chatbot baseline tư vấn khóa học và lộ trình học Python/AI cho sinh viên.

**Phản hồi:**

> Hướng học đề xuất là Python nền tảng. Bạn đang ở trình độ beginner, muốn học kiến thức nền tảng, có ít thời gian rảnh và ngân sách thấp nên hướng học Python cơ bản sẽ phù hợp.
>
> Bạn nên học cú pháp, biến, kiểu dữ liệu, điều kiện, vòng lặp, hàm cơ bản và thực hiện một project nhỏ.

**Giới hạn:**

> Chưa thể xác nhận khóa học, thời lượng, số giờ học, ngân sách và project cụ thể vì Chatbot Baseline không truy cập course catalog.

**Nhận xét:**

- Chatbot đưa ra định hướng học hợp lý và an toàn.
- Chatbot chỉ tư vấn dựa trên kiến thức chung.
- Chatbot chưa tra cứu được khóa học thực tế.
- Chatbot chưa xác minh chính xác các ràng buộc về thời gian và ngân sách.
- Chatbot không bịa thông tin khóa học cụ thể.

---

### 🧠 ReAct Agent

#### Bước 1: Tìm khóa học phù hợp

**Thought 1:**

Người dùng chưa có kiến thức nền tảng, muốn học kiến thức cơ bản, có ít thời gian rảnh và ngân sách thấp. Tôi cần tìm khóa học phù hợp với các điều kiện:

- Mục tiêu: `foundation`
- Trình độ: `beginner`
- Mức thời gian: `low`
- Mức ngân sách: `low`

**Action 1:**

```text
search_courses[foundation, beginner, low, low, ""]
```

**Observation 1:**

```text
KẾT QUẢ TÌM KIẾM KHÓA HỌC

Tìm thấy khóa học phù hợp:

- Mã khóa học: PY101
- Tên khóa học: Python nhập môn
- Nhóm khóa học: python_foundation
- Trình độ tối thiểu: beginner
- Thời lượng: 6 tuần
- Cường độ học: 4 giờ/tuần
- Mức thời gian: low
- Mức ngân sách: low
- Mức thực hành: high
- Có project: Có
- Project: chương trình quản lý danh sách sinh viên

PY101 đáp ứng các điều kiện về trình độ,
mục tiêu học nền tảng, thời gian ít và ngân sách thấp.
```

#### Bước 2: Kiểm tra chi tiết khóa học

**Thought 2:**

PY101 phù hợp với các ràng buộc chính. Tôi cần xem thông tin chi tiết để xác minh điều kiện tiên quyết, kỹ năng đạt được và nội dung project trước khi đưa ra tư vấn.

**Action 2:**

```text
get_course_details[PY101]
```

**Observation 2:**

```text
CHI TIẾT KHÓA HỌC PY101

Mã khóa học: PY101
Tên khóa học: Python nhập môn
Danh mục: python_foundation
Trình độ tối thiểu: beginner

Mục tiêu phù hợp:
- foundation
- exercises_project
- internship
- advanced

Chuyên ngành:
- Không giới hạn chuyên ngành

Khóa học tiên quyết:
- Không có

Kỹ năng yêu cầu:
- Không yêu cầu

Kỹ năng đạt được:
- Biến và kiểu dữ liệu
- Câu lệnh điều kiện
- Vòng lặp
- List và dictionary
- Hàm cơ bản

Thời lượng:
- 6 tuần

Cường độ:
- 4 giờ/tuần
- Mức thời gian: low

Ngân sách:
- low

Mức thực hành:
- high

Project:
- Chương trình quản lý danh sách sinh viên

Mô tả:
Khóa nhập môn cho người chưa biết Python,
học từ cú pháp cơ bản và thực hành ngay bằng bài tập ngắn.
```

#### Bước 3: Tổng hợp kết quả

**Thought 3:**

Tôi đã có đủ dữ liệu để tư vấn. PY101 phù hợp vì:

- Dành cho người mới bắt đầu.
- Không yêu cầu khóa học tiên quyết.
- Không yêu cầu kỹ năng đầu vào.
- Chỉ cần 4 giờ học mỗi tuần.
- Thuộc mức ngân sách thấp.
- Có nhiều nội dung thực hành và project.

**Final Answer:**

> Khóa học phù hợp nhất với bạn là **PY101 – Python nhập môn**.

> Khóa học này dành cho người chưa có kiến thức Python và không yêu cầu điều kiện tiên quyết. Thời lượng khóa học là **6 tuần**, với khoảng **4 giờ học mỗi tuần**, phù hợp với quỹ thời gian ít và mức ngân sách thấp.

> Bạn sẽ học:

> Biến và kiểu dữ liệu
> Câu lệnh điều kiện
> Vòng lặp
> List và dictionary
> Hàm cơ bản
>
> Cuối khóa, bạn sẽ thực hiện project **chương trình quản lý danh sách sinh viên**.
>
> Sau khi hoàn thành PY101, bạn có thể tiếp tục với PY102 để củng cố kỹ năng thông qua nhiều bài tập và project hơn.

**Nhận xét của Reviewer:**

- Agent xác định đúng hồ sơ người dùng là `beginner`.
- Agent ánh xạ đúng mục tiêu sang `foundation`.
- Agent sử dụng đúng mức thời gian `low`.
- Agent sử dụng đúng mức ngân sách `low`.
- Agent gọi `search_courses` để tra cứu course catalog.
- Agent gọi `get_course_details` để xác minh thông tin trước khi trả lời.
- Các thông tin về thời lượng, kỹ năng và project đều có nguồn từ dữ liệu khóa học.
- Agent không tự bịa học phí, lịch học hoặc cam kết việc làm.
- Kết quả cụ thể và đáng tin cậy hơn Chatbot Baseline.

---

## ✅ 3. BẢNG SO SÁNH KẾT QUẢ

| Nội dung đánh giá | Chatbot Baseline | ReAct Agent |
|---|:---:|:---:|
| Xác định đúng nhu cầu học nền tảng | ✅ | ✅ |
| Tìm được khóa học cụ thể | ❌ | ✅ |
| Kiểm tra trình độ đầu vào | ❌ | ✅ |
| Kiểm tra thời gian học | ❌ | ✅ |
| Kiểm tra ngân sách | ❌ | ✅ |
| Kiểm tra điều kiện tiên quyết | ❌ | ✅ |
| Cung cấp thông tin project | ❌ | ✅ |
| Đưa ra lý do đề xuất | ✅ | ✅ |
| Hạn chế bịa dữ liệu | Trung bình | Tốt |
| Kết quả chung | **PASS mức cơ bản** | **PASS** |


## 📌 4. KẾT LUẬN TEST CASE #3

Chatbot Baseline

PASS ở mức tư vấn tổng quát.

Chatbot đưa ra hướng học hợp lý nhưng không thể kiểm chứng thông tin cụ thể trong course catalog.

ReAct Agent

PASS.

Agent đã thực hiện đúng chuỗi:

Thought
→ Action: search_courses
→ Observation
→ Thought
→ Action: get_course_details
→ Observation
→ Final Answer

ReAct Agent cho kết quả cụ thể và đáng tin cậy hơn vì đề xuất được xây dựng từ dữ liệu khóa học, giới hạn thời gian, ngân sách và trình độ của sinh viên.