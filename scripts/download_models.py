import sys
from pathlib import Path
from huggingface_hub import snapshot_download

# ── Repo trên HuggingFace Hub ────────────────────────────────────────────────
ATE_REPO = "Naut1507/PhoBert_Vi_ATE"
ASC_REPO = "Naut1507/PhoBert_Vi_ASC"

# ── Đường dẫn local (khớp với cấu trúc thư mục thực) ────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent   # thư mục project root
ATE_DIR  = BASE_DIR / "ate_phobert" / "phobert_ate_v3" / "best_model"
ASC_DIR  = BASE_DIR / "asc_phobert" / "asc_phobert" / "best_model"


def download(repo_id: str, local_dir: Path) -> None:
    # Bỏ qua nếu đã có model.safetensors (tránh tải lại)
    if (local_dir / "model.safetensors").exists():
        print(f"✅ {repo_id} đã có sẵn tại {local_dir} — bỏ qua.")
        return

    print(f"Downloading {repo_id}")
    print(f"   → {local_dir}")
    local_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
    )

    size_mb = sum(f.stat().st_size for f in local_dir.rglob("*") if f.is_file()) / 1e6
    print(f"✅ Xong! ({size_mb:.0f} MB)\n")


def main() -> None:
    print("=" * 55)
    print("  ABSA Analyzer — Model Downloader")
    print("=" * 55)
    print()

    try:
        download(ATE_REPO, ATE_DIR)
        download(ASC_REPO, ASC_DIR)
    except Exception as e:
        print(f"\nLỗi: {e}")
        print("\nKiểm tra:")
        print("  - Kết nối internet")
        print("  - huggingface_hub đã cài: pip install huggingface_hub")
        print("  - Repo public trên HuggingFace")
        sys.exit(1)

    print("Tất cả model đã sẵn sàng!")
    print("   Chạy app: streamlit run app.py")


if __name__ == "__main__":
    main()