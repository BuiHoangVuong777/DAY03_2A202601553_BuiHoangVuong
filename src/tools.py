"""
🛠️ TOOL REGISTRY — AI LEARNING PATH ADVISOR
Role 2: Tool & Spec Engineer | Mốc 2: Implement Tools

Đề tài: Trợ lý tư vấn lộ trình học Python & AI cho người mới.

⚖️ NGUYÊN TẮC THIẾT KẾ XUYÊN SUỐT:
   Tool trả về FACTS — LLM đưa ra JUDGMENT.
   Tool được phép: tìm kiếm, lấy chi tiết, đối chiếu kỹ năng còn thiếu,
   trả lộ trình chuẩn suy ra từ đồ thị tiên quyết, lọc theo thời gian/ngân sách.
   Tool KHÔNG được: tự viết lời khuyên dài, tự quyết định thay LLM,
   tự cắt bớt lộ trình theo cảm tính.

🛡️ ERROR CONTRACT — mọi Observation mở đầu bằng đúng 1 tiền tố:
   KẾT QUẢ:           Tra cứu thành công, có dữ liệu.
   SẴN SÀNG:          Người học đủ kỹ năng cho khóa đang xét.
   CHƯA SẴN SÀNG:     Kết quả nghiệp vụ hợp lệ, còn thiếu kỹ năng (KHÔNG phải lỗi).
   KHÔNG CÓ KẾT QUẢ:  Truy vấn hợp lệ nhưng không khớp dữ liệu -> ĐƯỢC thử lại 1 lần.
   KHÔNG CÓ LỘ TRÌNH: Mục tiêu không khớp track nào -> ĐƯỢC thử lại 1 lần.
   LỖI THAM SỐ:       Sai kiểu / sai giá trị -> ĐƯỢC thử lại 1 lần theo cú pháp gợi ý.
   LỖI:               Dữ liệu không tồn tại -> DỪNG, thử lại vô nghĩa.
   LỖI HỆ THỐNG:      Sự cố ngoài dự kiến -> DỪNG.

📐 SCHEMA DỮ LIỆU (theo course_catalog.json của nhóm):
   minimum_profile_level : beginner | basic | intermediate
   goals                 : foundation | exercises_project | internship | advanced
   specializations       : ai_ml | deep_learning | data | nlp | generative_ai | ai_agent
   time_level            : low (<=4h/tuần) | medium (<=8h) | high (<=12h)
   budget_level          : low < medium < high (theo khả năng chi trả)

Ràng buộc kỹ thuật: Python 3.10+, không thư viện ngoài, không gọi API,
không đọc file ngoài, không eval/exec. Mọi tool luôn return str.
"""

import os
import sys
from typing import Any

# =====================================================================
# ⏱️ QUY TẮC THỜI GIAN & NGÂN SÁCH
# =====================================================================

# Người học tự nhận mức thời gian rảnh -> số giờ tối đa mỗi tuần.
TIME_RULES: dict[str, dict[str, int]] = {
    "low": {"max_hours_per_week": 4},
    "medium": {"max_hours_per_week": 8},
    "high": {"max_hours_per_week": 12},
}

# Quy ước thứ tự ngân sách: low < medium < high.
# Người có ngân sách cao hơn học được các khóa ở mức thấp hơn.
BUDGET_RANK: dict[str, int] = {"low": 1, "medium": 2, "high": 3}

VALID_PROFILE_LEVELS: tuple[str, ...] = ("beginner", "basic", "intermediate")

VALID_GOALS: tuple[str, ...] = ("foundation", "exercises_project", "internship", "advanced")

# Cách người dùng diễn đạt mức thời gian rảnh bằng tiếng Việt.
TIME_LEVEL_ALIASES: dict[str, str] = {
    "low": "low",
    "ít": "low",
    "it": "low",
    "thấp": "low",
    "thap": "low",
    "rất ít": "low",
    "medium": "medium",
    "vừa": "medium",
    "vua": "medium",
    "vừa phải": "medium",
    "trung bình": "medium",
    "trung binh": "medium",
    "high": "high",
    "nhiều": "high",
    "nhieu": "high",
    "cao": "high",
    "rất nhiều": "high",
}


# =====================================================================
# 📚 CATALOG KHÓA HỌC (dữ liệu giả lập, khai báo trực tiếp trong Python)
# =====================================================================

