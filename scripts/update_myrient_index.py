#!/usr/bin/env python3
"""Utility to update the local Myrient file index.

This script uses `rclone` with the HTTP remote to recursively list all files
from the Myrient open directory. The output is written to `data/myrient_index.txt`.
`rclone` must be installed and network access allowed.
"""

import os
import subprocess

BASE_URL = "https://myrient.erista.me/files/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
INDEX_PATH = os.path.join(ROOT_DIR, "data", "myrient_index.txt")


def main() -> None:
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    cmd = [
        "rclone",
        "lsf",
        "-R",
        "--http-url",
        BASE_URL,
        ":http:",
    ]
    print("Updating Myrient index. This may take a while...")
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        subprocess.check_call(cmd, stdout=f)
    print(f"Index written to {INDEX_PATH}")


if __name__ == "__main__":
    main()
