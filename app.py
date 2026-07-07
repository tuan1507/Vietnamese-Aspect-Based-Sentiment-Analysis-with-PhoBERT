import streamlit as st
import pandas as pd
import numpy as np
import json
import base64
import os
import shutil
import streamlit.components.v1 as components
import time
import re

# ── AUTO-DOWNLOAD MODEL NẾU CHƯA CÓ (cho HuggingFace Spaces + user mới clone) ──
def _ensure_models_downloaded():
    """Tải model từ HF Hub nếu chưa có. Chạy 1 lần lúc khởi động."""
    from pathlib import Path
    ate_ok = any(Path("ate_phobert").rglob("model.safetensors"))
    asc_ok = any(Path("asc_phobert").rglob("model.safetensors"))
    if ate_ok and asc_ok:
        return   # đã có đủ, bỏ qua
    import streamlit as _st
    _st.info("⏳ Đang tải model từ HuggingFace Hub (chỉ lần đầu, mất vài phút)...")
    from huggingface_hub import snapshot_download
    if not ate_ok:
        snapshot_download(
            repo_id="Naut1507/PhoBert_Vi_ATE",
            local_dir="ate_phobert/phobert_ate_v3/best_model",
            local_dir_use_symlinks=False,
        )
    if not asc_ok:
        snapshot_download(
            repo_id="Naut1507/PhoBert_Vi_ASC",
            local_dir="asc_phobert/asc_phobert/best_model",
            local_dir_use_symlinks=False,
        )
    _st.rerun()

_ensure_models_downloaded()

# ── absa package: business logic đã tách module ──────────────────────────────
from absa import (
    BASE_DIR, CACHE_DIR, HTML_TEMPLATE, COMP_DIR,
    load_models, phan_tich_batch, phan_tich_ai_that,
    ASPECT_CATEGORIES, is_valid_ASPECT_CATEGORIES,
    preprocess_text, file_md5, ensure_dirs,
    build_json_for_html, inject_html_data,
)
from absa.inference import warmup as _warmup_inference

# ── Streamlit config ─────────────────────────────────────────────────────────
st.set_page_config(page_title="Hệ thống phân tích cảm xúc", layout="wide")
ensure_dirs()

if st.query_params.get("reset") == "true":
    st.session_state.analyzed_df = None
    st.query_params.clear()
    time.sleep(0.1)
    st.rerun()


# ── Load model 1 lần cho cả process (Streamlit cache_resource) ───────────────
@st.cache_resource(show_spinner="Đang nạp mô hình PhoBERT...")
def _get_models():
    """
    Nạp model ATE + ASC vào GPU (nếu có) đúng 1 lần trong đời sống process.
    Nếu thất bại (thiếu file weight/tokenizer) → hiện thông báo chẩn đoán.
    """
    try:
        return load_models()
    except FileNotFoundError as e:
        from absa.models import ATE_WEIGHT_ROOT, ASC_WEIGHT_ROOT, dir_report
        st.error(f"Lỗi khi load model: {e}")
        st.info(
            "Nội dung 2 thư mục weight (để đối chiếu):\n\n"
            "ate_phobert:\n" + dir_report(ATE_WEIGHT_ROOT) + "\n\n"
            "asc_phobert:\n" + dir_report(ASC_WEIGHT_ROOT) + "\n\n"
            "Cần: 1 thư mục có config.json + model.safetensors (trọng số) và "
            "1 thư mục có vocab.txt + bpe.codes (tokenizer). Hai thứ này có thể "
            "nằm khác thư mục cũng được."
        )
        st.stop()

_models = _get_models()
_warmup_inference(_models)   # inject bundle vào absa.inference cho batch calls
# ==========================================
# KHU VỰC 3 & 4: GIAO DIỆN TƯƠNG TÁC VÀ RENDER
# Lưu thông tin file đã tải vào session state (nếu có)
if 'upload_history' not in st.session_state:
    st.session_state.upload_history = []
    

