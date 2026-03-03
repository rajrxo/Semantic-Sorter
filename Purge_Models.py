import os
import shutil
import sys
import subprocess

REMOVE_PACKAGES = "--full" in sys.argv


def safe_rmtree(path):
    if not path:
        return

    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"removed: {path}")
        except Exception as e:
            print(f"[warn] failed to remove {path}: {e}")
    else:
        print(f"not found: {path}")


def purge_model_caches():
    print("cleaning model caches...")

    home = os.path.expanduser("~")

    paths = [
        os.environ.get("HF_HOME"),
        os.environ.get("TRANSFORMERS_CACHE"),
        os.environ.get("TORCH_HOME"),
        os.path.join(home, ".cache", "huggingface"),
        os.path.join(home, ".cache", "torch"),
    ]

    seen = set()
    clean_paths = []

    for p in paths:
        if p and p not in seen:
            clean_paths.append(p)
            seen.add(p)

    for p in clean_paths:
        safe_rmtree(p)


def uninstall_packages():
    print("uninstalling python packages...")

    packages = [
        "sentence-transformers",
        "open_clip_torch",
        "transformers",
        "torch",
        "pytesseract",
        "pypdf",
        "scikit-learn",
        "pillow",
        "numpy",
    ]

    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "uninstall",
            "-y",
            *packages
        ])
    except Exception as e:
        print(f"[warn] pip uninstall issue: {e}")


if __name__ == "__main__":
    print("semantic sorter model cleanup")

    purge_model_caches()

    if REMOVE_PACKAGES:
        uninstall_packages()
        print("full cleanup complete")
    else:
        print("model cache cleaned")
        print("tip: run with --full to also uninstall python packages")