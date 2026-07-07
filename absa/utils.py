
import os
import re
import hashlib
import unicodedata

# ── Đường dẫn (neo theo vị trí file absa/utils.py để chạy được từ cwd bất kỳ) ──
# BASE_DIR là thư mục cha của package absa/ — chính là project root (nơi chứa app.py).
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR     = os.path.join(BASE_DIR, "cache_data")
COMP_DIR      = os.path.join(BASE_DIR, "dashboard_component")
HTML_TEMPLATE = os.path.join(BASE_DIR, "index.html")   # template gốc
HTML_OUTPUT   = os.path.join(COMP_DIR, "index.html")    # file render inject vào


def ensure_dirs():
    """Tạo cache_data/ và dashboard_component/ nếu chưa có."""
    for d in (CACHE_DIR, COMP_DIR):
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)


# ── Preprocess text đầu vào ──────────────────────────────────────────────────
_URL_RE  = re.compile(r"https?://\S+|www\.\S+")
_HTML_RE = re.compile(r"<[^>]+>")
_WS_RE   = re.compile(r"\s+")

def preprocess_text(text) -> str:
    """
    Làm sạch text đầu vào: bỏ URL, thẻ HTML, chuẩn hoá unicode NFC, gộp khoảng
    trắng. KHÔNG lowercase để giữ dấu và ngữ nghĩa cho PhoBERT.
    """
    if not isinstance(text, str):
        return ""
    s = unicodedata.normalize("NFC", text)
    s = _URL_RE.sub(" ", s)
    s = _HTML_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def file_md5(data: bytes) -> str:
    """MD5 hash 1 file (dùng làm cache key per-file)."""
    return hashlib.md5(data).hexdigest()