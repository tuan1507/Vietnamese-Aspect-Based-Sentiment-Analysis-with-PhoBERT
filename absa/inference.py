import torch
from underthesea import word_tokenize

from .models import ATE_MAX_LEN, ASC_MAX_LEN, ATE_ID2LABEL, ASC_ID2LABEL
from .aspect_category import normalize_aspect

_STATE = {
    "ate_tokenizer": None, "ate_model": None,
    "asc_tokenizer": None, "asc_model": None,
    "device": None, "use_amp": False,
    "ate_is_fast": False, "asc_is_fast": False,
}


def warmup(model_bundle: dict) -> None:
    _STATE.update({k: model_bundle[k] for k in _STATE.keys()})


def _get_word_ids_slow(tokenizer, words, max_length):
    word_ids = [None]
    for idx, word in enumerate(words):
        subs = tokenizer.tokenize(word) or [tokenizer.unk_token]
        word_ids.extend([idx] * len(subs))
    word_ids.append(None)
    if len(word_ids) > max_length:
        word_ids = word_ids[:max_length - 1] + [None]
    return word_ids


def _group_aspects(words, labels):
    """
    Ghép B-ASP + I-ASP thành các cụm aspect.
    Trả về list (aspect_display, aspect_seg):
      - aspect_seg    : giữ nguyên _ (dạng PhoBERT hiểu, dùng cho ASC)
      - aspect_display: đổi _ → space (hiển thị/normalize)
    """
    aspects, cur = [], []
    for tok, lbl in zip(words, labels):
        if lbl == "B-ASP":
            if cur:
                aspects.append(cur); cur = []
            cur = [tok]
        elif lbl == "I-ASP" and cur:
            cur.append(tok)
        else:
            if cur:
                aspects.append(cur); cur = []
    if cur:
        aspects.append(cur)

    out = []
    for span in aspects:
        aspect_seg     = " ".join(span)
        aspect_display = aspect_seg.replace("_", " ").strip()
        if len(aspect_display) >= 2:
            out.append((aspect_display, aspect_seg))
    return out


# BƯỚC 1: ATE trên 1 BATCH câu 
def _predict_aspects_batch(texts):
    tokenizer = _STATE["ate_tokenizer"]
    model     = _STATE["ate_model"]
    device    = _STATE["device"]
    use_amp   = _STATE["use_amp"]
    is_fast   = _STATE["ate_is_fast"]

    if not texts or tokenizer is None or model is None:
        return [[] for _ in texts], []

    # Word-segment tất cả câu 1 lần (underthesea CPU-bound)
    sentences_seg = [word_tokenize(str(t), format="text") for t in texts]
    words_list    = [s.strip().split() for s in sentences_seg]

    # Chỉ tokenize các câu không rỗng, giữ mapping về index gốc
    non_empty = [i for i, w in enumerate(words_list) if w]
    if not non_empty:
        return [[] for _ in texts], sentences_seg

    batch_words = [words_list[i] for i in non_empty]
    enc = tokenizer(
        batch_words,
        is_split_into_words=True,
        return_tensors="pt",
        truncation=True,
        max_length=ATE_MAX_LEN,
        padding=True,
    )

    # word_ids per sample
    if is_fast:
        all_word_ids = [enc.word_ids(k) for k in range(len(batch_words))]
    else:
        all_word_ids = [_get_word_ids_slow(tokenizer, w, ATE_MAX_LEN)
                        for w in batch_words]

    enc = {k: v.to(device) for k, v in enc.items()}

    with torch.inference_mode():
        if use_amp:
            with torch.autocast(device_type=device.type, dtype=torch.float16):
                logits = model(**enc).logits
        else:
            logits = model(**enc).logits
        preds = logits.argmax(-1).cpu().numpy()   # shape (B, seq_len)

    results = [[] for _ in texts]
    for local_i, orig_i in enumerate(non_empty):
        sample_preds = preds[local_i]
        word_ids     = all_word_ids[local_i]
        words        = batch_words[local_i]

        # First subword per word → nhãn của word đó
        final_labels, seen = [], set()
        for pid, wid in zip(sample_preds, word_ids):
            if wid is None or wid in seen:
                continue
            final_labels.append(ATE_ID2LABEL[int(pid)])
            seen.add(wid)

        n = min(len(words), len(final_labels))
        results[orig_i] = _group_aspects(words[:n], final_labels[:n])

    return results, sentences_seg


# BƯỚC 2: ASC trên tất cả (câu, aspect) của batch, đã flatten
def _predict_sentiments_batch(pairs):
    """
    pairs: list of (sentence_seg, term_seg).
    Trả về list nhãn ("positive"/"negative") cùng length.
    """
    if not pairs:
        return []
    tokenizer = _STATE["asc_tokenizer"]
    model     = _STATE["asc_model"]
    device    = _STATE["device"]
    use_amp   = _STATE["use_amp"]

    sentences = [p[0] for p in pairs]
    terms     = [p[1] for p in pairs]
    enc = tokenizer(
        sentences, terms,
        return_tensors="pt",
        truncation=True,
        max_length=ASC_MAX_LEN,
        padding=True,
    )
    enc = {k: v.to(device) for k, v in enc.items()}

    with torch.inference_mode():
        if use_amp:
            with torch.autocast(device_type=device.type, dtype=torch.float16):
                logits = model(**enc).logits
        else:
            logits = model(**enc).logits
        preds = logits.argmax(-1).cpu().numpy()

    return [ASC_ID2LABEL[int(p)] for p in preds]


#  API chính: batch inference
def phan_tich_batch(texts, batch_size: int = 32, progress_cb=None):
    all_results = [[] for _ in texts]
    total = len(texts)
    if total == 0:
        return all_results

    for start in range(0, total, batch_size):
        batch = texts[start:start + batch_size]

        # 1) ATE batch
        aspects_per_text, sentences_seg = _predict_aspects_batch(batch)

        # 2) Chuẩn hoá + flatten cặp (câu, aspect) cho ASC
        pairs, idx_map = [], []
        for local_i, aspects in enumerate(aspects_per_text):
            orig_i   = start + local_i
            sent_seg = sentences_seg[local_i] if local_i < len(sentences_seg) else ""
            for aspect_display, aspect_seg in aspects:
                category = normalize_aspect(aspect_display)
                if category is None:
                    continue   # rác — drop
                pairs.append((sent_seg, aspect_seg))
                idx_map.append((orig_i, category, aspect_display))

        # 3) ASC batch (1 forward duy nhất cho cả batch)
        labels = _predict_sentiments_batch(pairs)

        # 4) Gán kết quả về từng câu
        for (orig_i, cat, disp), label in zip(idx_map, labels):
            if label == "positive":
                polarity_vn = "🟢 Tích cực"
            elif label == "negative":
                polarity_vn = "🔴 Tiêu cực"
            else:
                polarity_vn = "⚪ Trung tính"
            all_results[orig_i].append({
                "Khía cạnh (Aspect)": cat,
                "Aspect gốc":         disp,
                "Cảm xúc (Polarity)": polarity_vn,
            })

        if progress_cb is not None:
            progress_cb(min(start + batch_size, total), total)

    return all_results


def phan_tich_ai_that(text):
    if not isinstance(text, str) or not text.strip():
        return []
    if _STATE["ate_model"] is None:
        return []
    return phan_tich_batch([text], batch_size=1)[0]