AI_COURSES: dict[str, dict[str, Any]] = {
    "PY101": {
        "title": "Python nhập môn",
        "category": "python_foundation",
        "minimum_profile_level": "beginner",
        "goals": ["foundation", "exercises_project", "internship", "advanced"],
        "specializations": [],
        "prerequisites": [],
        "required_skills": [],
        "skills_gained": [
            "biến và kiểu dữ liệu",
            "câu lệnh điều kiện",
            "vòng lặp",
            "list và dictionary",
            "hàm cơ bản",
        ],
        "duration_weeks": 6,
        "hours_per_week": 4,
        "time_level": "low",
        "budget_level": "low",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "chương trình quản lý danh sách sinh viên",
        "description": (
            "Khóa nhập môn cho người chưa biết Python, học từ cú pháp cơ bản và "
            "thực hành ngay bằng bài tập ngắn."
        ),
    },
    "PY102": {
        "title": "Python nền tảng qua bài tập và project",
        "category": "python_foundation",
        "minimum_profile_level": "basic",
        "goals": ["foundation", "exercises_project", "internship"],
        "specializations": [],
        "prerequisites": ["PY101"],
        "required_skills": [
            "biến và kiểu dữ liệu",
            "điều kiện",
            "vòng lặp",
            "hàm cơ bản",
        ],
        "skills_gained": [
            "tách hàm",
            "xử lý file",
            "exception cơ bản",
            "debugging",
            "làm project nhỏ",
        ],
        "duration_weeks": 6,
        "hours_per_week": 6,
        "time_level": "medium",
        "budget_level": "low",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "ứng dụng quản lý chi tiêu cá nhân",
        "description": (
            "Khóa củng cố nền tảng bằng nhiều bài tập, lab và một project nhỏ; "
            "phù hợp với sinh viên biết cú pháp nhưng chưa vững."
        ),
    },
    "PY201": {
        "title": "Lập trình hướng đối tượng và cấu trúc dữ liệu với Python",
        "category": "python_advanced",
        "minimum_profile_level": "basic",
        "goals": ["exercises_project", "internship", "advanced"],
        "specializations": [],
        "prerequisites": ["PY101"],
        "required_skills": ["hàm", "list và dictionary", "xử lý file cơ bản"],
        "skills_gained": [
            "oop",
            "class và object",
            "kế thừa",
            "stack và queue",
            "tổ chức mã nguồn",
        ],
        "duration_weeks": 8,
        "hours_per_week": 6,
        "time_level": "medium",
        "budget_level": "medium",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "ứng dụng quản lý khóa học theo mô hình OOP",
        "description": (
            "Cầu nối từ Python cơ bản lên nâng cao, tập trung vào OOP, cấu trúc "
            "dữ liệu và cách tổ chức chương trình."
        ),
    },
    "PY202": {
        "title": "Advanced Python và phát triển project",
        "category": "python_advanced",
        "minimum_profile_level": "intermediate",
        "goals": ["exercises_project", "internship", "advanced"],
        "specializations": [],
        "prerequisites": ["PY201"],
        "required_skills": [
            "python cơ bản",
            "oop",
            "cấu trúc dữ liệu",
            "đã làm ít nhất một project nhỏ",
        ],
        "skills_gained": [
            "decorator",
            "generator",
            "context manager",
            "type hints",
            "unit testing",
            "clean code",
        ],
        "duration_weeks": 8,
        "hours_per_week": 8,
        "time_level": "medium",
        "budget_level": "medium",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "ứng dụng Python hoàn chỉnh có test",
        "description": (
            "Khóa nâng cao dành cho sinh viên đã vững nền tảng và OOP, hướng tới "
            "project thực tế và chuẩn bị thực tập."
        ),
    },
    "MATH101": {
        "title": "Toán nền tảng cho AI",
        "category": "ai_foundation",
        "minimum_profile_level": "basic",
        "goals": ["internship", "advanced"],
        "specializations": ["ai_ml", "deep_learning"],
        "prerequisites": [],
        "required_skills": [],
        "skills_gained": [
            "đại số tuyến tính cơ bản",
            "xác suất",
            "thống kê",
            "đạo hàm cơ bản",
        ],
        "duration_weeks": 8,
        "hours_per_week": 4,
        "time_level": "low",
        "budget_level": "low",
        "practice_level": "medium",
        "has_projects": False,
        "project_type": None,
        "description": "Kiến thức toán cần thiết trước khi học Machine Learning.",
    },
    "DATA201": {
        "title": "Xử lý dữ liệu với NumPy và Pandas",
        "category": "data",
        "minimum_profile_level": "basic",
        "goals": ["exercises_project", "internship", "advanced"],
        "specializations": ["data", "ai_ml"],
        "prerequisites": ["PY101"],
        "required_skills": ["python cơ bản"],
        "skills_gained": ["numpy", "pandas", "làm sạch dữ liệu", "phân tích dữ liệu"],
        "duration_weeks": 5,
        "hours_per_week": 5,
        "time_level": "medium",
        "budget_level": "low",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "phân tích một bộ dữ liệu nhỏ",
        "description": "Bước chuyển từ Python sang xử lý dữ liệu cho AI.",
    },
    "ML301": {
        "title": "Machine Learning căn bản",
        "category": "machine_learning",
        "minimum_profile_level": "intermediate",
        "goals": ["internship", "advanced"],
        "specializations": ["ai_ml"],
        "prerequisites": ["PY201", "MATH101", "DATA201"],
        "required_skills": [
            "python và oop",
            "xác suất thống kê cơ bản",
            "xử lý dữ liệu",
        ],
        "skills_gained": [
            "regression",
            "classification",
            "clustering",
            "model evaluation",
            "scikit-learn",
        ],
        "duration_weeks": 10,
        "hours_per_week": 7,
        "time_level": "medium",
        "budget_level": "medium",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "project dự đoán với scikit-learn",
        "description": "Khóa nhập môn Machine Learning sau Python và dữ liệu.",
    },
    "DL401": {
        "title": "Deep Learning căn bản",
        "category": "deep_learning",
        "minimum_profile_level": "intermediate",
        "goals": ["internship", "advanced"],
        "specializations": ["deep_learning"],
        "prerequisites": ["ML301"],
        "required_skills": [
            "machine learning căn bản",
            "python",
            "đại số tuyến tính",
        ],
        "skills_gained": ["neural network", "backpropagation", "pytorch", "cnn cơ bản"],
        "duration_weeks": 10,
        "hours_per_week": 8,
        "time_level": "medium",
        "budget_level": "medium",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "mô hình phân loại ảnh bằng PyTorch",
        "description": "Bước tiếp theo sau Machine Learning cho người học AI.",
    },
    "NLP501": {
        "title": "Xử lý ngôn ngữ tự nhiên",
        "category": "nlp",
        "minimum_profile_level": "intermediate",
        "goals": ["exercises_project", "internship", "advanced"],
        "specializations": ["nlp", "generative_ai"],
        "prerequisites": ["DL401"],
        "required_skills": ["deep learning căn bản", "python", "pytorch"],
        "skills_gained": [
            "text preprocessing",
            "word embeddings",
            "transformer cơ bản",
            "text classification",
        ],
        "duration_weeks": 9,
        "hours_per_week": 8,
        "time_level": "medium",
        "budget_level": "high",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "ứng dụng phân loại văn bản",
        "description": "Khóa NLP thực hành trước khi học Generative AI.",
    },
    "GENAI601": {
        "title": "Generative AI và ứng dụng LLM",
        "category": "generative_ai",
        "minimum_profile_level": "intermediate",
        "goals": ["exercises_project", "internship", "advanced"],
        "specializations": ["generative_ai", "ai_agent"],
        "prerequisites": ["NLP501"],
        "required_skills": ["python", "deep learning", "transformer cơ bản"],
        "skills_gained": ["prompt engineering", "rag", "tool calling", "ai agent"],
        "duration_weeks": 8,
        "hours_per_week": 7,
        "time_level": "medium",
        "budget_level": "medium",
        "practice_level": "high",
        "has_projects": True,
        "project_type": "ứng dụng LLM có RAG hoặc tool calling",
        "description": "Khóa chuyên sâu về LLM, RAG và AI Agent.",
    },
}


# =====================================================================
# 🗺️ ĐỊNH NGHĨA LỘ TRÌNH
# ---------------------------------------------------------------------
# Chỉ khai báo KHÓA ĐÍCH (targets) — thứ tự học được SUY RA từ đồ thị
# prerequisites trong AI_COURSES, nên không bao giờ lệch với catalog.
# =====================================================================

