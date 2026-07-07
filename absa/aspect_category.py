import re
from functools import lru_cache
from difflib import SequenceMatcher


# 13 DANH MỤC 
ASPECT_CATEGORIES = {
    "Pin & Sạc": (
        "pin", "bin", "pín", "pim", "pun", "pit", "lỗi pin", "pin nhanh",
        "sạc", "xạc", "sạt", "sạc nhanh", "sạc pin", "sạc siêu nhanh", "sạc không dây",
        "hộp sạc", "cục sạc", "củ sạc", "cốc sạc", "cổng sạc", "dây sạc", "dây cáp sạc",
        "dock sạc", "chỗ sạc", "nguồn sạc", "nguồn", "đèn sạc", "sạc magsafe",
        "sạc dự phòng", "pin sạc dự phòng",
    ),
    "Âm thanh": (
        "âm thanh", "ân thanh", "âm", "chất âm", "chất lượng âm", "chất lượng âm thanh",
        "loa", "loa ngoài", "loa trong", "loa kép", "loa đơn",
        "bass", "treble", "treb", "trép", "mid", "âm bass", "âm trầm",
        "bass trầm", "bass boost", "bas boost", "tiếng bass",
        "mic", "micro", "microphone", "miccro", "mic đàm thoại",
        "chống ồn", "chống ổn", "khử tiếng ồn", "tiếng ồn", "cách âm", "xuyên âm", "lọc âm",
        "chống ồn chủ động", "chế độ chống ồn", "chức năng chống ồn",
        "âm lượng", "âm lương",
        "tai nghe", "tai ghe", "tại nghe", "tay nghe", "tai", "hộp tai nghe", "miếng lót tai",
        "anc", "chuyển bài", "âm nghe", "âm báo", "nhạc", "nghe nhạc", "xem phim",
        "thu âm", "ghi âm",
    ),
    "Nhân viên & Dịch vụ": (
        "nhân viên", "nhân sự", "nv", "cskh", "chăm sóc khách hàng", "chăm sóc",
        "phục vụ", "tư vấn", "hỗ trợ", "hổ trợ", "dịch vụ", "quản lý", "quản lí",
        "kỹ thuật viên", "kĩ thuật viên", "kỉ thuật viên", "kỹ thuật", "kĩ thuật",
        "thái độ", "hotline", "tổng đài", "khiếu nại", "tiếp đón", "chị bán hàng",
        "thẩm định", "chăm sóc sau bán", "dịch vụ khách hàng", "dịch vụ tư vấn",
    ),
    "Kết nối": (
        "kết nối", "kết nói", "kêt nối", "kiết nối",
        "wifi", "wf", "sóng", "sống", "sim", "khe sim", "sóng sim",
        "bluetooth", "blt", "mạng", "5 g", "4 g", "3 g", "nfc", "nc",
        "tín hiệu", "bắt sóng", "thu sóng", "sóng di động", "sóng điện thoại",
    ),
    "Màn hình": (
        "màn hình", "man hinh", "màn", "màn cong", "màn 2 k", "màn hình led", "màn hình cảm ứng",
        "cảm ứng", "cảm ứng vân tay", "cảm biến chạm", "cảm biến tiệm cận", "cảm biến",
        "vân tay", "vân", "khóa vâng tay", "dấu vân tay", "cảm biến vân tay",
        "hiển thị", "độ sáng", "độ sáng màn hình",
    ),
    "Camera & Chụp ảnh": (
        "camera", "cam", "máy ảnh", "cụm camera",
        "chụp", "chục ảnh", "chụp ảnh", "chụp hình", "chup hình", "chụp đêm",
        "cam sau", "cam trước", "cam chính", "camera trước", "camera sau", "camera chính",
        "camera ai", "camera zeiss", "camera chéo",
        "quay video", "quay phim", "video quay", "zoom", "flash",
        "ảnh", "ảnh chụp", "ảnh màu", "tốc độ chụp", "chống rung",
    ),
    "Bảo hành & Đổi trả": (
        "bảo hành", "bảo hàng", "bhanh", "bhành", "bảo hiểm",
        "chế độ bảo hành", "chính sách bảo hành", "gói bảo hành",
        "đổi trả", "đổi", "sửa chữa", "gửi máy", "dịch vụ sửa chữa", "đổi trả hàng",
    ),
    "Giá cả": (
        "giá", "giá tiền", "giá cả", "giá thành", "giá rẻ", "giá cả hợp lý",
        "mức giá", "tầm giá", "tiền", "giảm giá", "khuyến mãi", "trả góp",
        "hợp đồng tín dụng", "giá trị sản phẩm",
    ),
    "Thiết kế & Ngoại hình": (
        "thiết kế", "ngoại hình", "ngoại quan", "ngoại",
        "kiểu dáng", "mẫu mã", "hình thức", "hình thức mẫu mã", "form",
        "màu", "màu sắc", "màu tím", "màu hồng", "màu hồng nude", "màu đen",
        "màu đỏ", "màu vàng", "màu golden", "màu sơn", "sơn", "vạch cam",
        "titan", "ốp lưng", "kính mặt lưng", "vỏ máy", "vỏ điện thoại", "võ bên ngoài",
        "chất liệu", "hoàn thiện", "chất lượng hoàn thiện",
        "kích thước", "kích thước máy", "kết cấu", "khớp gập", "phần gập", "bản lề",
        "bên ngoài", "phần bọc", "kháng bụi kháng nước", "cảm giác đeo",
    ),
    "Nghe gọi": (
        "nghe gọi", "nghe ngọi", "gọi thoại", "cuộc gọi", "đàm thoại",
        "loa thoại", "loa đàm thoại", "mic thoại", "chuông", "nhạc chuông",
        "nói chuyện", "gọi", "gọi nhắn tin", "đàm thoại qua tai nghe",
        "âm thanh nhắc nhở", "âm thanh khi có cuộc gọi",
    ),
    "Hiệu năng & Cấu hình": (
        "hiệu năng", "cấu hình", "chip", "chất lượng",
        "độ mượt", "đa nhiệm", "tản nhiệt", "quạt tản nhiệt", "tản",
        "tốc độ", "độ trễ", "độ bền", "bền", "sài bền",
        "phần mềm", "phần cứng", "hệ điều hành", "ứng dụng", "app", "ứng dụng tiktok",
        "ai", "galaxy ai", "tốc độ xử lí", "nhiệt độ máy", "sập nguồn",
    ),
    "Bàn phím & Nút bấm": (
        "bàn phím", "phím bấm", "phím", "phímt", "nút bấm", "nút ấn", "nút lệnh",
        "nút chạm", "nút đài", "touchpad", "tuochpad", "trackpad", "touch bar",
        "đèn bàn phím", "phím số", "phím chức năng", "các phím chức năng",
        "mặt bàn phím", "bút spen",
    ),
    "Giao hàng & Cửa hàng": (
        "giao hàng", "gao hàng", "giao hang", "giao hàng trễ",
        "nhân viên giao hàng", "chuyển hàng nhanh", "dịch vụ giao hàng",
        "đóng gói", "đặt hàng", "shop", "cửa hàng", "tgdd", "nhân viên tgdd",
        "bán hàng", "nhân viên bán hàng", "nhân viên shop", "nhân viên cửa hàng",
        "cửa hàng chăm sóc khách", "thái độ bán hàng",
    ),
}

