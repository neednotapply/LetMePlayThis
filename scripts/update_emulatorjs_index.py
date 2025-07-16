#!/usr/bin/env python3
"""Generate the EmulatorJS game index used for Play Now links.

The script looks for JSON config files where each file represents a system.
All ``*.json`` files in the given directory (or the script's own directory if
no path is supplied) are parsed. Each JSON file should contain an ``items``
object mapping game titles to their configuration. The filename without the
extension is used as the system's short code.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from scrapers.emulatorjs import INDEX_PATH


def _collect_titles(config_dir: str) -> dict[str, list[str]]:
    """Return a mapping of system code to list of titles."""
    result: dict[str, list[str]] = {}
    for name in sorted(os.listdir(config_dir)):
        if not name.endswith(".json"):
            continue
        code = os.path.splitext(name)[0]
        path = os.path.join(config_dir, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"[emulatorjs] could not parse {path}")
                continue
        items = data.get("items")
        if isinstance(items, dict):
            titles = list(items.keys())
            if titles:
                result[code] = titles
        else:
            print(f"[emulatorjs] no items found in {path}")
    return result


def main() -> None:
    if len(sys.argv) > 2:
        print("Usage: update_emulatorjs_index.py [path_to_configs]")
        sys.exit(1)

    config_dir = sys.argv[1] if len(sys.argv) == 2 else SCRIPT_DIR
    index = _collect_titles(config_dir)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"[emulatorjs] wrote index for {len(index)} systems to {INDEX_PATH}")


if __name__ == "__main__":
    main()