LEARNING_TRACKS: dict[str, dict[str, Any]] = {
    "python_foundation": {
        "title": "Lộ trình Python nền tảng",
        "description": (
            "Dành cho người chưa biết hoặc chưa vững Python: học cú pháp rồi củng cố "
            "ngay bằng bài tập và project nhỏ."
        ),
        "aliases": [
            "python",
            "học python",
            "hoc python",
            "python nền tảng",
            "python cơ bản",
            "python nhập môn",
            "nền tảng lập trình",
            "foundation",
            "học lại nền tảng",
            "người mới học python",
        ],
        "targets": ["PY102"],
    },
    "python_advanced": {
        "title": "Lộ trình Python nâng cao",
        "description": (
            "Dành cho người đã biết cơ bản, muốn đi sâu: OOP, cấu trúc dữ liệu, "
            "clean code và project hoàn chỉnh có test."
        ),
        "aliases": [
            "python nâng cao",
            "python nang cao",
            "advanced python",
            "python advanced",
            "nâng cao",
            "oop",
            "hướng đối tượng",
            "cấu trúc dữ liệu",
            "clean code",
        ],
        "targets": ["PY202"],
    },
    "data": {
        "title": "Lộ trình Xử lý & Phân tích Dữ liệu",
        "description": (
            "Lộ trình ngắn để làm việc với dữ liệu: Python cơ bản rồi NumPy/Pandas."
        ),
        "aliases": [
            "data",
            "data science",
            "khoa học dữ liệu",
            "khoa hoc du lieu",
            "phân tích dữ liệu",
            "xử lý dữ liệu",
            "data analyst",
            "numpy",
            "pandas",
        ],
        "targets": ["DATA201"],
    },
    "internship": {
        "title": "Lộ trình Chuẩn bị Thực tập AI/ML",
        "description": (
            "Lộ trình đủ rộng để ứng tuyển thực tập: Python vững + project có test, "
            "cộng toán nền tảng, xử lý dữ liệu và Machine Learning."
        ),
        "aliases": [
            "thực tập",
            "thuc tap",
            "internship",
            "thực tập ai/ml",
            "thuc tap ai",
            "chuẩn bị thực tập",
            "đi thực tập",
            "xin thực tập",
        ],
        "targets": ["PY202", "ML301"],
    },
    "ai_ml": {
        "title": "Lộ trình Machine Learning",
        "description": (
            "Lộ trình vào Machine Learning: Python + OOP, toán nền tảng, xử lý dữ liệu, "
            "rồi mới tới các thuật toán ML."
        ),
        "aliases": [
            "ai",
            "ml",
            "ai/ml",
            "machine learning",
            "học machine learning",
            "trí tuệ nhân tạo",
            "tri tue nhan tao",
            "artificial intelligence",
            "học ai từ đầu",
            "nhập môn ai",
        ],
        "targets": ["ML301"],
    },
    "deep_learning": {
        "title": "Lộ trình Deep Learning",
        "description": (
            "Đi từ nền tảng lên mạng nơ-ron sâu: phải vững Machine Learning cổ điển "
            "trước khi học kiến trúc deep learning và PyTorch."
        ),
        "aliases": [
            "deep learning",
            "dl",
            "học sâu",
            "mạng nơ-ron",
            "mang no-ron",
            "neural network",
            "pytorch",
        ],
        "targets": ["DL401"],
    },
    "nlp": {
        "title": "Lộ trình Xử lý Ngôn ngữ Tự nhiên (NLP)",
        "description": (
            "Dành cho người muốn làm việc với văn bản và ngôn ngữ. Phải vững Deep "
            "Learning trước khi học embedding, attention và Transformer."
        ),
        "aliases": [
            "nlp",
            "xử lý ngôn ngữ tự nhiên",
            "xu ly ngon ngu tu nhien",
            "ngôn ngữ tự nhiên",
            "natural language processing",
            "transformer",
            "phân tích văn bản",
            "text mining",
        ],
        "targets": ["NLP501"],
    },
    "generative_ai": {
        "title": "Lộ trình Generative AI & AI Agent",
        "description": (
            "Lộ trình dài nhất, đích đến là xây dựng AI Agent và ứng dụng LLM. "
            "Bắt buộc đi qua NLP và Transformer trước khi tới Generative AI."
        ),
        "aliases": [
            "generative ai",
            "genai",
            "gen ai",
            "ai agent",
            "xây ai agent",
            "xay ai agent",
            "llm",
            "rag",
            "chatbot",
            "prompt engineering",
        ],
        "targets": ["GENAI601"],
    },
}


# Ngưỡng ký tự tối thiểu để cho phép so khớp theo substring.
_MIN_FUZZY_LEN = 3

# Đặt biến môi trường TOOLS_DEBUG=1 khi phát triển để in chi tiết lỗi hệ thống
# ra stderr. Observation trả về cho Agent không đổi, và stdout (nơi chứa trace
# log của Role 5) không bị nhiễu.
_TOOL_DEBUG = os.getenv("TOOLS_DEBUG", "").strip() == "1"


# =====================================================================
# 🔧 HELPER FUNCTIONS (private — KHÔNG đăng ký vào AVAILABLE_TOOLS)
# =====================================================================

def _system_error(tool_name: str, exc: Exception) -> str:
    """
    Tạo Observation chuẩn cho lỗi hệ thống ngoài dự kiến.

    Không bao giờ để lộ stack trace ra Observation. Khi bật TOOLS_DEBUG=1,
    chi tiết lỗi được in ra stderr để lập trình viên còn debug được.

    Args:
        tool_name (str): Tên tool đã ném lỗi, dùng cho log.
        exc (Exception): Exception bắt được ở lớp ngoài cùng.

    Returns:
        str: Chuỗi "LỖI HỆ THỐNG: Không thể xử lý yêu cầu."

    Example:
        >>> _system_error("search_ai_courses", ValueError("x"))
        'LỖI HỆ THỐNG: Không thể xử lý yêu cầu.'
    """
    if _TOOL_DEBUG:
        print(f"[Tool Error] {tool_name}: {type(exc).__name__}: {exc}", file=sys.stderr)
    return "LỖI HỆ THỐNG: Không thể xử lý yêu cầu."


