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

from scrapers.myrient import update_index


def main() -> None:
    update_index()


if __name__ == "__main__":
    main()
