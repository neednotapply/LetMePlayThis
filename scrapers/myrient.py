# scrapers/myrient.py
import os
import urllib.parse
import json

import requests
from bs4 import BeautifulSoup
# Attempt to use rapidfuzz for fast fuzzy matching but fall back to difflib
from scrapers.fuzz_fallback import fuzz
from scrapers.platform_map import canonicalize_platform_name

BASE_URL = "https://myrient.erista.me/files"

# Local index file generated via scripts/update_myrient_index.py
INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "myrient_index.txt")
# File storing crawl progress so that indexing can be resumed
PROGRESS_PATH = os.path.join(os.path.dirname(INDEX_PATH), "myrient_progress.json")

_index_cache: list[str] | None = None


def update_index(resume: bool = False) -> None:
    """Regenerate or resume the local index file by crawling the Myrient directory."""

    def crawl(out_file, stack: list[str], count: int) -> list[str]:
        """Recursively collect all file paths from the open directory."""
        results: list[str] = []
        session = requests.Session()

        while stack:
            rel = stack.pop()
            encoded_rel = urllib.parse.quote(rel, safe="/")
            url = urllib.parse.urljoin(f"{BASE_URL}/", encoded_rel)
            print(f"[myrient] Fetching {url}")
            resp = session.get(url)
            if resp.status_code == 404:
                print(f"[myrient] 404 Not Found: {url} -- skipping")
                continue
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for a in soup.select("table#list a"):
                href = a.get("href")
                if not href or href == "../":
                    continue
                decoded = urllib.parse.unquote(href)
                if href.endswith("/"):
                    stack.append(rel + decoded)
                else:
                    path = rel + decoded
                    results.append(path)
                    out_file.write(path + "\n")
                    count += 1
                    if count % 100 == 0:
                        out_file.flush()
                        print(f"[myrient] {count} files indexed so far...")
            # Save crawl progress so we can resume if needed
            with open(PROGRESS_PATH, "w", encoding="utf-8") as pf:
                json.dump(stack, pf)

        out_file.flush()
        return results

    global _index_cache
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)

    stack: list[str]
    count = 0
    mode = "w"
    if resume and os.path.isfile(PROGRESS_PATH) and os.path.isfile(INDEX_PATH):
        with open(PROGRESS_PATH, "r", encoding="utf-8") as pf:
            stack = json.load(pf)
        count = sum(1 for _ in open(INDEX_PATH, "r", encoding="utf-8"))
        mode = "a"
        print(f"[myrient] Resuming crawl with {len(stack)} paths left...")
    else:
        stack = [""]
        print("[myrient] Starting new crawl. This may take a while...")

    with open(INDEX_PATH, mode, encoding="utf-8") as f:
        entries = crawl(f, stack, count)

    if os.path.isfile(PROGRESS_PATH):
        os.remove(PROGRESS_PATH)

    _index_cache = None
    total = count + len(entries)
    print(f"[myrient] Index updated with {total} entries.")