def _normalize_text(value: Any) -> str:
    """
    Chuẩn hóa một giá trị bất kỳ về chuỗi thường, gọn khoảng trắng.

    Bóc luôn dấu nháy thừa mà LLM hay sinh ra khi viết Action,
    ví dụ "'ML301'" hoặc '"machine learning"'.

    Args:
        value (Any): Giá trị cần chuẩn hóa. None được coi là chuỗi rỗng.

    Returns:
        str: Chuỗi đã chuẩn hóa, hoặc "" nếu không có nội dung.

    Example:
        >>> _normalize_text("  'ML301' ")
        'ml301'
    """
    if value is None:
        return ""
    text = str(value).strip().strip("'\"`").strip()
    return " ".join(text.lower().split())


def _tokenize(text: str) -> list[str]:
    """
    Tách một chuỗi đã chuẩn hóa thành danh sách từ rời.

    Dùng cho việc so khớp các alias siêu ngắn (ml, dl, ai): chúng chỉ được coi
    là khớp khi đứng thành một từ độc lập, tránh khớp bừa vào giữa từ khác
    (ví dụ "ml" không được khớp vào "html").

    Args:
        text (str): Chuỗi đã chuẩn hóa qua _normalize_text.

    Returns:
        list[str]: Danh sách từ, đã bỏ dấu câu và dấu gạch chéo.

    Example:
        >>> _tokenize("thực tập ai/ml")
        ['thực', 'tập', 'ai', 'ml']
    """
    cleaned = text
    for char in "/,.;:!?()[]{}\"'-_":
        cleaned = cleaned.replace(char, " ")
    return cleaned.split()


def _normalize_code(value: Any) -> str:
    """
    Chuẩn hóa mã khóa học về dạng CHỮ HOA không khoảng trắng thừa.

    Args:
        value (Any): Mã khóa học thô, ví dụ " ml301 ".

    Returns:
        str: Mã đã chuẩn hóa, ví dụ "ML301". Trả "" nếu rỗng.

    Example:
        >>> _normalize_code(" ml301 ")
        'ML301'
    """
    return _normalize_text(value).upper()


def _normalize_skill_list(skills: list[Any]) -> list[str]:
    """
    Chuẩn hóa danh sách kỹ năng: bỏ hoa/thường, bỏ khoảng trắng thừa, bỏ trùng.

    Args:
        skills (list[Any]): Danh sách kỹ năng thô do người dùng cung cấp.

    Returns:
        list[str]: Danh sách kỹ năng đã chuẩn hóa, giữ nguyên thứ tự xuất hiện.

    Example:
        >>> _normalize_skill_list(["Python Cơ Bản", " numpy ", "python cơ bản"])
        ['python cơ bản', 'numpy']
    """
    normalized: list[str] = []
    for skill in skills:
        clean = _normalize_text(skill)
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized


def _has_skill(required: str, owned_skills: list[str]) -> bool:
    """
    Kiểm tra người học đã có một kỹ năng yêu cầu hay chưa.

    So khớp chính xác trước; nếu không khớp thì cho phép so khớp substring hai
    chiều để chấp nhận cách diễn đạt khác nhau ("python" ~ "python cơ bản",
    "thống kê" ~ "xác suất thống kê cơ bản").

    Args:
        required (str): Kỹ năng yêu cầu, đã chuẩn hóa.
        owned_skills (list[str]): Kỹ năng người học đang có, đã chuẩn hóa.

    Returns:
        bool: True nếu coi như đã có kỹ năng đó.

    Example:
        >>> _has_skill("python cơ bản", ["python"])
        True
    """
    if required in owned_skills:
        return True
    for owned in owned_skills:
        shorter = required if len(required) <= len(owned) else owned
        if len(shorter) < _MIN_FUZZY_LEN:
            continue
        if required in owned or owned in required:
            return True
    return False


def _validate_choice(value: Any, allowed: tuple[str, ...]) -> str | None:
    """
    Kiểm tra một tham số dạng lựa chọn có nằm trong tập hợp lệ hay không.

    Args:
        value (Any): Giá trị cần kiểm tra. None hoặc rỗng nghĩa là "không lọc".
        allowed (tuple[str, ...]): Tập giá trị hợp lệ.

    Returns:
        str | None: "" nếu người dùng không truyền; giá trị đã chuẩn hóa nếu hợp lệ;
            None nếu truyền một giá trị không hợp lệ.

    Example:
        >>> _validate_choice("BEGINNER", VALID_PROFILE_LEVELS)
        'beginner'
    """
    text = _normalize_text(value)
    if not text:
        return ""
    return text if text in allowed else None


def _validate_level(level: Any) -> str | None:
    """
    Xác thực tham số trình độ tối thiểu của khóa học.

    Args:
        level (Any): Giá trị level thô (beginner / basic / intermediate).

    Returns:
        str | None: "" nếu bỏ trống, level chuẩn hóa nếu hợp lệ, None nếu sai.

    Example:
        >>> _validate_level("Basic")
        'basic'
    """
    return _validate_choice(level, VALID_PROFILE_LEVELS)


def _validate_budget(budget: Any) -> str | None:
    """
    Xác thực tham số ngân sách.

    Args:
        budget (Any): Giá trị ngân sách thô.

    Returns:
        str | None: "" nếu bỏ trống, budget chuẩn hóa nếu hợp lệ, None nếu sai.

    Example:
        >>> _validate_budget(" HIGH ")
        'high'
    """
    return _validate_choice(budget, tuple(BUDGET_RANK))


def _resolve_hours(available_hours_per_week: Any) -> int | None:
    """
    Quy đổi tham số thời gian rảnh về số giờ tối đa mỗi tuần.

    Nhận cả số nguyên (số giờ cụ thể) và mức thời gian dạng chữ theo TIME_RULES
    ("ít" / "vừa" / "nhiều" hoặc "low" / "medium" / "high"), vì người dùng
    thường nói mức chứ không nói con số.

    Args:
        available_hours_per_week (Any): Số giờ hoặc mức thời gian.

    Returns:
        int | None: Số giờ tối đa mỗi tuần, hoặc None nếu không hợp lệ.

    Example:
        >>> _resolve_hours(6)
        6
        >>> _resolve_hours("ít")
        4
    """
    if isinstance(available_hours_per_week, bool):
        return None
    if isinstance(available_hours_per_week, int):
        return available_hours_per_week if available_hours_per_week > 0 else None

    text = _normalize_text(available_hours_per_week)
    if not text:
        return None
    if text.isdigit():
        hours = int(text)
        return hours if hours > 0 else None

    level = TIME_LEVEL_ALIASES.get(text)
    if level is None:
        return None
    return TIME_RULES[level]["max_hours_per_week"]


