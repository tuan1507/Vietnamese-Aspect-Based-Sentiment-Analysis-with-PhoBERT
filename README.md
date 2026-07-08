# ABSA Analyzer — Phân tích cảm xúc tiếng Việt theo khía cạnh

> Tự động trích xuất khía cạnh và phân loại cảm xúc từ đánh giá sản phẩm điện tử tiếng Việt, sử dụng PhoBERT.

## Dùng thử nhanh

Mở [Live Demo trên HuggingFace](https://huggingface.co/spaces/Naut1507/Absa-Analyzer) — upload file CSV → chọn cột → bấm Chạy.

> Demo chạy CPU miễn phí, nên dùng file dưới 200 dòng. File lớn hơn thì chạy local (xem bên dưới).

---

## Chạy trên máy local

```bash
git clone https://github.com/tuan1507/Vietnamese-Aspect-Based-Sentiment-Analysis-with-PhoBERT.git
cd Vietnamese-Aspect-Based-Sentiment-Analysis-with-PhoBERT
pip install -r requirements.txt
python scripts/download_models.py   # tải model từ HuggingFace về máy (chỉ cần 1 lần)
streamlit run app.py
```

---

## Dữ liệu sử dụng

Dataset đánh giá sản phẩm điện tử tiếng việt thu thập từ các sàn thương mại điện tử, gồm điện thoại, laptop và phụ kiện.

| File | Mô tả | Số dòng |
|---|---|---|
| `Dataset_ATE_final.csv` | Gán nhãn B-ASP / I-ASP / O theo chuẩn BIO, dùng train model ATE 
| `Dataset_ASC_final.csv` | Gán nhãn Tích cực / Tiêu cực cho từng cặp (câu, aspect), dùng train model ASC

Dataset đầy đủ (thô + đã xử lý) lưu tại: [Naut1507/Vietnamese-product-reviewss](https://huggingface.co/datasets/Naut1507/Vietnamese-product-reviewss)

---

## 13 danh mục khía cạnh

Mỗi aspect thô trích xuất từ câu đánh giá sẽ được chuẩn hóa về 1 trong 13 danh mục sau:

| # | Danh mục | Ví dụ aspect thô nhận diện được |
|---|---|---|
| 1 | **Pin & Sạc** | pin, bin, sạc nhanh, củ sạc, cổng sạc, sạc dự phòng |
| 2 | **Âm thanh** | loa, bass, mic, tai nghe, chống ồn, chất âm, thu âm |
| 3 | **Màn hình** | màn hình, cảm ứng, vân tay, độ sáng, màn cong |
| 4 | **Camera & Chụp ảnh** | camera, cam sau, chụp đêm, quay video, zoom, flash |
| 5 | **Hiệu năng & Cấu hình** | chip, hiệu năng, độ mượt, tản nhiệt, phần mềm, AI |
| 6 | **Thiết kế & Ngoại hình** | thiết kế, màu sắc, chất liệu, kích thước, ốp lưng, bản lề |
| 7 | **Kết nối** | wifi, bluetooth, sim, 5G, NFC, tín hiệu, bắt sóng |
| 8 | **Nghe gọi** | cuộc gọi, đàm thoại, loa thoại, mic thoại, nhạc chuông |
| 9 | **Bàn phím & Nút bấm** | bàn phím, touchpad, nút bấm, đèn bàn phím, bút spen |
| 10 | **Giá cả** | giá, khuyến mãi, trả góp, tầm giá, giảm giá |
| 11 | **Bảo hành & Đổi trả** | bảo hành, đổi trả, sửa chữa, chính sách bảo hành |
| 12 | **Nhân viên & Dịch vụ** | nhân viên, tư vấn, chăm sóc khách hàng, thái độ |
| 13 | **Giao hàng & Cửa hàng** | giao hàng, đóng gói, cửa hàng, nhân viên giao hàng |

---

## Mô hình

| Model | Nhiệm vụ | Link |
|---|---|---|
| PhoBERT-base-v2 fine-tune | ATE — Trích xuất aspect (BIO tagging) | [Naut1507/PhoBert_Vi_ATE](https://huggingface.co/Naut1507/PhoBert_Vi_ATE) |
| PhoBERT-base-v2 fine-tune | ASC — Phân loại cảm xúc (Tích cực / Tiêu cực) | [Naut1507/PhoBert_Vi_ASC](https://huggingface.co/Naut1507/PhoBert_Vi_ASC) |

---

## Tính năng

- 🎯 2 model PhoBERT fine-tune riêng cho ATE và ASC
- 📊 Dashboard tương tác — biểu đồ theo sản phẩm, khía cạnh, xu hướng
- 🧠 13 danh mục aspect + fuzzy matching cho từ sai chính tả / viết tắt
- 📁 Lưu cache kết quả — xem lại lịch sử phân tích không cần chạy lại

---

## Cấu trúc project

```
app.py                          # Khởi chạy app Streamlit
requirements.txt                # Thư viện cần cài
Dockerfile                      # Deploy bằng Docker
│
├── main_dasboard/
│   └── dashboard.html          # Giao diện dashboard (HTML template gốc)
│
├── absa/                       # Toàn bộ logic AI và xử lý dữ liệu
│   ├── models.py               # Nạp 2 model PhoBERT (ATE + ASC)
│   ├── inference.py            # Chạy AI: trích aspect → chấm cảm xúc
│   ├── aspect_category.py      # Chuẩn hóa aspect về 13 danh mục cố định
│   ├── data_builder.py         # Tính số liệu, tạo JSON cho dashboard
│   ├── utils.py                # Đường dẫn, làm sạch text, cache
│   └── static/
│       ├── css/
│       │   ├── upload.css          # CSS trang upload
│       │   ├── dashboard.css       # CSS dashboard chính
│       │   └── dashboard_iframe.css# CSS khi nhúng vào Streamlit
│       └── js/
│           └── dashboard.js        # Vẽ biểu đồ, xử lý tương tác
│
├── scripts/
│   ├── download_models.py      # Tải model từ HuggingFace Hub về máy
│   └── upload_dataset.py       # Upload data lên HuggingFace Datasets
│
└── output/                     # Tự sinh ra khi chạy app, không cần chỉnh
    └── dashboard_component/
        └── index.html
```

---

## License

MIT