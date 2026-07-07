---
title: Absa Analyzer
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8501
app_file: app.py
pinned: false
license: mit
---

# ABSA Analyzer — Vietnamese Aspect-Based Sentiment Analysis

> Hệ thống phân tích cảm xúc đa khía cạnh cho tiếng Việt, xây trên PhoBERT.

## Quick Start

```bash
git clone https://github.com/tuan1507/Vietnamese-Aspect-Based-Sentiment-Analysis-with-PhoBERT.git
cd Vietnamese-Aspect-Based-Sentiment-Analysis-with-PhoBERT
pip install -r requirements.txt
python scripts/download_models.py
streamlit run app.py
```

## 🏗 Architecture

```
app.py                  # Streamlit entrypoint
index.html              # Dashboard template
absa/
├── __init__.py         # Public API
├── utils.py            # Paths, preprocess, hash
├── aspect_category.py  # 13 categories + fuzzy normalize
├── models.py           # Load PhoBERT + resolvers
├── inference.py        # Batch ATE + Batch ASC + FP16
└── dashboard.py        # Build JSON + inject HTML
scripts/
└── download_models.py  # Tải model từ HuggingFace Hub
```

## ✨ Features

- 🎯 **2 mô hình PhoBERT-base** fine-tune cho ATE + ASC
- 📊 **Dashboard tương tác** — biểu đồ cảm xúc theo sản phẩm, khía cạnh
- 🧠 **13 danh mục aspect** + fuzzy fallback cho từ mới/typo
- ⚡ **Batch inference GPU** — 4,000 dòng CSV trong ~1 phút
- 🎨 **UI light theme** — ổn định trên mọi chế độ trình duyệt

##  Models

- **ATE**: [Naut1507/PhoBert_Vi_ATE](https://huggingface.co/Naut1507/PhoBert_Vi_ATE)
- **ASC**: [Naut1507/PhoBert_Vi_ASC](https://huggingface.co/Naut1507/PhoBert_Vi_ASC)

## 📄 License

## Dùng thử

1. Mở [Live Demo](https://huggingface.co/spaces/Naut1507/Absa-Analyzer)
2. Upload file → chọn cột văn bản → bấm Chạy Phân tích
3. Xem dashboard kết quả

> ⚠️ Demo chạy trên CPU free tier — nên dùng file <200 dòng để kết quả nhanh.
> Với file lớn, clone repo và chạy local với GPU.

MIT