def _resolve_prerequisite_chain(targets: list[str]) -> list[str]:
    """
    Suy ra thứ tự học từ đồ thị prerequisites (topological sort).

    Đi sâu vào các môn tiên quyết trước, rồi mới thêm chính môn đó, nên kết quả
    luôn đúng thứ tự học được. Nhờ vậy lộ trình không bao giờ lệch với catalog.

    Args:
        targets (list[str]): Danh sách mã khóa đích của lộ trình.

    Returns:
        list[str]: Danh sách mã khóa theo đúng thứ tự học, đã bỏ trùng.

    Example:
        >>> _resolve_prerequisite_chain(["DATA201"])
        ['PY101', 'DATA201']
    """
    ordered: list[str] = []
    seen: set[str] = set()
    visiting: set[str] = set()

    def visit(code: str) -> None:
        if code in seen or code in visiting:
            return
        course = AI_COURSES.get(code)
        if course is None:
            return
        visiting.add(code)
        for prereq in course["prerequisites"]:
            visit(prereq)
        visiting.discard(code)
        seen.add(code)
        ordered.append(code)

    for target in targets:
        visit(target)
    return ordered


def _format_course_summary(code: str, course: dict[str, Any]) -> str:
    """
    Tạo dòng tóm tắt một khóa học cho kết quả tìm kiếm.

    Args:
        code (str): Mã khóa học.
        course (dict[str, Any]): Bản ghi khóa học trong AI_COURSES.

    Returns:
        str: Một dòng gồm mã, tên, trình độ tối thiểu, giờ mỗi tuần và ngân sách.

    Example:
        >>> _format_course_summary("PY101", AI_COURSES["PY101"])
        '- PY101 | Python nhập môn | beginner | 4h/tuần | ngân sách: low'
    """
    return (
        f"- {code} | {course['title']} | {course['minimum_profile_level']} | "
        f"{course['hours_per_week']}h/tuần | ngân sách: {course['budget_level']}"
    )


def _format_course_detail(code: str, course: dict[str, Any]) -> str:
    """
    Tạo khối mô tả chi tiết đầy đủ của một khóa học.

    Args:
        code (str): Mã khóa học.
        course (dict[str, Any]): Bản ghi khóa học trong AI_COURSES.

    Returns:
        str: Chuỗi nhiều dòng mô tả toàn bộ thuộc tính của khóa.

    Example:
        >>> _format_course_detail("PY101", AI_COURSES["PY101"]).splitlines()[0]
        'Mã khóa học : PY101'
    """
    prerequisites = ", ".join(course["prerequisites"]) or "(không có)"
    required = ", ".join(course["required_skills"]) or "(không yêu cầu)"
    gained = ", ".join(course["skills_gained"]) or "(không có)"
    goals = ", ".join(course["goals"]) or "(không có)"
    specializations = ", ".join(course["specializations"]) or "(không thuộc chuyên ngành nào)"
    project = course["project_type"] or "(không có project)"

    return (
        f"Mã khóa học  : {code}\n"
        f"Tên khóa     : {course['title']}\n"
        f"Lĩnh vực     : {course['category']}\n"
        f"Trình độ cần : {course['minimum_profile_level']}\n"
        f"Thời lượng   : {course['duration_weeks']} tuần "
        f"({course['hours_per_week']} giờ/tuần, mức thời gian: {course['time_level']})\n"
        f"Ngân sách    : {course['budget_level']}\n"
        f"Thực hành    : mức {course['practice_level']} | Project: {project}\n"
        f"Tiên quyết   : {prerequisites}\n"
        f"Kỹ năng cần  : {required}\n"
        f"Kỹ năng đạt  : {gained}\n"
        f"Mục tiêu     : {goals}\n"
        f"Chuyên ngành : {specializations}\n"
        f"Mô tả        : {course['description']}"
    )


def _course_matches_keyword(course: dict[str, Any], code: str, keyword: str) -> bool:
    """
    Kiểm tra một khóa học có khớp từ khóa tìm kiếm hay không.

    Quét trên mã, tên, lĩnh vực, mục tiêu, chuyên ngành, loại project, mô tả,
    kỹ năng yêu cầu và kỹ năng đạt được.

    Args:
        course (dict[str, Any]): Bản ghi khóa học.
        code (str): Mã khóa học.
        keyword (str): Từ khóa đã chuẩn hóa.

    Returns:
        bool: True nếu từ khóa xuất hiện trong bất kỳ trường nào ở trên.

    Example:
        >>> _course_matches_keyword(AI_COURSES["ML301"], "ML301", "machine learning")
        True
    """
    haystack: list[str] = [
        code,
        course["title"],
        course["category"],
        course["description"],
        course["project_type"] or "",
        *course["goals"],
        *course["specializations"],
        *course["required_skills"],
        *course["skills_gained"],
    ]
    return any(keyword in _normalize_text(field) for field in haystack)


def _find_learning_track(goal: str) -> tuple[str, dict[str, Any]] | None:
    """
    Tìm lộ trình học khớp với mục tiêu người dùng nêu.

    Thứ tự ưu tiên: khớp chính xác title/alias, sau đó khớp substring hai chiều.
    Alias siêu ngắn (dưới _MIN_FUZZY_LEN ký tự như "ml", "dl", "ai") chỉ được
    khớp khi đứng thành một từ độc lập trong câu, để "học ML" ra kết quả mà
    "html" thì không. Khi nhiều alias cùng khớp, chọn alias dài nhất.

    Args:
        goal (str): Mục tiêu học đã chuẩn hóa.

    Returns:
        tuple[str, dict[str, Any]] | None: Cặp (track_key, track) nếu tìm thấy.

    Example:
        >>> _find_learning_track("ai agent")[0]
        'generative_ai'
        >>> _find_learning_track("học ML")[0]
        'ai_ml'
    """
    if not goal:
        return None

    goal_tokens = set(_tokenize(goal))
    best_key: str | None = None
    best_score = 0

    for key, track in LEARNING_TRACKS.items():
        candidates = [_normalize_text(track["title"]), _normalize_text(key.replace("_", " "))]
        candidates.extend(_normalize_text(alias) for alias in track["aliases"])

        for candidate in candidates:
            if not candidate:
                continue
            if candidate == goal:
                return key, track
            shorter = candidate if len(candidate) <= len(goal) else goal
            if len(shorter) < _MIN_FUZZY_LEN:
                # Alias quá ngắn để so substring an toàn -> so theo từ độc lập.
                if candidate in goal_tokens and len(candidate) > best_score:
                    best_key, best_score = key, len(candidate)
                continue
            if candidate in goal or goal in candidate:
                if len(candidate) > best_score:
                    best_key, best_score = key, len(candidate)

    if best_key is None:
        return None
    return best_key, LEARNING_TRACKS[best_key]