_KEYWORDS_SORTED = sorted(
    ((cat, kw.lower()) for cat, kws in ASPECT_CATEGORIES.items() for kw in kws),
    key=lambda x: (-len(x[1]), x[0])
)

_KW_TO_CAT = {kw: cat for cat, kw in _KEYWORDS_SORTED}
_ALL_KEYWORDS = list(_KW_TO_CAT.keys())
_VALID_CATS = set(ASPECT_CATEGORIES.keys())

_SPEC_TAIL = re.compile(
    r"^(pin|sạc nhanh|sạc|camera|cam|wifi|sóng 4 g|sóng|màn hình|màn|loa)"
    r"\s+\d[\w\s]*$"
)

# Ngưỡng similarity cho fuzzy match. 0.82 chọn thực nghiệm:
#   bắt được typo phổ biến  ("cammera"→"camera": 0.86, "bảo hàh"→"bảo hành": 0.86)
#   không match nhầm generic ("điện thoại" vs "vỏ điện thoại": 0.87 — sẽ bị chặn
_FUZZY_CUTOFF = 0.82

# Blacklist các generic term mà user không muốn phân loại (các từ quá tổng quát)
_GENERIC_BLACKLIST = frozenset({
    "sản phẩm", "sảm phẩm", "sp", "máy", "laptop", "đt", "điện thoại",
    "di động", "thiết bị", "hàng", "vỏ", "hộp",
})


def _fuzzy_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


@lru_cache(maxsize=4096)
def _fuzzy_lookup(s: str) -> str | None:
    best_kw, best_score = None, 0.0
    for kw in _ALL_KEYWORDS:
        # Optimization: chỉ so khi độ dài chênh không quá 3 ký tự
        if abs(len(kw) - len(s)) > 3:
            continue
        sc = _fuzzy_similarity(s, kw)
        if sc > best_score:
            best_score, best_kw = sc, kw
    if best_score < _FUZZY_CUTOFF or best_kw is None:
        return None
    # Nếu s là substring của keyword → là generic/prefix, không match
    if s in best_kw:
        return None
    return _KW_TO_CAT[best_kw]


def normalize_aspect(raw) -> str | None:
    """
    Chuẩn hoá 1 aspect thô từ ATE về 1 trong 13 danh mục cố định.
    Pipeline:
      1. Cắt spec đuôi số (pin 5800 → pin)
      2. Blacklist generic (điện thoại, máy, sp... → None)
      3. Exact keyword match (nhanh, ~95% coverage)
      4. Fuzzy fallback (bắt typo/biến thể mới, cached)
    Returns:
        Tên danh mục (str), hoặc None nếu không phân loại được → sẽ DROP khỏi analytics.
    """
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip().lower().replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    if len(s) < 2:
        return None
    m = _SPEC_TAIL.match(s)
    if m:
        s = m.group(1)
    # 1) Blacklist generic — drop trước cả exact match
    if s in _GENERIC_BLACKLIST:
        return None
    # 2) Exact substring match (dài trước ngắn)
    for cat, kw in _KEYWORDS_SORTED:
        if kw in s:
            return cat
    # 3) Fuzzy fallback cho typo/biến thể mới
    return _fuzzy_lookup(s)


def is_valid_ASPECT_CATEGORIES(aspect_values) -> bool:
    vals = {str(v) for v in aspect_values if v is not None and str(v) != "nan"}
    return bool(vals) and vals.issubset(_VALID_CATS)