@st.cache_resource
def clear_cache_on_startup():
    # Chỉ chạy đúng 1 lần khi server Streamlit vừa khởi động (chạy lại lệnh streamlit)
    if os.path.exists(CACHE_DIR):
        try:
            shutil.rmtree(CACHE_DIR)
        except:
            pass
    return True

clear_cache_on_startup()

if 'analyzed_df' not in st.session_state:
    st.session_state.analyzed_df = None
    # Khôi phục nếu user chỉ reload (F5) trang mà không chạy lại lệnh streamlit
    csv_path  = os.path.join(CACHE_DIR, "last_analyzed.csv")
    hist_path = os.path.join(CACHE_DIR, "last_analyzed_history.json")
    if os.path.exists(csv_path):
        try:
            cached_df = pd.read_csv(csv_path)
            # ── CACHE VERSION CHECK ──────────────────────────────────────────
            # Cache hợp lệ chỉ khi cột 'Khía cạnh (Aspect)' chứa TÊN DANH MỤC
            # sạch (VD "Pin & Sạc") — sinh bởi normalize_aspect(). Nếu là aspect
            # thô cũ ("pin", "màn hình", "bin"…) → cache stale, xoá và phân
            # tích lại.
            if is_valid_category(cached_df.get('Khía cạnh (Aspect)',
                                                pd.Series([], dtype=str)).dropna().unique()):
                st.session_state.analyzed_df = cached_df
                if os.path.exists(hist_path):
                    with open(hist_path, "r", encoding="utf-8") as f:
                        st.session_state.upload_history = json.load(f)
            else:
                # Cache format cũ — xoá để tránh nạp nhầm
                try:
                    os.remove(csv_path)
                    if os.path.exists(hist_path):
                        os.remove(hist_path)
                except OSError:
                    pass
        except Exception:
            pass