def _list_valid_codes() -> str:
    """
    Liệt kê toàn bộ mã khóa học hợp lệ, dùng để gợi ý khi báo lỗi.

    Returns:
        str: Các mã khóa học ngăn cách bằng dấu phẩy.

    Example:
        >>> _list_valid_codes().startswith("PY101")
        True
    """
    return ", ".join(AI_COURSES)


def _list_valid_goals() -> str:
    """
    Liệt kê các mục tiêu học hợp lệ kèm alias tiêu biểu, dùng khi báo lỗi.

    Returns:
        str: Chuỗi nhiều dòng, mỗi dòng một lộ trình và vài alias gợi ý.

    Example:
        >>> "Lộ trình Deep Learning" in _list_valid_goals()
        True
    """
    lines: list[str] = []
    for track in LEARNING_TRACKS.values():
        hints = ", ".join(track["aliases"][:4])
        lines.append(f"- {track['title']} (ví dụ: {hints})")
    return "\n".join(lines)


# =====================================================================
# 🛠️ TOOL 1 — TÌM KIẾM KHÓA HỌC
# =====================================================================

def search_ai_courses(
    keyword: str | None = None,
    level: str | None = None,
    budget_level: str | None = None,
) -> str:
    """
    Tìm các khóa học theo từ khóa, trình độ tối thiểu và ngân sách.

    Quét từ khóa trên mã, tên, lĩnh vực, mục tiêu, chuyên ngành, loại project,
    mô tả, kỹ năng yêu cầu và kỹ năng đạt được; không phân biệt hoa thường; hỗ
    trợ cả tiếng Việt và tiếng Anh có trong dữ liệu. Bỏ trống toàn bộ tham số
    thì trả về mọi khóa học. Bộ lọc ngân sách theo khả năng chi trả: ngân sách
    cao xem được cả khóa rẻ hơn.

    Args:
        keyword (str | None): Từ khóa tìm kiếm, ví dụ "machine learning", "oop",
            "internship", "python_foundation".
        level (str | None): Lọc theo trình độ tối thiểu: beginner, basic, intermediate.
        budget_level (str | None): Mức ngân sách tối đa: low, medium, high.

    Returns:
        str: Danh sách khóa khớp, mỗi dòng gồm mã, tên, trình độ, giờ/tuần và
            ngân sách. Bắt đầu bằng "KẾT QUẢ:" khi có dữ liệu, "KHÔNG CÓ KẾT QUẢ:"
            khi rỗng, hoặc "LỖI THAM SỐ:" khi level/budget không hợp lệ.

    Example:
        >>> search_ai_courses("machine learning").startswith("KẾT QUẢ:")
        True
        >>> search_ai_courses(level="beginner").count("PY101")
        1
    """
    try:
        clean_keyword = _normalize_text(keyword)

        clean_level = _validate_level(level)
        if clean_level is None:
            return (
                f"LỖI THAM SỐ: level '{level}' không hợp lệ. "
                f"Chỉ nhận: {', '.join(VALID_PROFILE_LEVELS)}."
            )

        clean_budget = _validate_budget(budget_level)
        if clean_budget is None:
            return (
                f"LỖI THAM SỐ: budget_level '{budget_level}' không hợp lệ. "
                f"Chỉ nhận: {', '.join(BUDGET_RANK)}."
            )

        matches: list[str] = []
        for code, course in AI_COURSES.items():
            if clean_keyword and not _course_matches_keyword(course, code, clean_keyword):
                continue
            if clean_level and course["minimum_profile_level"] != clean_level:
                continue
            if clean_budget and BUDGET_RANK[course["budget_level"]] > BUDGET_RANK[clean_budget]:
                continue
            matches.append(_format_course_summary(code, course))

        if not matches:
            criteria: list[str] = []
            if clean_keyword:
                criteria.append(f"từ khóa '{clean_keyword}'")
            if clean_level:
                criteria.append(f"trình độ '{clean_level}'")
            if clean_budget:
                criteria.append(f"ngân sách '{clean_budget}'")
            described = " và ".join(criteria) if criteria else "tiêu chí đã cho"
            return (
                f"KHÔNG CÓ KẾT QUẢ: Không tìm thấy khóa học nào khớp {described}. "
                f"Hãy thử từ khóa rộng hơn (ví dụ 'python', 'oop', 'machine learning', "
                f"'deep learning') hoặc nới mức ngân sách."
            )

        return f"KẾT QUẢ: Tìm thấy {len(matches)} khóa học.\n" + "\n".join(matches)

    except Exception as exc:  # noqa: BLE001 - tool không được làm vỡ vòng lặp ReAct
        return _system_error("search_ai_courses", exc)


# =====================================================================
# 🛠️ TOOL 2 — CHI TIẾT KHÓA HỌC
# =====================================================================

def get_ai_course_detail(course_code: str) -> str:
    """
    Lấy toàn bộ thông tin chi tiết của một khóa học theo mã.

    Args:
        course_code (str): Mã khóa học, ví dụ "ML301". Không phân biệt hoa thường.

    Returns:
        str: Khối chi tiết gồm tiên quyết, kỹ năng cần, kỹ năng đạt, thời lượng,
            mức thời gian, ngân sách, project, mục tiêu và chuyên ngành. Bắt đầu
            bằng "KẾT QUẢ:" khi thành công, hoặc "LỖI:" khi mã rỗng / không tồn tại.

    Example:
        >>> get_ai_course_detail("ml301").startswith("KẾT QUẢ:")
        True
        >>> get_ai_course_detail("XX999").startswith("LỖI: Không tìm thấy khóa học")
        True
    """
    try:
        if not isinstance(course_code, str):
            return "LỖI THAM SỐ: course_code phải là chuỗi, ví dụ get_ai_course_detail['ML301']."

        code = _normalize_code(course_code)
        if not code:
            return "LỖI: Mã khóa học không được để trống."

        course = AI_COURSES.get(code)
        if course is None:
            return (
                f"LỖI: Không tìm thấy khóa học '{code}'. "
                f"Các mã hợp lệ: {_list_valid_codes()}."
            )

        return f"KẾT QUẢ: Chi tiết khóa học {code}.\n" + _format_course_detail(code, course)

    except Exception as exc:  # noqa: BLE001
        return _system_error("get_ai_course_detail", exc)


