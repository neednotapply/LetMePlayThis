# scrapers/myrient.py
import os
import subprocess
import urllib.parse

from rapidfuzz import fuzz

BASE_URL = "https://myrient.erista.me/files"

# Local index file generated via scripts/update_myrient_index.py
INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "myrient_index.txt")

_index_cache: list[str] | None = None


def update_index() -> None:
    """Uses rclone to regenerate the local index file."""
    global _index_cache
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    cmd = [
        "rclone",
        "lsf",
        "-R",
        "--http-url",
        f"{BASE_URL}/",
        ":http:",
    ]
    print("[myrient] Updating local index via rclone. This may take a while...")
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        subprocess.check_call(cmd, stdout=f)
    _index_cache = None

MYRIENT_PLATFORM_MAP = {
    "Nintendo Game Boy": "No-Intro/Nintendo - Game Boy",
    "Nintendo Game Boy Color": "No-Intro/Nintendo - Game Boy Color",
    "Nintendo Game Boy Advance": "No-Intro/Nintendo - Game Boy Advance",
    "Nintendo DS": "No-Intro/Nintendo - Nintendo DS (Decrypted)",
    "Nintendo 64": "No-Intro/Nintendo - Nintendo 64",
    "Nintendo Entertainment System": "No-Intro/Nintendo - Nintendo Entertainment System (Headered)",
    "Super Nintendo (SNES)": "No-Intro/Nintendo - Super Nintendo Entertainment System",
    "Nintendo 3DS": "No-Intro/Nintendo - Nintendo 3DS (Decrypted)",
    "Nintendo GameCube": "Redump/Nintendo - GameCube",
    "Nintendo Wii": "Redump/Nintendo - Wii",
    "Nintendo Wii U": "Redump/Nintendo - Wii U",
    "Sony PlayStation": "Redump/Sony - PlayStation",
    "Sony PlayStation 2": "Redump/Sony - PlayStation 2",
    "Sony Playstation 3": "Redump/Sony - PlayStation 3",
    "Sony Playstation 4": "Redump/Sony - PlayStation 4",
    "Sony PSP": "Redump/Sony - PlayStation Portable",
    "Microsoft Xbox": "Redump/Microsoft - Xbox",
    "Microsoft Xbox 360": "Redump/Microsoft - Xbox 360",
    # Additional consoles and computers
    "3DO Interactive Multiplayer": "Redump/Panasonic - 3DO Interactive Multiplayer",
    "Atari 2600": "No-Intro/Atari - Atari 2600",
    "Fujitsu FM Towns Marty": "Redump/Fujitsu - FM-Towns",
    "Sega Dreamcast": "Redump/Sega - Dreamcast",
    "Sega Game Gear": "No-Intro/Sega - Game Gear",
    "Sega Genesis": "No-Intro/Sega - Mega Drive - Genesis",
    "Sega Saturn": "Redump/Sega - Saturn",
    "Sony Playstation Vita": "No-Intro/Sony - PlayStation Vita (PSN) (Content)",
    # Common PC platforms
    "PC": "Redump/IBM - PC compatible",
    "DOS": "Redump/IBM - PC compatible",
}

THRESHOLD = 70

def get_myrient_subpath_exact(platform_name: str) -> str | None:
    return MYRIENT_PLATFORM_MAP.get(platform_name)


def _load_index() -> list[str]:
    """Loads the local index from INDEX_PATH, or returns an empty list."""
    global _index_cache
    if _index_cache is not None:
        return _index_cache
    if not os.path.isfile(INDEX_PATH):
        print(f"[myrient] index file not found at {INDEX_PATH}. Run scripts/update_myrient_index.py to create it.")
        _index_cache = []
    else:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            _index_cache = [line.strip() for line in f if line.strip()]
    return _index_cache

async def search_myrient(game_title: str, platform_name: str) -> list[str]:
    """Search the local Myrient index for a matching file."""
    subpath = get_myrient_subpath_exact(platform_name)
    if subpath is None:
        print(f"[myrient] No subpath mapping for '{platform_name}'")
        return []

    index = _load_index()
    if not index:
        return []

    candidates = []
    for entry in index:
        if not entry.startswith(subpath):
            continue
        fname = os.path.basename(entry)
        score = fuzz.WRatio(fname.lower(), game_title.lower())
        if score >= THRESHOLD:
            encoded_path = urllib.parse.quote(entry, safe="/ ")
            url = f"{BASE_URL}/{encoded_path}"
            candidates.append((score, url, fname))

    if not candidates:
        return []

    best_score, best_url, best_name = max(candidates, key=lambda t: t[0])
    print(f"[myrient] Best match: '{best_name}' (score={best_score}) => {best_url}")
    return [best_url]

async def get_myrient_download_links(game_title: str, platform_name: str) -> list[str]:
    return await search_myrient(game_title, platform_name)
