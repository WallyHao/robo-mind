#!/usr/bin/env python3
"""Download Pi05 pre-trained weights from HuggingFace Hub.

Usage:
    python download_model.py [--output-dir /path/to/save]

MIRROR:
    # 国内网络建议使用镜像站
    export HF_ENDPOINT=https://hf-mirror.com
    python download_model.py

Requires: pip install huggingface_hub
"""

import argparse
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Pi05 base model from HuggingFace")
    parser.add_argument(
        "--output-dir",
        default=str(Path.cwd() / "pi05_model"),
        help="directory to save the model (default: ./pi05_model)",
    )
    parser.add_argument(
        "--hf-mirror",
        default=os.environ.get("HF_ENDPOINT", ""),
        help="HuggingFace mirror endpoint (e.g. https://hf-mirror.com)",
    )
    parser.add_argument(
        "--proxy",
        default="",
        help="SOCKS5 proxy URL (e.g. socks5h://127.0.0.1:7897)",
    )
    args = parser.parse_args()

    if args.hf_mirror:
        os.environ["HF_ENDPOINT"] = args.hf_mirror
    else:
        os.environ.pop("HF_ENDPOINT", None)

    if args.proxy:
        os.environ["HTTP_PROXY"] = args.proxy
        os.environ["HTTPS_PROXY"] = args.proxy

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)

    model_id = "lerobot/pi05_base"
    save_path = args.output_dir

    print(f"Downloading {model_id} to {save_path} ...")

    try:
        snapshot_download(
            repo_id=model_id,
            local_dir=save_path,
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
        )
        print(f"Done. Model saved to: {save_path}")
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