# =====================================================================
# 🛠️ TOOL 3 — KIỂM TRA MỨC SẴN SÀNG
# =====================================================================

def check_course_readiness(course_code: str, current_skills: list[str]) -> str:
    """
    Đối chiếu kỹ năng hiện có của người học với kỹ năng bắt buộc của một khóa.

    Chỉ báo cáo đủ hay thiếu và thiếu những gì, kèm trình độ tối thiểu và môn
    tiên quyết của khóa để LLM có bằng chứng. Việc kết luận nên học gì tiếp theo
    thuộc về LLM, không thuộc về tool này.

    Args:
        course_code (str): Mã khóa học cần kiểm tra, ví dụ "ML301".
        current_skills (list[str]): Danh sách kỹ năng người học đang có.
            Danh sách rỗng là hợp lệ (người mới hoàn toàn).

    Returns:
        str: Bắt đầu bằng "SẴN SÀNG:" nếu đủ kỹ năng, "CHƯA SẴN SÀNG:" nếu còn
            thiếu, hoặc "LỖI:"/"LỖI THAM SỐ:" khi đầu vào không hợp lệ.

    Example:
        >>> check_course_readiness("ML301", ["python"]).startswith("CHƯA SẴN SÀNG:")
        True
        >>> check_course_readiness("PY101", []).startswith("SẴN SÀNG:")
        True
    """
    try:
        if not isinstance(course_code, str):
            return "LỖI THAM SỐ: course_code phải là chuỗi, ví dụ 'ML301'."

        code = _normalize_code(course_code)
        if not code:
            return "LỖI: Mã khóa học không được để trống."

        course = AI_COURSES.get(code)
        if course is None:
            return (
                f"LỖI: Không tìm thấy khóa học '{code}'. "
                f"Các mã hợp lệ: {_list_valid_codes()}."
            )

        if not isinstance(current_skills, list):
            return (
                "LỖI THAM SỐ: current_skills phải là danh sách (list) các kỹ năng, "
                "ví dụ ['python cơ bản', 'oop']."
            )

        if any(not isinstance(skill, str) for skill in current_skills):
            return (
                "LỖI THAM SỐ: Mỗi phần tử trong current_skills phải là chuỗi, "
                "ví dụ ['python cơ bản', 'oop']."
            )

        owned = _normalize_skill_list(current_skills)
        required = _normalize_skill_list(course["required_skills"])
        prerequisites = ", ".join(course["prerequisites"]) or "(không có)"

        context = (
            f"Khóa đang kiểm tra : {code} ({course['title']})\n"
            f"- Trình độ tối thiểu: {course['minimum_profile_level']}\n"
            f"- Môn tiên quyết    : {prerequisites}"
        )

        if not required:
            return (
                f"SẴN SÀNG: Khóa {code} không yêu cầu kỹ năng nền tảng nào.\n"
                f"{context}\n"
                f"- Kỹ năng yêu cầu   : (không yêu cầu)\n"
                f"- Người học đã có   : {', '.join(owned) or '(chưa khai báo)'}\n"
                f"- Kỹ năng còn thiếu : (không có)"
            )

        matched = [skill for skill in required if _has_skill(skill, owned)]
        missing = [skill for skill in required if skill not in matched]

        body = (
            f"{context}\n"
            f"- Kỹ năng yêu cầu   : {', '.join(required)}\n"
            f"- Người học đã có   : {', '.join(owned) or '(chưa có kỹ năng nào)'}\n"
            f"- Kỹ năng còn thiếu : {', '.join(missing) or '(không có)'}"
        )

        if missing:
            return f"CHƯA SẴN SÀNG: Còn thiếu {len(missing)}/{len(required)} kỹ năng.\n{body}"
        return f"SẴN SÀNG: Đã đủ {len(required)}/{len(required)} kỹ năng bắt buộc.\n{body}"

    except Exception as exc:  # noqa: BLE001
        return _system_error("check_course_readiness", exc)


# =====================================================================
# 🛠️ TOOL 4 — LỘ TRÌNH HỌC CHUẨN
# =====================================================================

def get_learning_track(goal: str) -> str:
    """
    Trả về lộ trình học chuẩn ứng với mục tiêu người dùng.

    Thứ tự học được suy ra từ đồ thị prerequisites trong catalog, nên luôn đúng
    thứ tự học được. Tool không cá nhân hóa và không loại bớt khóa dựa trên kỹ
    năng người dùng — việc đó thuộc phần suy luận của LLM.

    Args:
        goal (str): Mục tiêu học, tiếng Việt hoặc tiếng Anh. Ví dụ "học python",
            "python nâng cao", "machine learning", "xây ai agent", "thực tập".

    Returns:
        str: Tên lộ trình, mô tả và chuỗi mã kèm tên khóa theo thứ tự. Bắt đầu
            bằng "KẾT QUẢ:" khi tìm thấy, "KHÔNG CÓ LỘ TRÌNH:" khi không khớp,
            hoặc "LỖI:" khi mục tiêu để trống.

    Example:
        >>> get_learning_track("ai agent").startswith("KẾT QUẢ:")
        True
        >>> get_learning_track("nấu ăn").startswith("KHÔNG CÓ LỘ TRÌNH:")
        True
    """
    try:
        if not isinstance(goal, str):
            return "LỖI THAM SỐ: goal phải là chuỗi, ví dụ get_learning_track['ai agent']."

        clean_goal = _normalize_text(goal)
        if not clean_goal:
            return "LỖI: Mục tiêu học không được để trống."

        found = _find_learning_track(clean_goal)
        if found is None:
            return (
                f"KHÔNG CÓ LỘ TRÌNH: Không tìm thấy lộ trình khớp mục tiêu '{clean_goal}'.\n"
                f"Các mục tiêu hợp lệ:\n{_list_valid_goals()}"
            )

        _, track = found
        sequence = _resolve_prerequisite_chain(track["targets"])
        if not sequence:
            return (
                f"KHÔNG CÓ LỘ TRÌNH: Lộ trình '{track['title']}' chưa có khóa học nào "
                f"trong catalog."
            )

        steps: list[str] = []
        total_weeks = 0
        for index, code in enumerate(sequence, start=1):
            course = AI_COURSES[code]
            total_weeks += course["duration_weeks"]
            steps.append(
                f"  {index}. {code} — {course['title']} "
                f"({course['duration_weeks']} tuần, {course['hours_per_week']}h/tuần, "
                f"ngân sách {course['budget_level']})"
            )

        chain = " → ".join(sequence)
        return (
            f"KẾT QUẢ: Lộ trình chuẩn cho mục tiêu '{clean_goal}'.\n"
            f"Tên lộ trình : {track['title']}\n"
            f"Mô tả        : {track['description']}\n"
            f"Thứ tự học   : {chain}\n"
            f"Tổng thời gian: {total_weeks} tuần cho {len(sequence)} khóa\n"
            f"Chi tiết     :\n" + "\n".join(steps)
        )

    except Exception as exc:  # noqa: BLE001
        return _system_error("get_learning_track", exc)


