import os
import warnings
import logging
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
)
from .utils import BASE_DIR

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
try:
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()
except Exception:
    pass
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.tokenization_utils_base").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning,  module="transformers")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

# ── Hyperparams & label maps (khớp CHÍNH XÁC với notebook train) ─────────────
ATE_MAX_LEN  = 128
ASC_MAX_LEN  = 128
ATE_ID2LABEL = {0: "O", 1: "B-ASP", 2: "I-ASP"}
ASC_ID2LABEL = {0: "negative", 1: "positive"}

ATE_WEIGHT_ROOT = os.path.join(BASE_DIR, "ate_phobert")
ASC_WEIGHT_ROOT = os.path.join(BASE_DIR, "asc_phobert")


def _has_weights(d: str) -> bool:
    """Thư mục chứa TRỌNG SỐ model: config.json + model.safetensors/pytorch_model.bin."""
    return (os.path.isdir(d)
            and os.path.exists(os.path.join(d, "config.json"))
            and any(os.path.exists(os.path.join(d, w))
                    for w in ("model.safetensors", "pytorch_model.bin")))


def _has_tokenizer(d: str) -> bool:
    """Thư mục chứa TOKENIZER: (vocab.txt + bpe.codes) HOẶC tokenizer.json (fast)."""
    if not os.path.isdir(d):
        return False
    slow = (os.path.exists(os.path.join(d, "vocab.txt"))
            and os.path.exists(os.path.join(d, "bpe.codes")))
    fast = os.path.exists(os.path.join(d, "tokenizer.json"))
    return slow or fast


def _find_dir(root: str, ok, what: str) -> str:
    """Dò thư mục con của root thoả ok(). Ưu tiên best_model → checkpoint-* → nông nhất."""
    if not os.path.isdir(root):
        raise FileNotFoundError(f"Không tìm thấy thư mục: {root}")
    if ok(root):
        return root
    best, others = [], []
    for cur, dirs, _ in os.walk(root):
        for d in dirs:
            full = os.path.join(cur, d)
            if not ok(full):
                continue
            (best if d == "best_model" else others).append(full)
    if best:
        return min(best, key=lambda p: p.count(os.sep))
    if others:
        def key(p):
            b = os.path.basename(p)
            step = int(b.split("-")[-1]) if (b.startswith("checkpoint-")
                                             and b.split("-")[-1].isdigit()) else -1
            return (step, -p.count(os.sep))
        return max(others, key=key)
    raise FileNotFoundError(f"Không tìm thấy {what} trong: {root}")


def dir_report(root: str) -> str:
    """Liệt kê nhanh nội dung thư mục weight — để chẩn đoán khi lỗi."""
    if not os.path.isdir(root):
        return f"  {root}  →  KHÔNG TỒN TẠI"
    lines = [f"  {root}"]
    for cur, dirs, files in os.walk(root):
        rel = os.path.relpath(cur, root)
        prefix = "    " if rel == "." else f"    {rel}/"
        keys = sorted(f for f in files if f in (
            "config.json", "model.safetensors", "pytorch_model.bin",
            "vocab.txt", "bpe.codes", "tokenizer.json",
            "tokenizer_config.json", "special_tokens_map.json"))
        lines.append(f"{prefix}  [{', '.join(keys) if keys else 'không có file model/tokenizer'}]")
    return "\n".join(lines)


def load_models():
    """
    Load 2 mô hình PhoBERT (ATE + ASC) lên RAM/GPU.

    Returns:
        dict với các khoá:
          ate_tokenizer, ate_model, asc_tokenizer, asc_model,
          device, use_amp, ate_is_fast, asc_is_fast

    Raises:
        FileNotFoundError nếu thư mục weight/tokenizer thiếu.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = (device.type == "cuda")   # bật autocast FP16 khi có CUDA

    ate_w = _find_dir(ATE_WEIGHT_ROOT, _has_weights,
                      "trọng số ATE (config.json + model.safetensors)")
    ate_t = _find_dir(ATE_WEIGHT_ROOT, _has_tokenizer,
                      "tokenizer ATE (vocab.txt+bpe.codes hoặc tokenizer.json)")
    asc_w = _find_dir(ASC_WEIGHT_ROOT, _has_weights,
                      "trọng số ASC (config.json + model.safetensors)")
    asc_t = _find_dir(ASC_WEIGHT_ROOT, _has_tokenizer,
                      "tokenizer ASC (vocab.txt+bpe.codes hoặc tokenizer.json)")

    # Ưu tiên fast tokenizer (Rust backend) — nhanh gấp 5-10x
    ate_tokenizer = AutoTokenizer.from_pretrained(ate_t, use_fast=True) \
                    if os.path.exists(os.path.join(ate_t, "tokenizer.json")) \
                    else AutoTokenizer.from_pretrained(ate_t)
    asc_tokenizer = AutoTokenizer.from_pretrained(asc_t, use_fast=True) \
                    if os.path.exists(os.path.join(asc_t, "tokenizer.json")) \
                    else AutoTokenizer.from_pretrained(asc_t)

    ate_model = AutoModelForTokenClassification.from_pretrained(ate_w).to(device).eval()
    asc_model = AutoModelForSequenceClassification.from_pretrained(asc_w).to(device).eval()

    return {
        "ate_tokenizer": ate_tokenizer,
        "ate_model":     ate_model,
        "asc_tokenizer": asc_tokenizer,
        "asc_model":     asc_model,
        "device":        device,
        "use_amp":       use_amp,
        "ate_is_fast":   bool(getattr(ate_tokenizer, "is_fast", False)),
        "asc_is_fast":   bool(getattr(asc_tokenizer, "is_fast", False)),
        "ate_dir":       ate_w,
        "asc_dir":       asc_w,
    }