MYRIENT_PLATFORM_MAP = {
    "Nintendo Game Boy": "No-Intro/Nintendo - Game Boy",
    "Nintendo Game Boy Color": "No-Intro/Nintendo - Game Boy Color",
    "Nintendo Game Boy Advance": "No-Intro/Nintendo - Game Boy Advance",
    "Nintendo DS": "No-Intro/Nintendo - Nintendo DS (Decrypted)",
    "Nintendo 64": "No-Intro/Nintendo - Nintendo 64",
    "Nintendo Entertainment System": "No-Intro/Nintendo - Nintendo Entertainment System (Headered)",
    "Super Nintendo (SNES)": "No-Intro/Nintendo - Super Nintendo Entertainment System",
    "Super Nintendo Entertainment System": "No-Intro/Nintendo - Super Nintendo Entertainment System",
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
    "Atari 5200": "No-Intro/Atari - 5200",
    "Atari 7800": "No-Intro/Atari - 7800",
    "Fujitsu FM Towns Marty": "Redump/Fujitsu - FM-Towns",
    "Bandai Pippin": "Redump/Bandai - Pippin",
    "Atari Jaguar CD": "Redump/Atari - Jaguar CD Interactive Multimedia System",
    "Sega Dreamcast": "Redump/Sega - Dreamcast",
    "Sega Mega CD": "Redump/Sega - Mega CD & Sega CD",
    "Sega Game Gear": "No-Intro/Sega - Game Gear",
    "Sega Genesis": "No-Intro/Sega - Mega Drive - Genesis",
    "Sega Saturn": "Redump/Sega - Saturn",
    "Sony Playstation Vita": "No-Intro/Sony - PlayStation Vita (PSN) (Content)",
    "NEC PC Engine - TurboGrafx-16": "No-Intro/NEC - PC Engine - TurboGrafx-16",
    "NEC PC Engine CD": "Redump/NEC - PC Engine CD & TurboGrafx CD",
    "NEC PC-FX": "Redump/NEC - PC-FX & PC-FXGA",
    "NEC PC-98": "Redump/NEC - PC-98 series",
    "Panasonic 3DO": "Redump/Panasonic - 3DO Interactive Multiplayer",
    "Philips CD-i": "Redump/Philips - CD-i",
    "SNK Neo Geo CD": "Redump/SNK - Neo Geo CD",
    "Apple Macintosh": "Redump/Apple - Macintosh",
    "Nintendo Famicom Disk System": "No-Intro/Nintendo - Family Computer Disk System (FDS)",
    "Nintendo 64 (BigEndian)": "No-Intro/Nintendo - Nintendo 64 (BigEndian)",
    "Nintendo 64DD": "No-Intro/Nintendo - Nintendo 64DD",
    "Nintendo Pokemon Mini": "No-Intro/Nintendo - Pokemon Mini",
    "Nintendo Virtual Boy": "No-Intro/Nintendo - Virtual Boy",
    "Nintendo New 3DS": "No-Intro/Nintendo - New Nintendo 3DS (Decrypted)",
    "Nintendo GameCube (NKit)": "Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]",
    "Nintendo Wii (NKit)": "Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]",
    "Nintendo Wii U (WUA)": "Internet Archive/teamgt19/nintendo-wii-u-usa-full-set-wua-format-embedded-dlc-updates",
    "Nintendo Wii U eShop (WUA)": "Internet Archive/teamgt19/nintendo-wii-u-eshop-usa-full-set-wua-format-embedded-dlc-updates",
    "Sony PlayStation 3 (PSN)": "No-Intro/Sony - PlayStation 3 (PSN) (Content)",
    # Arcade platforms
    "Arcade Konami FireBeat": "Redump/Arcade - Konami - FireBeat",
    "Arcade Konami M2": "Redump/Arcade - Konami - M2",
    "Arcade Konami System 573": "Redump/Arcade - Konami - System 573",
    "Arcade Konami System GV": "Redump/Arcade - Konami - System GV",
    "Arcade Konami e-Amusement": "Redump/Arcade - Konami - e-Amusement",
    "Arcade Triforce": "Redump/Arcade - Namco - Sega - Nintendo - Triforce",
    "Arcade Namco System 246": "Redump/Arcade - Namco - System 246",
    "Arcade Sega Chihiro": "Redump/Arcade - Sega - Chihiro",
    "Arcade Sega Lindbergh": "Redump/Arcade - Sega - Lindbergh",
    "Arcade Sega Naomi": "Redump/Arcade - Sega - Naomi",
    "Arcade Sega Naomi 2": "Redump/Arcade - Sega - Naomi 2",
    "Arcade Sega RingEdge": "Redump/Arcade - Sega - RingEdge",
    "Arcade Sega RingEdge 2": "Redump/Arcade - Sega - RingEdge 2",
    # Total DOS Collection
    "DOS 1982": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1982",
    "DOS 1983": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1983",
    "DOS 1985": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1985",
    "DOS 1988": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1988",
    "DOS 1990": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1990",
    "DOS 1991": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1991",
    "DOS 1996": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1996",
    "DOS 1997": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1997",
    "DOS 1999": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/1999",
    "DOS 199x": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/199x",
    "DOS 2002": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/2002",
    "DOS 2003": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/2003",
    "DOS 2008": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/2008",
    "DOS 2009": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/2009",
    "DOS 2011": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/2011",
    "DOS 2014": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/2014",
    "DOS 2015": "Internet Archive/sketch_the_cow/Total_DOS_Collection_Release_16_March_2019/Games/Files/2015",
    # Common PC platforms
    "PC": "Redump/IBM - PC compatible",
    "DOS": "Redump/IBM - PC compatible",
}

THRESHOLD = 70

def get_myrient_subpath_exact(platform_name: str) -> str | None:
    canonical = canonicalize_platform_name(platform_name)
    return MYRIENT_PLATFORM_MAP.get(canonical)


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
            encoded_path = urllib.parse.quote(entry, safe="/")
            url = f"{BASE_URL}/{encoded_path}"
            candidates.append((score, url, fname))

    if not candidates:
        return []

    best_score, best_url, best_name = max(candidates, key=lambda t: t[0])
    print(f"[myrient] Best match: '{best_name}' (score={best_score}) => {best_url}")
    return [best_url]

async def get_myrient_download_links(game_title: str, platform_name: str) -> list[str]:
    return await search_myrient(game_title, platform_name)
