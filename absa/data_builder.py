import json
import math
import os
import re
import pandas as pd
import streamlit as st

@st.cache_data(show_spinner=False, ttl=3600, max_entries=8)
def build_json_cached(df_results: pd.DataFrame) -> str:
    """Wrapper cache-friendly cho build_json_for_html."""
    return build_json_for_html(df_results)


def build_json_for_html(df_results):
    """
    Tạo dữ liệu JSON cho giao diện HTML mới.
    """
    total_aspects = len(df_results)
    pos_count = int((df_results['Cảm xúc (Polarity)'] == '🟢 Tích cực').sum())
    neg_count = int((df_results['Cảm xúc (Polarity)'] == '🔴 Tiêu cực').sum())
    pos_rate = round(pos_count / total_aspects * 100) if total_aspects > 0 else 0
    neg_rate = round(neg_count / total_aspects * 100) if total_aspects > 0 else 0
    nps_score = pos_rate - neg_rate

    aspect_counts = df_results['Khía cạnh (Aspect)'].value_counts()
    top_aspect = aspect_counts.index[0] if len(aspect_counts) > 0 else "N/A"
    top_aspect_count = int(aspect_counts.iloc[0]) if len(aspect_counts) > 0 else 0
    
    aspect_list = []
    for aspect, count in aspect_counts.items():
        asp_df = df_results[df_results['Khía cạnh (Aspect)'] == aspect]
        asp_pos = int((asp_df['Cảm xúc (Polarity)'] == '🟢 Tích cực').sum())
        asp_neg = int((asp_df['Cảm xúc (Polarity)'] == '🔴 Tiêu cực').sum())
        aspect_list.append({
            "name": aspect,
            "total": int(count),
            "pos": asp_pos,
            "neg": asp_neg,
            "neg_rate": round(asp_neg / int(count) * 100) if int(count) > 0 else 0,
            "pos_rate": round(asp_pos / int(count) * 100) if int(count) > 0 else 0
        })
    for a in aspect_list:
        a["impact"] = round((a["pos"] - a["neg"]) / total_aspects * 100) if total_aspects > 0 else 0

    worst_aspects = sorted([a for a in aspect_list if a["total"] >= 1], key=lambda x: x["neg"], reverse=True)[:8]
    pos_drivers = sorted([a for a in aspect_list if a["impact"] > 0], key=lambda x: x["impact"], reverse=True)[:2]
    neg_drivers = sorted([a for a in aspect_list if a["impact"] < 0], key=lambda x: x["impact"])[:2]

    # Trend calculation
    import math
    import re
    
    def parse_days_ago(text):
        if not text or str(text).lower() == 'nan': return -1
        text = str(text).lower()
        match = re.search(r'(\d+)\s+(ngày|tuần|tháng|năm)', text)
        if match:
            val = int(match.group(1))
            unit = match.group(2)
            if unit == 'ngày': return val
            if unit == 'tuần': return val * 7
            if unit == 'tháng': return val * 30
            if unit == 'năm': return val * 365
        return -1

    trend_data = []
    has_date = 'Thời gian' in df_results.columns and not df_results['Thời gian'].eq('').all()
    if has_date:
        df_results['days_ago'] = df_results['Thời gian'].apply(parse_days_ago)
        valid_df = df_results[df_results['days_ago'] >= 0]
        if not valid_df.empty:
            buckets = [
                valid_df[valid_df['days_ago'] > 21],
                valid_df[(valid_df['days_ago'] > 14) & (valid_df['days_ago'] <= 21)],
                valid_df[(valid_df['days_ago'] > 7) & (valid_df['days_ago'] <= 14)],
                valid_df[(valid_df['days_ago'] >= 1) & (valid_df['days_ago'] <= 7)],
                valid_df[valid_df['days_ago'] == 0]
            ]
            for chunk in buckets:
                c_tot = len(chunk)
                if c_tot > 0:
                    c_pos = int((chunk['Cảm xúc (Polarity)'] == '🟢 Tích cực').sum())
                    c_neg = int((chunk['Cảm xúc (Polarity)'] == '🔴 Tiêu cực').sum())
                    trend_data.append({"pos": round(c_pos/c_tot*100), "neg": round(c_neg/c_tot*100)})
                else:
                    trend_data.append({"pos": 0, "neg": 0})
                    
    if len(trend_data) != 5:
        trend_data = []
        chunk_size = math.ceil(total_aspects / 5) if total_aspects > 0 else 1
        for i in range(5):
            chunk = df_results.iloc[i*chunk_size:(i+1)*chunk_size]
            c_tot = len(chunk)
            if c_tot > 0:
                c_pos = int((chunk['Cảm xúc (Polarity)'] == '🟢 Tích cực').sum())
                c_neg = int((chunk['Cảm xúc (Polarity)'] == '🔴 Tiêu cực').sum())
                trend_data.append({"pos": round(c_pos/c_tot*100), "neg": round(c_neg/c_tot*100)})
            else:
                trend_data.append({"pos": 0, "neg": 0})
            
    trend_points_pos = " ".join([f"{i*25},{100-td['pos']}" for i, td in enumerate(trend_data)])
    trend_points_neg = " ".join([f"{i*25},{100-td['neg']}" for i, td in enumerate(trend_data)])
    trend_poly_pos = f"0,100 {trend_points_pos} 100,100"

    product_list = []
    if 'Sản phẩm' not in df_results.columns:
        df_results['Sản phẩm'] = 'Sản phẩm chung'
        
    for prod_name, group in df_results.groupby('Sản phẩm'):
        if pd.isna(prod_name):
            prod_name = 'Sản phẩm chưa rõ'
        p_total = int(len(group))
        p_pos = int((group['Cảm xúc (Polarity)'] == '🟢 Tích cực').sum())
        p_neg = int((group['Cảm xúc (Polarity)'] == '🔴 Tiêu cực').sum())
        
        sample_reviews = []
        for _, row in group.head(10).iterrows():
            asp = str(row.get('Khía cạnh (Aspect)', ''))
            txt = str(row.get('Văn bản', '')).replace('"', "'")
            pol = "🟢 Tích cực" if row.get('Cảm xúc (Polarity)') == '🟢 Tích cực' else "🔴 Tiêu cực" 
            sample_reviews.append(f"{pol} | {asp}:\n  \"{txt}\"")
        tooltip_text = "\n\n".join(sample_reviews)
        if len(group) > 10:
            tooltip_text += f"\n\n... và {len(group) - 10} đánh giá khác"
        
        pos_ratio = p_pos / p_total if p_total > 0 else 0
        score = 1.0 + (pos_ratio * 4.0)
        score = round(score, 1)
        
        p_pos_rate = round(p_pos / p_total * 100) if p_total > 0 else 0
        product_list.append({
            "name": str(prod_name),
            "total": p_total,
            "pos": p_pos,
            "neg": p_neg,
            "pos_rate": p_pos_rate,
            "neg_rate": round(p_neg / p_total * 100) if p_total > 0 else 0,
            "score": score,
            "tooltip": tooltip_text
        })
    product_list.sort(key=lambda x: x["score"], reverse=True)
    best_products = sorted([p for p in product_list if p["total"] >= 1], key=lambda x: x["pos_rate"], reverse=True)[:3]

    top_10_aspects = aspect_counts.head(10).index.tolist()
    heatmap = []
    for prod_name, group in df_results.groupby('Sản phẩm'):
        if pd.isna(prod_name):
            prod_name = 'Sản phẩm chưa rõ'
        p_data = {"product": str(prod_name), "aspects": {}}
        for asp in top_10_aspects:
            asp_group = group[group['Khía cạnh (Aspect)'] == asp]
            a_total = len(asp_group)
            a_pos = int((asp_group['Cảm xúc (Polarity)'] == '🟢 Tích cực').sum())
            a_neg = int((asp_group['Cảm xúc (Polarity)'] == '🔴 Tiêu cực').sum())
            pos_pct = round((a_pos / a_total * 100)) if a_total > 0 else 0
            neg_pct = round((a_neg / a_total * 100)) if a_total > 0 else 0
            p_data["aspects"][asp] = {"pos_pct": pos_pct, "neg_pct": neg_pct}
        heatmap.append(p_data)

    feed = []
    if 'Văn bản' in df_results.columns:
        for text, group in df_results.groupby('Văn bản'):
            tags = []
            seen = set()   # dedupe theo (aspect, polarity) — 1 câu không hiện 2 tag "Pin & Sạc" trùng
            prod = str(group['Sản phẩm'].iloc[0]) if 'Sản phẩm' in group.columns else "Sản phẩm chung"
            for _, row in group.iterrows():
                pol = "pos" if row['Cảm xúc (Polarity)'] == '🟢 Tích cực' else "neg" if row['Cảm xúc (Polarity)'] == '🔴 Tiêu cực' else "neu"
                # Tag review card DÙNG TÊN DANH MỤC (đồng bộ với sidebar & charts).
                # Trước đây từng thử hiện Aspect gốc để "bảo toàn ngữ nghĩa" nhưng training
                # data hầu hết là aspect 1 từ (pin, sạc, loa…) nên span thô = từ trần,
                # không thêm ngữ nghĩa mà còn lộ typo (VD "bin") và duplicate ("pin • pin").
                asp = row['Khía cạnh (Aspect)']
                key = (asp, pol)
                if key in seen:
                    continue
                seen.add(key)
                tags.append({
                    "aspect": asp,
                    "polarity": pol
                })
            feed.append({
                "text": str(text),
                "product": prod,
                "tags": tags
            })
            
    data = {
        "metrics": {
            "total": total_aspects,
            "pos_rate": pos_rate,
            "neg_rate": neg_rate,
            "neu_rate": 100 - pos_rate - neg_rate,
            "nps": nps_score,
            "top_aspect": top_aspect,
            "top_aspect_count": top_aspect_count,
            "pos_count": pos_count,
            "neg_count": neg_count
        },
        "trend": {
            "pos_pts": trend_points_pos,
            "neg_pts": trend_points_neg,
            "pos_poly": trend_poly_pos
        },
        "drivers": {
            "pos": [{"name": d["name"], "rate": d["impact"]} for d in pos_drivers],
            "neg": [{"name": d["name"], "rate": abs(d["impact"])} for d in neg_drivers]
        },
        "products": product_list,
        "aspects": aspect_list,
        "worst_aspects": worst_aspects,
        "best_products": best_products,
        "heatmap": {
            "columns": top_10_aspects,
            "data": heatmap
        },
        "feed": feed
    }
    return json.dumps(data, ensure_ascii=False)

