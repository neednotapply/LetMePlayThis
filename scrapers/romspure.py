# scrapers/romspure.py

import aiohttp
import urllib.parse
from bs4 import BeautifulSoup

# We do fuzzy matching for the game name within the search results
# Attempt to use rapidfuzz for fast fuzzy matching but fall back to difflib
from scrapers.fuzz_fallback import fuzz

# Import the dictionary-based function from platform_map
from scrapers.platform_map import get_romspure_subpath_exact

BASE_URL = "https://romspure.cc"

async def search_romspure(game_title: str, platform_name: str) -> list[str]:
    # 1) Attempt an exact dictionary match for the platform
    subpath = get_romspure_subpath_exact(platform_name)
    if subpath is None:
        print(f"[romspure] No exact subpath mapping for '{platform_name}' in platform_map.")
        return []

    # 2) Build the search URL
    encoded_query = urllib.parse.quote(game_title)
    search_url = f"{BASE_URL}/roms/{subpath}?keywords={encoded_query}&orderby=popular&order=desc"
    print(f"[romspure] Searching: {search_url}")

    # 3) Fetch the HTML with aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as resp:
            if resp.status != 200:
                print(f"[romspure] HTTP {resp.status} from {search_url}")
                return []
            html = await resp.text()

    # 4) Parse the HTML
    soup = BeautifulSoup(html, "html.parser")
    containers = soup.select("div.col-archive-item")
    if not containers:
        snippet = html[:500]
        print(f"[romspure] No results for '{game_title}' subpath='{subpath}'")
        print("DEBUG snippet:", snippet)
        return []

    # We'll gather (url, displayed_name, fuzzy_score)
    candidates = []
    for c in containers:
        a_tag = c.select_one('a[href^="https://romspure.cc/roms/"]')
        if not a_tag:
            continue

        detail_url = a_tag.get("href")
        # Ensure the final link has the exact subpath
        if detail_url:
            path = urllib.parse.urlparse(detail_url).path
            expect = f"/roms/{subpath}/"
            if not path.startswith(expect):
                continue
        else:
            continue

        # The displayed name is typically in <h3 class="h6 font-weight-semibold">
        h3 = a_tag.select_one("h3.h6.font-weight-semibold")
        if not h3:
            continue

        displayed_name = h3.get_text(strip=True)
        score = fuzz.WRatio(displayed_name.lower(), game_title.lower())
        if score < 70:
            # If the displayed name is below threshold, skip
            continue

        candidates.append((detail_url, displayed_name, score))

    if not candidates:
        return []

    # 5) pick the single best fuzzy match
    best = max(candidates, key=lambda x: x[2])  # (detail_url, name, score)
    best_url, best_name, best_score = best
    print(f"[romspure] Best match: '{best_name}' (score={best_score}) => {best_url}")
    return [best_url]

async def get_romspure_download_links(game_title: str, platform_name: str) -> list[str]:
    """
    1) calls search_romspure
    2) returns just the best single link
    """
    detail_urls = await search_romspure(game_title, platform_name)
    return detail_urls  # either [the_url] or []
