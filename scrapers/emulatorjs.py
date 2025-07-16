# scrapers/emulatorjs.py
"""Lookup game titles in a local EmulatorJS index and build Play Now links."""

from __future__ import annotations

import json
import os
from typing import Dict, List

from scrapers.fuzz_fallback import fuzz
from scrapers.platform_map import canonicalize_platform_name

# Environment variable for the base URL used to build play links
# Can be overridden at runtime via :func:`set_base_url`.
BASE_URL: str | None = os.environ.get("EMULATORJS_BASE_URL")


def set_base_url(url: str | None) -> None:
    """Override :data:`BASE_URL` with a value from configuration."""
    global BASE_URL
    BASE_URL = url

# Path to the JSON index generated via scripts/update_emulatorjs_index.py
INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "emulatorjs_index.json")

# Mapping of TheGamesDB platform names to EmulatorJS short codes
EMULATORJS_PLATFORM_MAP: Dict[str, str] = {
    "Nintendo Game Boy": "gb",
    "Nintendo Game Boy Color": "gbc",
    "Nintendo Game Boy Advance": "gba",
    "Nintendo Entertainment System": "nes",
    "Super Nintendo (SNES)": "snes",
    "Super Nintendo Entertainment System": "snes",
    "Nintendo 64": "n64",
    "Sega Genesis": "segaMD",
    "Sega Mega Drive - Genesis": "segaMD",
    "Sega Mega Drive": "segaMD",
    "Sony PlayStation": "psx",
    "3DO Interactive Multiplayer": "3do",
}

_index_cache: Dict[str, List[str]] | None = None


def _load_index() -> Dict[str, List[str]]:
    """Load the index from ``INDEX_PATH`` once and cache it."""
    global _index_cache
    if _index_cache is not None:
        return _index_cache

    if os.path.isfile(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            _index_cache = json.load(f)
    else:
        print(f"[emulatorjs] index file not found at {INDEX_PATH}")
        _index_cache = {}

    return _index_cache


def _get_code(platform_name: str) -> str | None:
    canonical = canonicalize_platform_name(platform_name)
    return EMULATORJS_PLATFORM_MAP.get(canonical)


async def search_emulatorjs(game_title: str, platform_name: str) -> str | None:
    """Return a Play Now URL if a match is found."""
    if not BASE_URL:
        return None
    code = _get_code(platform_name)
    if code is None:
        print(f"[emulatorjs] no code for platform '{platform_name}'")
        return None

    index = _load_index().get(code, [])
    if not index:
        return None

    best_idx: int | None = None
    best_score = -1
    for idx, title in enumerate(index):
        score = fuzz.WRatio(title.lower(), game_title.lower())
        if score > best_score:
            best_idx = idx
            best_score = score

    if best_idx is None or best_score < 70:
        return None

    # EmulatorJS URLs use 1-based numbering in the fragment
    return f"{BASE_URL}{code}---{best_idx + 1}"


async def get_emulatorjs_play_url(game_title: str, platform_name: str) -> str | None:
    """Asynchronous wrapper for :func:`search_emulatorjs`."""

    return await search_emulatorjs(game_title, platform_name)
