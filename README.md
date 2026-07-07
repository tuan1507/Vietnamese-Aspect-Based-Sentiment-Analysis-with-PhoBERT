# ABSA Analyzer

Hệ thống phân tích cảm xúc đa khía cạnh (Aspect-Based Sentiment Analysis)
cho tiếng Việt, dựa trên PhoBERT.

## Cấu trúc thư mục

```
1.DACN3/
├── app.py                  # Streamlit entrypoint (~730 dòng)
├── index.html              # Template dashboard
├── .streamlit/
│   └── config.toml         # Ép Streamlit dùng light theme
├── absa/                   # Package business logic (import từ đây)
│   ├── __init__.py         # Public API
│   ├── utils.py            # Đường dẫn + preprocess + hash
│   ├── taxonomy.py         # 13 danh mục + normalize + fuzzy fallback
│   ├── models.py           # Load PhoBERT + dò weight/tokenizer
│   ├── inference.py        # Batch ATE + Batch ASC + FP16 autocast
│   └── dashboard.py        # Build JSON + inject HTML (có @st.cache_data)
├── ate_phobert/            # Weight model ATE (bạn để sẵn)
├── asc_phobert/            # Weight model ASC (bạn để sẵn)
├── dashboard_component/    # Streamlit component dir (tự tạo)
└── cache_data/             # Cache DataFrame kết quả (tự tạo)
```

## Chạy

```bash
cd 1.DACN3
streamlit run app.py
```

## Tối ưu chính so với bản cũ

| Vấn đề | Bản cũ | Bản mới |
|---|---|---|
| **Tốc độ inference** | Vòng lặp 1-1, GPU 22% | Batch 32, FP16 autocast, GPU 80-95% |
| **Load dashboard** | Tính lại DataFrame mỗi F5 | `@st.cache_data` — cache hit <10ms |
| **Aspect ngoài từ điển** | Drop luôn | Fuzzy fallback (Levenshtein, cached LRU 4096) |
| **Từ generic ("máy", "điện thoại")** | Sang danh mục chung chung | Blacklist → drop khỏi analytics |
| **Tổ chức code** | 1 file 2240 dòng | app.py 730 + 5 module rõ vai trò |

Ước tính:
- **4,246 dòng CSV**: ~15-25 phút → **30-60 giây**
- **VRAM peak**: ~500MB → ~2-3 GB (thoải mái với 5060 Ti 16GB)

## Extending taxonomy (khi có domain mới)

Sửa `absa/taxonomy.py`:

```python
ASPECT_TAXONOMY = {
    "Danh mục mới": (
        "keyword 1", "keyword 2", ...,
    ),
    # ...
}
```

Fuzzy matching sẽ tự động bắt các typo/biến thể (`cammera` → `camera`).
Nếu thấy generic term không muốn phân loại, thêm vào `_GENERIC_BLACKLIST`.

## Public API

Import từ `absa`:

```python
from absa import (
    BASE_DIR, CACHE_DIR, HTML_TEMPLATE, COMP_DIR,
    load_models, phan_tich_batch, phan_tich_ai_that,
    ASPECT_TAXONOMY, is_valid_taxonomy,
    preprocess_text, file_md5, ensure_dirs,
    build_json_for_html, inject_html_data,
)
```