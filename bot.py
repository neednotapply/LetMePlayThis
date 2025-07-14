import os
import json
import discord
from discord.ext import commands
from discord import app_commands, Interaction
import aiohttp
from bs4 import BeautifulSoup

# Import your scraper functions:
from scrapers.gog_games import get_gog_download_links
from scrapers.romspure import get_romspure_download_links
from scrapers.myrient import get_myrient_download_links

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

with open(config_path, "r") as f:
    config = json.load(f)

TOKEN = config["token"]
GUILD_ID = int(config["guildId"])
GUILD = discord.Object(id=GUILD_ID)

THEGAMESDB_API_KEY = config["theGamesDbApiKey"]
PREFIX = config["prefix"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# -------------------------------------------------------------------------
# Basic GET helper for TheGamesDB calls
# -------------------------------------------------------------------------
async def fetch_json(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            print(f"DEBUG fetch_json GET {resp.url} => {resp.status}")
            if resp.status != 200:
                text = await resp.text()
                print("DEBUG response text:", text)
                raise RuntimeError(f"HTTP {resp.status} from TheGamesDB")
            return await resp.json()

# -------------------------------------------------------------------------
# Utility to clean HTML from descriptions
# -------------------------------------------------------------------------
def clean_text(raw_text: str) -> str:
    return BeautifulSoup(raw_text, "html.parser").get_text(separator=" ").strip()

# -------------------------------------------------------------------------
# 1) ByGameName search with TheGamesDB
# -------------------------------------------------------------------------
async def search_by_name(title: str) -> list:
    base_url = "https://api.thegamesdb.net/v1/Games/ByGameName"
    fields = "platform,rating"
    url = (
        f"{base_url}?apikey={THEGAMESDB_API_KEY}"
        f"&name={title}"
        f"&fields={fields}"
    )
    data = await fetch_json(url)
    return data.get("data", {}).get("games", [])

# -------------------------------------------------------------------------
# 2) Minimal ByGameID to get platform + release_date for dropdown label
# -------------------------------------------------------------------------
async def fetch_for_dropdown(game_id: int) -> dict:
    base = "https://api.thegamesdb.net/v1/Games/ByGameID"
    fields = "platform,overview,rating"
    includes = "platform"

    url = (
        f"{base}?apikey={THEGAMESDB_API_KEY}"
        f"&id={game_id}"
        f"&fields={fields}"
        f"&include={includes}"
    )
    data = await fetch_json(url)
    games_list = data.get("data", {}).get("games", [])
    if not games_list:
        return {"title": "", "year": "????", "platform_name": "Unknown"}

    g_info = games_list[0]
    game_title = g_info.get("game_title", "Unknown Title")
    rdate = g_info.get("release_date", "")
    year_str = rdate[:4] if rdate else "????"

    incl = data.get("include", {})
    p_data = incl.get("platform", {}).get("data", {})
    p_val = g_info.get("platform")
    p_str = "Unknown"
    if p_val is not None:
        spv = str(p_val)
        if spv in p_data:
            p_str = p_data[spv].get("name", "Unknown")

    return {
        "title": game_title,
        "year": year_str,
        "platform_name": p_str
    }

# -------------------------------------------------------------------------
# 3) Full ByGameID for final embed details
# -------------------------------------------------------------------------
async def get_full_details(game_id: int) -> dict:
    base = "https://api.thegamesdb.net/v1/Games/ByGameID"
    fields = "platform,overview,rating"
    includes = "platform"

    url = (
        f"{base}?apikey={THEGAMESDB_API_KEY}"
        f"&id={game_id}"
        f"&fields={fields}"
        f"&include={includes}"
    )
    data = await fetch_json(url)
    games_list = data.get("data", {}).get("games", [])
    if not games_list:
        return {}

    g_info = games_list[0]
    result = {}
    result["title"] = g_info.get("game_title", "Unknown Title")
    rdate = g_info.get("release_date", "")
    result["release_date"] = rdate if rdate else "Unknown"
    result["overview"] = g_info.get("overview", "")
    result["rating"] = g_info.get("rating", "N/A")

    incl = data.get("include", {})
    p_data = incl.get("platform", {}).get("data", {})
    p_val = g_info.get("platform")
    plat_str = "Unknown"
    if p_val is not None:
        spv = str(p_val)
        if spv in p_data:
            plat_str = p_data[spv].get("name", "Unknown")
    result["platform"] = plat_str

    return result

# -------------------------------------------------------------------------
# 4) /v1/Games/Images for clearlogo/boxart from TheGamesDB
# -------------------------------------------------------------------------
async def fetch_images(game_id: int) -> str:
    base_url = "https://api.thegamesdb.net/v1/Games/Images"
    filter_types = "clearlogo,boxart"
    url = (
        f"{base_url}?apikey={THEGAMESDB_API_KEY}"
        f"&games_id={game_id}"
        f"&filter%5Btype%5D={filter_types}"
    )
    data = await fetch_json(url)

    data_obj = data.get("data", {})
    base_original = data_obj.get("base_url", {}).get("original", "https://cdn.thegamesdb.net/images/original/")
    images_dict = data_obj.get("images", {})

    arr = images_dict.get(str(game_id), [])
    if not arr:
        return ""

    clearlogo_obj = next((img for img in arr if img.get("type") == "clearlogo"), None)
    if clearlogo_obj:
        filename = clearlogo_obj["filename"]
        return base_original + filename

    boxarts = [img for img in arr if img.get("type") == "boxart"]
    if boxarts:
        filename = boxarts[0]["filename"]
        return base_original + filename

    return ""

# -------------------------------------------------------------------------
# Aggregator for download links (GOG + Romspure)
# Returns a list of tuples: (source, URL)
# -------------------------------------------------------------------------
async def get_all_download_links(game_title: str, platform_name: str) -> list[tuple[str, str]]:
    links = []

    # For PC games (including DOS), only query GOG-Games.
    if platform_name.lower() in {"pc", "dos"}:
        gog_links = await get_gog_download_links(game_title)
        for url in gog_links:
            links.append(("GOG-Games", url))
    else:
        # For non-PC platforms query both Romspure and Myrient.
        roms_links = await get_romspure_download_links(game_title, platform_name)
        for url in roms_links:
            links.append(("RomsPure", url))

        myrient_links = await get_myrient_download_links(game_title, platform_name)
        for url in myrient_links:
            links.append(("Myrient", url))

    return links

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# -------------------------------------------------------------------------
# /play slash command
# -------------------------------------------------------------------------
@bot.tree.command(name="play", description="Search TheGamesDB for video games")
@app_commands.describe(title="Game title to search")
async def play_command(interaction: Interaction, title: str):
    """
    Flow:
      1) Search TheGamesDB -> up to 10 results.
      2) For each, fetch minimal info (platform + year) for dropdown label.
      3) User picks one -> fetch full details + images -> aggregate download links from GOG (for PC)
         or RomsPure (for non-PC).
      4) Build embed.
    """
    await interaction.response.defer()

    # A) Search TheGamesDB
    search_results = await search_by_name(title)
    if not search_results:
        await interaction.followup.send("No results found or an error occurred.")
        return

    top_games = search_results[:10]

    # Build dropdown options
    options = []
    for g in top_games:
        g_id = g["id"]
        fallback_title = g.get("game_title", "Unknown Title")
        drow = await fetch_for_dropdown(g_id)
        final_title = drow["title"] if drow["title"] else fallback_title
        plat_str = drow["platform_name"]
        year_str = drow["year"]
        label_str = f"{final_title} ({plat_str}, {year_str})"
        options.append(discord.SelectOption(label=label_str, value=str(g_id)))

    async def select_callback(select_interaction: Interaction):
        await select_interaction.response.defer()
        game_id_str = select_interaction.data["values"][0]
        game_id = int(game_id_str)

        # 1) Retrieve full details from TheGamesDB
        details = await get_full_details(game_id)
        if not details:
            await select_interaction.followup.send("Could not retrieve game details.")
            return

        # 2) Fetch images (clearlogo or boxart)
        img_url = await fetch_images(game_id)

        # 3) Build embed
        title_text = details["title"]
        overview = clean_text(details["overview"] or "No overview.")
        release_date = details["release_date"]
        rating = details["rating"]
        platform_str = details["platform"]

        embed = discord.Embed(
            title=title_text,
            description=overview[:500] + ("..." if len(overview) > 500 else ""),
            color=discord.Color.blue()
        )
        embed.add_field(name="Platform", value=platform_str, inline=True)
        embed.add_field(name="Release Date", value=release_date, inline=True)
        embed.add_field(name="Rating", value=str(rating), inline=True)

        if img_url:
            embed.set_thumbnail(url=img_url)
        else:
            embed.set_footer(text="No image found for this game.")

        # 4) Aggregator: Get download links from GOG and/or RomsPure
        dl_links = await get_all_download_links(title_text, platform_str)
        if dl_links:
            link_text = "\n".join(
                f"[{title_text} at {source}]({url})" for source, url in dl_links
            )
            embed.add_field(name="Download Links", value=link_text, inline=False)
        else:
            embed.add_field(name="Download Links", value="No links found", inline=False)

        await select_interaction.edit_original_response(embed=embed, view=None)

    select = discord.ui.Select(placeholder="Select a game", options=options)
    select.callback = select_callback
    view = discord.ui.View()
    view.add_item(select)
    await interaction.followup.send("Select a game:", view=view)

bot.run(TOKEN)