# =====================================================================
# 🛠️ TOOL 5 — LỌC THEO THỜI GIAN VÀ NGÂN SÁCH
# =====================================================================

def filter_courses_by_constraints(
    course_codes: list[str],
    available_hours_per_week: int | str,
    budget_level: str,
) -> str:
    """
    Phân loại một danh sách khóa học theo ràng buộc thời gian và ngân sách.

    Một khóa phù hợp về thời gian khi hours_per_week <= số giờ người học có.
    Một khóa phù hợp về ngân sách khi mức của khóa không cao hơn mức người học
    (low < medium < high). Tool chỉ phân loại và nêu lý do, không xếp hạng và
    không khuyên chọn khóa nào.

    Args:
        course_codes (list[str]): Danh sách mã khóa học cần lọc.
        available_hours_per_week (int | str): Số giờ học được mỗi tuần (số nguyên
            dương), hoặc mức thời gian theo TIME_RULES: "ít"/"low" (<=4h),
            "vừa"/"medium" (<=8h), "nhiều"/"high" (<=12h).
        budget_level (str): Ngân sách người học: low, medium hoặc high.

    Returns:
        str: Hai nhóm "PHÙ HỢP" và "CHƯA PHÙ HỢP" kèm lý do cụ thể cho từng khóa
            chưa phù hợp. Bắt đầu bằng "KẾT QUẢ:", hoặc "LỖI THAM SỐ:" khi đầu
            vào không hợp lệ.

    Example:
        >>> filter_courses_by_constraints(["PY101", "ML301"], 5, "low").startswith("KẾT QUẢ:")
        True
        >>> filter_courses_by_constraints(["PY101"], "ít", "low").startswith("KẾT QUẢ:")
        True
    """
    try:
        if not isinstance(course_codes, list):
            return (
                "LỖI THAM SỐ: course_codes phải là danh sách (list) mã khóa học, "
                "ví dụ ['PY101', 'ML301']."
            )

        if any(not isinstance(code, str) for code in course_codes):
            return (
                "LỖI THAM SỐ: Mỗi phần tử trong course_codes phải là chuỗi, "
                "ví dụ ['PY101', 'ML301']."
            )

        max_hours = _resolve_hours(available_hours_per_week)
        if max_hours is None:
            return (
                f"LỖI THAM SỐ: available_hours_per_week '{available_hours_per_week}' "
                f"không hợp lệ. Nhận số nguyên dương (ví dụ 6) hoặc mức thời gian: "
                f"ít/low (<=4h), vừa/medium (<=8h), nhiều/high (<=12h)."
            )

        clean_budget = _validate_budget(budget_level)
        if not clean_budget:
            return (
                f"LỖI THAM SỐ: budget_level '{budget_level}' không hợp lệ. "
                f"Chỉ nhận: {', '.join(BUDGET_RANK)}."
            )

        if not course_codes:
            return "KHÔNG CÓ KẾT QUẢ: Danh sách course_codes rỗng, không có gì để lọc."

        budget_cap = BUDGET_RANK[clean_budget]
        fits: list[str] = []
        unfits: list[str] = []
        invalids: list[str] = []

        for raw_code in course_codes:
            code = _normalize_code(raw_code)
            course = AI_COURSES.get(code)
            if course is None:
                invalids.append(f"- {raw_code} | mã không hợp lệ, không có trong catalog")
                continue

            hours = course["hours_per_week"]
            enough_time = hours <= max_hours
            enough_budget = BUDGET_RANK[course["budget_level"]] <= budget_cap

            if enough_time and enough_budget:
                fits.append(
                    f"- {code} | {course['title']} | {hours}h/tuần | "
                    f"ngân sách: {course['budget_level']}"
                )
                continue

            reasons: list[str] = []
            if not enough_time:
                reasons.append(f"thiếu thời gian (cần {hours}h/tuần, có {max_hours}h/tuần)")
            if not enough_budget:
                reasons.append(
                    f"vượt ngân sách (khóa mức {course['budget_level']}, "
                    f"người học mức {clean_budget})"
                )
            unfits.append(f"- {code} | {course['title']} | " + " và ".join(reasons))

        blocks: list[str] = [
            f"KẾT QUẢ: Đã lọc {len(course_codes)} khóa với "
            f"{max_hours}h/tuần và ngân sách {clean_budget}."
        ]
        blocks.append("PHÙ HỢP:\n" + ("\n".join(fits) if fits else "- (không có khóa nào)"))
        blocks.append(
            "CHƯA PHÙ HỢP:\n" + ("\n".join(unfits) if unfits else "- (không có khóa nào)")
        )
        if invalids:
            blocks.append("MÃ KHÔNG HỢP LỆ:\n" + "\n".join(invalids))

        return "\n".join(blocks)

    except Exception as exc:  # noqa: BLE001
        return _system_error("filter_courses_by_constraints", exc)


# =====================================================================
# 📇 TOOL REGISTRY — danh sách tool ReAct Agent được phép gọi
# =====================================================================

AVAILABLE_TOOLS = {
    "search_ai_courses": search_ai_courses,
    "get_ai_course_detail": get_ai_course_detail,
    "check_course_readiness": check_course_readiness,
    "get_learning_track": get_learning_track,
    "filter_courses_by_constraints": filter_courses_by_constraints,
}
