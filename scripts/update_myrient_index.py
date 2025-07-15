#!/usr/bin/env python3
"""Utility to update the local Myrient file index.

This script crawls the Myrient open directory using Python code (no `rclone`
required) and writes the results to `data/myrient_index.txt`.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from scrapers.myrient import update_index, PROGRESS_PATH, INDEX_PATH


def main() -> None:
    resume = False
    if os.path.exists(PROGRESS_PATH):
        while True:
            ans = input("Resume previous crawl or start over? [r/s]: ").strip().lower()
            if ans == "r":
                resume = True
                break
            if ans == "s":
                break
            print("Please enter 'r' to resume or 's' to start over.")
    else:
        ans = input("Start new crawl? [y/N]: ").strip().lower()
        if ans != "y":
            print("Aborting.")
            return

    if not resume:
        if os.path.exists(INDEX_PATH):
            os.remove(INDEX_PATH)
        if os.path.exists(PROGRESS_PATH):
            os.remove(PROGRESS_PATH)

    update_index(resume=resume)


if __name__ == "__main__":
    main()