if st.session_state.analyzed_df is None:
    # Thiết lập giao diện hiện đại, chuyên nghiệp đồng bộ với CSS của Dashboard chính
    st.markdown("""
        <style>
            /* Ẩn các thành phần mặc định của Streamlit */
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stHeader"] { background: transparent !important; }
            footer { display: none !important; }
            
            /* Cấu hình màu nền chính và font chữ */
            body, [data-testid="stAppViewContainer"] {
                background-color: #F4F2EE !important;
                font-family: 'DM Sans', sans-serif !important;
            }
            
            /* Điều chỉnh khoảng cách block container */
            .block-container { 
                max-width: 1100px !important; 
                padding-top: 6vh !important; 
                padding-bottom: 6vh !important; 
            }
            
            /* Style cho cột bên trái: Panel giới thiệu thông tin */
            .info-panel {
                background-color: #2f91f2;
                color: #ffffff;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 12px 30px rgba(97, 89, 183, 0.15);
                height: 100%;
                min-height: 550px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            
            .logo-area {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 25px;
            }
            
            .logo-icon {
                font-size: 24px;
            }
            
            .logo-title {
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 1px;
                color: rgba(255, 255, 255, 0.85);
            }
            
            .info-title {
                font-size: 2.2rem;
                font-weight: 700;
                line-height: 1.25;
                margin-bottom: 12px;
                letter-spacing: -0.5px;
                color: #ffffff;
            }
            
            .info-subtitle {
                font-size: 0.95rem;
                opacity: 0.85;
                margin-bottom: 35px;
                line-height: 1.5;
            }
            
            .feature-item {
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
                align-items: flex-start;
            }
            
            .feature-icon {
                width: 38px;
                height: 38px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                flex-shrink: 0;
            }
            
            .feature-text h4 {
                font-size: 0.95rem;
                font-weight: 600;
                margin-bottom: 4px;
                color: #ffffff;
            }
            
            .feature-text p {
                font-size: 0.85rem;
                opacity: 0.8;
                line-height: 1.4;
                margin: 0;
            }
            
            .tech-badges {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-top: 25px;
                padding-top: 20px;
                border-top: 1px solid rgba(255, 255, 255, 0.12);
            }
            
            .tech-badge {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 0.72rem;
                font-weight: 500;
                color: #ffffff;
            }

            /* Style cho cột bên phải: Card cấu hình tải tệp */
            div[data-testid="column"]:nth-of-type(2) {
                background: #ffffff !important;
                border: 1px solid rgba(0, 0, 0, 0.05) !important;
                border-radius: 20px !important;
                padding: 40px !important;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.03) !important;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                min-height: 550px;
            }
            
            .upload-card-header {
                margin-bottom: 25px;
            }
            
            .upload-card-title {
                font-size: 1.5rem;
                font-weight: 700;
                color: #1A1816;
                margin-bottom: 6px;
                letter-spacing: -0.3px;
            }
            
            .upload-card-sub {
                font-size: 0.88rem;
                color: #5A5650;
                line-height: 1.4;
            }

            /* Tùy chỉnh vùng kéo thả file */
            div[data-testid="stFileUploader"] {
                padding: 0 !important;
                margin-bottom: 15px;
            }
            
            div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
                border: 2px dashed #6159b7 !important;
                background-color: #fcfbfe !important;
                border-radius: 12px !important;
                padding: 24px !important;
                transition: all 0.25s ease !important;
            }
            
            div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover {
                background-color: #f6f5fc !important;
                border-color: #2f91f2 !important;
            }
            
            div[data-testid="stFileUploader"] label[data-testid="stWidgetLabel"] {
                display: none !important;
            }

            /* Biểu tượng tải lên có hiệu ứng di chuột nhẹ */
            div[data-testid="stFileUploader"] svg {
                color: #6159b7 !important;
                transform: scale(1.1);
                transition: transform 0.2s ease;
            }
            div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]:hover svg {
                transform: scale(1.2) translateY(-2px);
            }

            /* Kiểu dáng cho các Dropdown chọn cột */
            div[data-testid="stSelectbox"] {
                margin-bottom: 15px !important;
            }

            div[data-testid="stSelectbox"] label[data-testid="stWidgetLabel"] p {
                color: #5A5650 !important;
                font-weight: 600 !important;
                font-size: 0.85rem !important;
                margin-bottom: 6px !important;
            }
            
            /* ── Selectbox: giữ TRẮNG-ĐEN dù trình duyệt để dark mode ─────── */
            /* Container ngoài của baseweb select */
            div[data-testid="stSelectbox"] div[data-baseweb="select"],
            div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
                border-radius: 10px !important;
                background-color: #ffffff !important;
                color: #1e293b !important;
                border: 1px solid #e2e8f0 !important;
            }
            /* Text hiển thị giá trị đang chọn */
            div[data-testid="stSelectbox"] div[data-baseweb="select"] div,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] input,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
                color: #1e293b !important;
                background-color: transparent !important;
            }
            /* Placeholder khi chưa chọn */
            div[data-testid="stSelectbox"] div[data-baseweb="select"] [class*="placeholder"] {
                color: #64748b !important;
            }
            /* Popover / danh sách bung ra khi click */
            div[data-baseweb="popover"],
            div[data-baseweb="popover"] div,
            ul[role="listbox"],
            ul[role="listbox"] li,
            li[role="option"] {
                background-color: #ffffff !important;
                color: #1e293b !important;
            }
            li[role="option"]:hover,
            li[role="option"][aria-selected="true"] {
                background-color: #f1f5f9 !important;
                color: #1e293b !important;
            }
            /* Text input (nếu có ở các tab khác) — cùng phong cách */
            div[data-testid="stTextInput"] input,
            div[data-testid="stTextArea"] textarea {
                background-color: #ffffff !important;
                color: #1e293b !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 10px !important;
            }
            
            /* Tùy chỉnh nút Phân tích */
            div.stButton button[kind="primary"] {
                background-color: #6159b7 !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                border: none !important;
                border-radius: 10px !important;
                padding: 12px 24px !important;
                width: 100% !important;
                box-shadow: 0 6px 15px rgba(97, 89, 183, 0.2) !important;
                transition: all 0.2s ease !important;
                margin-top: 10px;
            }
            
            div.stButton button[kind="primary"]:hover {
                transform: translateY(-1px) !important;
                box-shadow: 0 10px 22px rgba(97, 89, 183, 0.3) !important;
                background-color: #524ab7 !important;
            }

            /* Styling cho thông báo của Streamlit */
            div[data-testid="stAlert"] {
                background-color: #ecfdf5 !important;
                border: 1px solid #a7f3d0 !important;
                border-radius: 10px !important;
                padding: 10px 14px !important;
                margin-bottom: 15px !important;
            }
            div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
                color: #065f46 !important;
                font-weight: 500 !important;
                font-size: 0.85rem !important;
                margin: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.1, 1.0], gap="large")
    
    with col1:
        st.markdown("""<div class="info-panel">
<div>
<div class="logo-area">
<div class="logo-icon">📊</div>
<span class="logo-title">ABSA ANALYZER</span>
</div>
<div class="info-title">Phân tích AI & Dashboard</div>
<div class="info-subtitle">Hệ thống phân tích cảm xúc đa khía cạnh (Aspect-Based Sentiment Analysis) tự động trích xuất ý kiến khách hàng và trực quan hóa dữ liệu trực quan.</div>

<div class="feature-item">
<div class="feature-icon" style="background-color: rgba(16, 185, 129, 0.2); color: #10B981; font-weight: bold; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.15);">🔍</div>
<div class="feature-text">
<h4>Trích xuất khía cạnh (ATE)</h4>
<p>Tự động nhận diện các đối tượng/khía cạnh được nhắc đến trong văn bản (ví dụ: Màn hình, Bàn phím, Nhân viên, Giá cả...).</p>
</div>
</div>

<div class="feature-item">
<div class="feature-icon" style="background-color: rgba(239, 68, 68, 0.2); color: #EF4444; font-weight: bold; box-shadow: 0 4px 10px rgba(239, 68, 68, 0.15);">🎭</div>
<div class="feature-text">
<h4>Phân loại cảm xúc (ASC)</h4>
<p>Xác định chính xác sắc thái thái độ đối với từng khía cạnh cụ thể (Tích cực, Tiêu cực).</p>
</div>
</div>

<div class="feature-item">
<div class="feature-icon" style="background-color: rgba(47, 145, 242, 0.25); color: #e0f2fe; font-weight: bold; box-shadow: 0 4px 10px rgba(47, 145, 242, 0.15);">⚡</div>
<div class="feature-text">
<h4>Công nghệ Deep Learning</h4>
<p>Tích hợp mô hình ngôn ngữ lớn được huấn luyện và tinh chỉnh tối ưu cho tiếng Việt.</p>
</div>
</div>
</div>

</div>""", unsafe_allow_html=True)
        
    with col2:
        st.markdown("""<div class="upload-card-header">
<h3 class="upload-card-title">Tải lên dữ liệu</h3>
<p class="upload-card-sub">Chọn tệp tin dữ liệu đánh giá sản phẩm (.csv hoặc .xlsx) để bắt đầu quét mô hình AI.</p>
</div>""", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Kéo thả file .csv hoặc .xlsx", type=['csv', 'xlsx'])
        
        if uploaded_file is not None:
            import os
            import hashlib
            
            # Đảm bảo thư mục cache tồn tại
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR)
                
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
                
            original_len = len(df_upload)
            df_upload = df_upload.dropna(how='all').drop_duplicates()
                
            st.success(f"Đã tải lên {original_len} dòng. Còn {len(df_upload)} dòng hợp lệ.")
            
            text_column = st.selectbox("Cột chứa văn bản bình luận để quét AI:", options=df_upload.columns.tolist())
            prod_options = ["(Không có cột Sản phẩm)"] + df_upload.columns.tolist()
            product_column = st.selectbox("Cột tên Sản phẩm (Dùng để nhóm kết quả):", options=prod_options)
            date_options = ["(Không có cột Ngày tháng)"] + df_upload.columns.tolist()
            date_column = st.selectbox("Cột Ngày/Tháng (Dùng để vẽ xu hướng):", options=date_options)
            
            # TỰ ĐỘNG PHÁT HIỆN CACHE DỰA TRÊN FILE VÀ CỘT ĐÃ CHỌN
            file_bytes = uploaded_file.getvalue()
            hasher = hashlib.md5(file_bytes)
            hasher.update(text_column.encode('utf-8'))
            hasher.update(product_column.encode('utf-8'))
            hasher.update(date_column.encode('utf-8'))
            cache_hash = hasher.hexdigest()
            cache_path = os.path.join(CACHE_DIR, f"{cache_hash}.csv")
            
            is_cached = os.path.exists(cache_path)
            
            if is_cached:
                # TẢI NHANH TỪ CACHE - KHÔNG CẦN CHẠY AI LẠI
                cached_df = pd.read_csv(cache_path)
                st.session_state.upload_history.append({
                    "name": uploaded_file.name,
                    "date": time.strftime("%d/%m/%Y %H:%M"),
                    "rows": len(df_upload),
                    "hash": cache_hash,   # ← để nút "Xem chi tiết" biết file nào để load
                })
                # Lưu vào cache mặc định để reload tự động nhận diện
                cached_df.to_csv(os.path.join(CACHE_DIR, "last_analyzed.csv"), index=False, encoding='utf-8')
                with open(os.path.join(CACHE_DIR, "last_analyzed_history.json"), "w", encoding="utf-8") as f:
                    json.dump(st.session_state.upload_history, f, ensure_ascii=False)
                    
                st.session_state.analyzed_df = cached_df
                st.success("⚡ Phát hiện kết quả phân tích cũ trong bộ nhớ Cache! Đang khôi phục dữ liệu nhanh...")
                time.sleep(0.5)
                st.rerun()
            else:
                if st.button("Chạy Phân tích", use_container_width=True, type="primary"):
                    with st.spinner("AI đang quét qua từng dòng trong dữ liệu..."):
                        # ── Chuẩn bị inputs cho batch inference ──────────────
                        text_col_name = text_column
                        prod_col_name = product_column if product_column != "(Không có cột Sản phẩm)" else None
                        date_col_name = date_column    if date_column    != "(Không có cột Ngày tháng)" else None

                        rows_meta = []   # song song với texts_clean: (prod, orig_text, date)
                        texts_clean = []
                        for _, row in df_upload.iterrows():
                            raw = row[text_col_name]
                            raw_str = str(raw) if raw is not None else ""
                            if not raw_str or raw_str.lower() == 'nan':
                                cleaned = ""
                            else:
                                cleaned = preprocess_text(raw_str)
                            texts_clean.append(cleaned)
                            rows_meta.append((
                                str(row[prod_col_name]) if prod_col_name else "Sản phẩm chung",
                                raw_str,
                                str(row[date_col_name]) if date_col_name else "",
                            ))

                        # ── BATCH INFERENCE (thay vòng lặp 1-1) ──────────────
                        # Trên RTX 5060 Ti 16GB: batch 32-64 tối ưu. Với PhoBERT-base
                        # + seq_len 128, mỗi batch dùng ~200-400 MB VRAM peak.
                        total_rows = len(texts_clean)
                        progress_bar = st.progress(0.0, text=f"0 / {total_rows} câu")

                        def _pcb(done, total):
                            progress_bar.progress(min(done/total, 1.0), text=f"{done} / {total} câu")

                        # Chỉ phân tích các câu không rỗng để không lãng phí batch slot
                        idx_nonempty = [i for i, t in enumerate(texts_clean) if t]
                        batch_texts  = [texts_clean[i] for i in idx_nonempty]
                        batch_out    = phan_tich_batch(batch_texts, batch_size=32, progress_cb=_pcb)

                        # ── Flatten về DataFrame rows ────────────────────────
                        all_results = []
                        for local_i, orig_i in enumerate(idx_nonempty):
                            prod_val, orig_text, date_val = rows_meta[orig_i]
                            for extract in batch_out[local_i]:
                                all_results.append({
                                    "Sản phẩm": prod_val,
                                    "Văn bản": orig_text,
                                    "Khía cạnh (Aspect)": extract["Khía cạnh (Aspect)"],
                                    "Aspect gốc":         extract.get("Aspect gốc", extract["Khía cạnh (Aspect)"]),
                                    "Cảm xúc (Polarity)": extract["Cảm xúc (Polarity)"],
                                    "Thời gian": date_val,
                                })

                        progress_bar.empty()

                        if all_results:
                            analyzed_df = pd.DataFrame(all_results)
                            # Lưu vào cả Cache file riêng và Cache mặc định
                            analyzed_df.to_csv(cache_path, index=False, encoding='utf-8')
                            analyzed_df.to_csv(os.path.join(CACHE_DIR, "last_analyzed.csv"), index=False, encoding='utf-8')
                            
                            st.session_state.upload_history.append({
                                "name": uploaded_file.name,
                                "date": time.strftime("%d/%m/%Y %H:%M"),
                                "rows": len(df_upload),
                                "hash": cache_hash,   # ← để nút "Xem chi tiết" biết file nào để load
                            })
                            with open(os.path.join(CACHE_DIR, "last_analyzed_history.json"), "w", encoding="utf-8") as f:
                                json.dump(st.session_state.upload_history, f, ensure_ascii=False)
                                
                            st.session_state.analyzed_df = analyzed_df
                            st.success("✅ Trích xuất bằng AI hoàn tất! Đang chuyển hướng...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("⚠️ AI không tìm thấy khía cạnh nào trong tập dữ liệu.")
else:
    # Ẩn HOÀN TOÀN các thành phần mặc định của Streamlit để hiển thị chuẩn 100% giao diện HTML
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
            [data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
            .block-container { 
                padding-top: 0rem !important; 
                padding-bottom: 0rem !important; 
                padding-left: 0rem !important; 
                padding-right: 0rem !important; 
                max-width: 100% !important; 
            }
            iframe { border: none !important; }
        </style>
    """, unsafe_allow_html=True)
    
    json_data = build_json_for_html(st.session_state.analyzed_df)

    # ── XỬ LÝ LIVE INFERENCE BẰNG NATIVE COMPONENT ──────────────────────────
    infer_text = st.session_state.get("infer_text", "")
    infer_result = st.session_state.get("infer_result", None)

    # Cập nhật lịch sử file và kết quả inference vào json_data
    parsed_json = json.loads(json_data)
    parsed_json["uploadHistory"] = st.session_state.upload_history
    parsed_json["inferResult"] = infer_result   # None hoặc list kết quả
    parsed_json["inferText"]   = infer_text      # câu vừa được phân tích
    # Nếu vừa click "Xem chi tiết" ở lịch sử → yêu cầu dashboard mở tab 2 sau render.
    # Xoá flag ngay sau khi truyền để lần rerun tiếp theo không tự chuyển tab.
    if st.session_state.get("pending_tab"):
        parsed_json["openTab"] = st.session_state.pending_tab
        del st.session_state["pending_tab"]
    json_data = json.dumps(parsed_json, ensure_ascii=False)

    # ── Đường dẫn HTML: neo theo BASE_DIR ─────────────────────────────────────
    # Template ưu tiên đọc từ THƯ MỤC GỐC (BASE_DIR/index.html); nếu không có
    # thì fallback về BASE_DIR/dashboard_component/index.html (bố cục cũ).
    # File render sau khi tiêm được ghi ra BASE_DIR/dashboard_component/index.html
    # để Streamlit component nạp.
    # Đường dẫn HTML template ưu tiên BASE_DIR/index.html (thư mục gốc project),
    # fallback về COMP_DIR/index.html cho bố cục cũ. File render output luôn ghi
    # vào COMP_DIR/index.html để Streamlit component nạp.
    root_template = HTML_TEMPLATE
    comp_dir      = COMP_DIR
    comp_template = os.path.join(comp_dir, "index.html")

    if os.path.exists(root_template):
        html_file_path = root_template
    elif os.path.exists(comp_template):
        html_file_path = comp_template
    else:
        st.error(
            "Không tìm thấy template dashboard.\n\n"
            f"Cần 1 trong 2 file sau tồn tại:\n"
            f"  • {root_template}\n"
            f"  • {comp_template}"
        )
        st.stop()

    final_html_content = inject_html_data(html_file_path, json_data)

    # Khởi tạo Bidirectional Component
    if not os.path.exists(comp_dir):
        os.makedirs(comp_dir)
        
    boilerplate = """
    <!-- DASH_INJECT_START -->
    <script>
    function sendToStreamlit(value) {
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setComponentValue",
            value: value,
        }, "*");
    }
    
    function updateStreamlitHeight() {
        const bodyHeight = document.body.scrollHeight;
        const htmlHeight = document.documentElement.scrollHeight;
        const realHeight = Math.max(bodyHeight, htmlHeight) + 50;
        
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:setFrameHeight",
            height: realHeight,
        }, "*");
    }

    window.addEventListener("load", function() {
        window.parent.postMessage({
            isStreamlitMessage: true,
            type: "streamlit:componentReady",
            apiVersion: 1,
        }, "*");
        
        updateStreamlitHeight();
        
        const resizeObserver = new ResizeObserver(() => {
            updateStreamlitHeight();
        });
        resizeObserver.observe(document.body);
    });
    </script>
    <!-- DASH_INJECT_END -->
    """
    final_html_content = final_html_content.replace("</body>", boilerplate + "</body>")
    
    with open(comp_template, "w", encoding="utf-8") as f:
        f.write(final_html_content)
        
    html_mtime = int(os.path.getmtime(html_file_path))
    dashboard_comp = components.declare_component(f"dashboard_comp_{html_mtime}", path=comp_dir)
    
    returned_value = dashboard_comp(default=None, key=f"dashboard_{st.session_state.get('run_count', 0)}")
    
    if returned_value:
        if returned_value == "RESET_UPLOAD":
            st.session_state.analyzed_df = None
            if os.path.exists(os.path.join(CACHE_DIR, "last_analyzed.csv")):
                os.remove(os.path.join(CACHE_DIR, "last_analyzed.csv"))
            st.session_state.run_count = st.session_state.get('run_count', 0) + 1
            st.rerun()
        elif isinstance(returned_value, str) and returned_value.startswith("LOAD_HISTORY:"):
            # ── User click "Xem chi tiết" ở tab Hệ thống ────────────────────
            requested_hash = returned_value.split(":", 1)[1].strip()
            # Chấp nhận chỉ ký tự an toàn: hex md5 hoặc alphanumeric
            if requested_hash and all(c.isalnum() or c in "_-" for c in requested_hash):
                target_csv = os.path.join(CACHE_DIR, f"{requested_hash}.csv")
                if os.path.exists(target_csv):
                    try:
                        loaded_df = pd.read_csv(target_csv)
                        # Validate cùng schema với DataFrame hiện tại
                        if is_valid_category(loaded_df.get('Khía cạnh (Aspect)',
                                                          pd.Series([], dtype=str)).dropna().unique()):
                            st.session_state.analyzed_df = loaded_df
                            # Đồng bộ vào cache mặc định để F5 tự nạp lại đúng file này
                            loaded_df.to_csv(os.path.join(CACHE_DIR, "last_analyzed.csv"),
                                             index=False, encoding='utf-8')
                            # Đánh dấu tab cần mở sau rerun
                            st.session_state.pending_tab = 2
                            st.session_state.run_count = st.session_state.get('run_count', 0) + 1
                            st.rerun()
                        else:
                            st.warning("File lịch sử có định dạng cũ, không tương thích. "
                                       "Hãy phân tích lại file này để cập nhật.")
                    except Exception as e:
                        st.warning(f"Không nạp được file lịch sử: {e}")
                else:
                    st.warning("File kết quả cho lịch sử này không còn trên đĩa "
                               "(có thể cache đã bị xoá). Hãy upload lại file gốc để phân tích.")
        elif returned_value != infer_text:
            st.session_state.infer_text = returned_value
            try:
                st.session_state.infer_result = phan_tich_ai_that(returned_value)
            except Exception as e:
                st.session_state.infer_result = [{"error": str(e)}]
            st.session_state.run_count = st.session_state.get('run_count', 0) + 1
            st.rerun()