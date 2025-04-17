import urllib.parse
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from playwright.async_api import async_playwright

BASE_URL = "https://gog-games.to"
THRESHOLD = 85  # Adjusted threshold for strict matching

async def search_gog_games(query: str) -> list[tuple[str, str, float]]:
    """
    Uses Playwright to load the URL https://gog-games.to/?search=<query> and parse the rendered results.
    Returns a list of tuples: (detail_url, displayed_name, fuzzy_score) for candidates
    whose fuzzy score is above THRESHOLD.
    """
    encoded_query = urllib.parse.quote(query)
    search_url = f"{BASE_URL}/?search={encoded_query}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # For debugging, you can set headless=False
        page = await browser.new_page()
        # Navigate to the search URL and wait until network is idle.
        await page.goto(search_url, wait_until="networkidle")
        # Wait an additional 5000ms to let the JavaScript fully render the results.
        await page.wait_for_timeout(5000)

        # Try waiting for the specific selector (up to 15 seconds)
        try:
            await page.wait_for_selector("a.jsx-3307928730.card", timeout=15000)
        except Exception as e:
            print("[gog_games] No results found using selector 'a.jsx-3307928730.card'; trying generic selector.")
            # If not found, we don't immediately return but will check the content below.

        html = await page.content()
        await browser.close()

    print(f"[gog_games debug] Fetched HTML snippet (via Playwright): {html[:500]}")

    soup = BeautifulSoup(html, "html.parser")
    # Try the specific selector first.
    results = soup.select("a.jsx-3307928730.card")
    if not results:
        results = soup.select("a[href^='/game/']")

    candidates = []
    for a_tag in results:
        href = a_tag.get("href")
        if not href:
            continue
        detail_url = urllib.parse.urljoin(BASE_URL, href)

        # Extract the displayed game title using the nested span.
        title_span = a_tag.select_one("div.jsx-3307928730.title span")
        if not title_span:
            title_span = a_tag.find("span")
            if not title_span:
                continue
        displayed_name = title_span.get_text(strip=True)

        score = fuzz.WRatio(displayed_name.lower(), query.lower())
        print(f"[gog_games debug] Candidate: '{displayed_name}' with score {score} for query '{query}'")
        if score >= THRESHOLD:
            candidates.append((detail_url, displayed_name, score))

    return candidates

async def get_gog_download_links(query: str) -> list[str]:
    """
    Calls search_gog_games(query) and returns the detail link (wrapped in a list)
    for the best candidate that passes the fuzzy match threshold.
    """
    candidates = await search_gog_games(query)
    if not candidates:
        print("[gog_games] No candidates found.")
        return []

    best = max(candidates, key=lambda tup: tup[2])
    best_url, best_name, best_score = best
    print(f"[gog_games] Best match: '{best_name}' (score={best_score}) => {best_url}")

    if best_score < THRESHOLD:
        return []
    return [best_url]
