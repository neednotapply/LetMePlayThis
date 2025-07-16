#!/usr/bin/env python3
"""Generate the EmulatorJS game index used for Play Now links."""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from scrapers.emulatorjs import INDEX_PATH, EMULATORJS_PLATFORM_MAP


def _collect_titles(frontend_dir: str) -> dict[str, list[str]]:
    """Return a mapping of system code to list of titles."""
    result: dict[str, list[str]] = {}
    data_dir = os.path.join(frontend_dir, "data")
    for code in EMULATORJS_PLATFORM_MAP.values():
        path = os.path.join(data_dir, code, "index.json")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError:
                print(f"[emulatorjs] could not parse {path}")
                continue
        titles: list[str] = []
        for item in entries:
            title = (
                item.get("title")
                or item.get("name")
                or item.get("slug")
                or ""
            )
            if title:
                titles.append(title)
        if titles:
            result[code] = titles
    return result


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: update_emulatorjs_index.py <path_to_frontend>")
        sys.exit(1)

    frontend_dir = sys.argv[1]
    index = _collect_titles(frontend_dir)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"[emulatorjs] wrote index for {len(index)} systems to {INDEX_PATH}")


if __name__ == "__main__":
    main()

