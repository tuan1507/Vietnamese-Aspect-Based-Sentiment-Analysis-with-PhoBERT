
from huggingface_hub import HfApi
import os

# ── CẤU HÌNH ────────────────────────────────────────────────────────────────
HF_USERNAME  = "Naut1507"                        
DATASET_NAME = "Vietnamese-product-reviewss"         
REPO_ID      = f"{HF_USERNAME}/{DATASET_NAME}"

# Các file/thư mục cần upload (đường dẫn tính từ thư mục gốc project)
FILES_TO_UPLOAD = [
    # ── Data thô từ TGDD ──────────────────────────────────────────────────
    {
        "local": "1.DataRaw/tgdd_final.csv",
        "remote": "raw/tgdd_final.csv",
        "desc": "Toàn bộ review"
    },
    {
        "local": "1.DataRaw/tgdd_laptop_reviews_raw.csv",
        "remote": "raw/tgdd_laptop_reviews_raw.csv",
        "desc": "Review laptop thô"
    },
    {
        "local": "1.DataRaw/tgdd_phukien_reviews_raw.csv",
        "remote": "raw/tgdd_phukien_reviews_raw.csv",
        "desc": "Review phụ kiện thô"
    },
    {
        "local": "1.DataRaw/tgdd_phone_reviews_raw.csv",
        "remote": "raw/tgdd_phone_reviews_raw.csv",
        "desc": "Review điện thoại thô"
    },

    # ── Data đã xử lý, dùng để train ─────────────────────────────────────
    {
        "local": "2.ProcessingData/data_processing.csv",
        "remote": "processed/data_processing.csv",
        "desc": "Data sau khi làm sạch"
    },
    {
        "local": "2.ProcessingData/Dataset_ATE_final.csv",
        "remote": "processed/Dataset_ATE_final.csv",
        "desc": "Dataset cuối dùng train model ATE"
    },
    {
        "local": "2.ProcessingData/Dataset_ASC_final.csv",
        "remote": "processed/Dataset_ASC_final.csv",
        "desc": "Dataset cuối dùng train model ASC"
    },
]
# ────────────────────────────────────────────────────────────────────────────


def main():
    api = HfApi()

    # 1. Tạo repo dataset (bỏ qua nếu đã tồn tại)
    print(f"Tạo dataset repo: {REPO_ID}")
    api.create_repo(
        repo_id=REPO_ID,
        repo_type="dataset",
        exist_ok=True,   # không báo lỗi nếu đã có
        private=False,
    )
    print("✅ Repo sẵn sàng\n")

    # 2. Upload từng file
    for item in FILES_TO_UPLOAD:
        local_path  = item["local"]
        remote_path = item["remote"]

        if not os.path.exists(local_path):
            print(f"⚠️  Bỏ qua (không tìm thấy): {local_path}")
            continue

        size_mb = os.path.getsize(local_path) / 1024 / 1024
        print(f"⬆️  Đang upload: {local_path}  ({size_mb:.1f} MB)")
        print(f"    → {REPO_ID}/{remote_path}")

        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=remote_path,
            repo_id=REPO_ID,
            repo_type="dataset",
            commit_message=f"Upload {remote_path}",
        )
        print(f"    ✅ Xong\n")

    # 3. Upload README riêng cho dataset
    dataset_readme = f"""---
language:
- vi
task_categories:
- text-classification
- token-classification
tags:
- aspect-based-sentiment-analysis
- vietnamese
- phobert
- absa
pretty_name: TGDD Vietnamese Product Reviews
---

# TGDD Vietnamese Product Reviews

Dataset đánh giá sản phẩm điện tử tiếng Việt thu thập từ các sàn thương mại điện tử,
dùng để train 2 model PhoBERT cho bài toán ABSA (Aspect-Based Sentiment Analysis).

## Nội dung

| Thư mục | Mô tả |
|---|---|
| `raw/` | Data thô crawl từ TGDD |
| `processed/` | Data đã làm sạch, gán nhãn, sẵn sàng train |

## File chính

| File | Dùng để |
|---|---|
| `processed/Dataset_ATE_final.csv` | Train model ATE (trích xuất aspect) |
| `processed/Dataset_ASC_final.csv` | Train model ASC (phân loại cảm xúc) |

## Model đã train

- ATE: [Naut1507/PhoBert_Vi_ATE](https://huggingface.co/Naut1507/PhoBert_Vi_ATE)
- ASC: [Naut1507/PhoBert_Vi_ASC](https://huggingface.co/Naut1507/PhoBert_Vi_ASC)

## Project

[Vietnamese-ABSA-with-PhoBERT](https://github.com/tuan1507/Vietnamese-Aspect-Based-Sentiment-Analysis-with-PhoBERT)
"""
    api.upload_file(
        path_or_fileobj=dataset_readme.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=REPO_ID,
        repo_type="dataset",
        commit_message="Add dataset README",
    )

    print("=" * 50)
    print(f"✅ Upload hoàn tất!")
    print(f"🔗 https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()