def inject_html_data(html_path, json_data_str):
    """
    Đọc template HTML, tiêm CSS + JS vào để render giao diện dashboard.

    - CSS đọc từ absa/static/dashboard.css → tiêm vào <head>
    - JS  đọc từ absa/static/dashboard.js  → tiêm vào <body>
    - Idempotent qua marker DASH_INJECT_START/END:
      dù chạy app bao nhiêu lần cũng không bị chồng const DATA.
    """
    _STATIC_CSS = os.path.join(os.path.dirname(__file__), "static", "css")
    _STATIC_JS  = os.path.join(os.path.dirname(__file__), "static", "js")

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    html_content = re.sub(
        r'\s*<!-- DASH_INJECT_START -->.*?<!-- DASH_INJECT_END -->\s*',
        '\n', html_content, flags=re.DOTALL)
    html_content = re.sub(
        r'\s*<script>(?:(?!</script>)[\s\S])*\bconst DATA\b(?:(?!</script>)[\s\S])*</script>\s*',
        '\n', html_content)
    html_content = re.sub(
        r'\s*<script>(?:(?!</script>)[\s\S])*streamlit:componentReady(?:(?!</script>)[\s\S])*</script>\s*',
        '\n', html_content)

    css_path = os.path.join(_STATIC_CSS, "dashboard.css")
    if os.path.exists(css_path):
        css_code = open(css_path, encoding="utf-8").read()
        css_block = f"\n<!-- DASH_INJECT_START -->\n<style>\n{css_code}\n</style>\n<!-- DASH_INJECT_END -->\n"
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", css_block + "</head>")

    js_template = open(os.path.join(_STATIC_JS, "dashboard.js"), encoding="utf-8").read()
    js_code     = js_template.replace("__JSON_DATA__", json_data_str)

    streamlit_bridge = """
    <script>
        // ── Giao tiếp với Streamlit: gửi giá trị về Python ──────────────
        // Hàm này được gọi từ dashboard.js mỗi khi user click
        // upload-zone (RESET_UPLOAD), Xem chi tiết (LOAD_HISTORY:hash),
        // hoặc gõ text inference.
        (function() {
            function waitForStreamlit(callback, maxTries = 20) {
                let tries = 0;
                const interval = setInterval(() => {
                    if (window.Streamlit) {
                        clearInterval(interval);
                        callback();
                    } else if (++tries >= maxTries) {
                        clearInterval(interval);
                        console.warn("Streamlit chưa sẵn sàng sau", maxTries, "lần thử");
                    }
                }, 100);
            }

            waitForStreamlit(() => {
                window.Streamlit.setComponentReady();
                window.sendToStreamlit = function(value) {
                    window.Streamlit.setComponentValue(value);
                };
            });
        })();
    </script>
    """

    injected_script = f"""
    <!-- DASH_INJECT_START -->
    <script>
{js_code}
    </script>
    {streamlit_bridge}
    <!-- DASH_INJECT_END -->
    """

    if "</body>" in html_content:
        return html_content.replace("</body>", injected_script + "\n</body>")
    return html_content + injected_script