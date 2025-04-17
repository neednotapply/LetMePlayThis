#!/usr/bin/env python3
import os
import json
import discord
import aiohttp
import asyncio
from discord.ext import commands

# Load config
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "config.json")) as f:
    cfg = json.load(f)

TOKEN = cfg["token"]
GUILD_ID = int(cfg["guildId"])
APP_ID = None  # We'll fetch it from the bot

REMOVE_COMMAND_ID = "1301606807122219019"
ENSURE_COMMAND_ID = "1361848834891841718"

intents = discord.Intents.none()
bot = commands.Bot(command_prefix=cfg.get("prefix", "!"), intents=intents)

@bot.event
async def on_ready():
    global APP_ID
    APP_ID = bot.user.id
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # --- Remove old command ---
        delete_url = f"https://discord.com/api/v10/applications/{APP_ID}/commands/{REMOVE_COMMAND_ID}"
        async with session.delete(delete_url) as resp:
            if resp.status == 204:
                print(f"✅ Removed command ID {REMOVE_COMMAND_ID}")
            else:
                print(f"⚠️ Failed to remove {REMOVE_COMMAND_ID} (status {resp.status})")

    # Re-sync all commands (should register new one again)
    print(f"🔄 Syncing commands to guild {GUILD_ID}")
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print("✅ Guild sync complete")

    print("🔄 Syncing global commands")
    await bot.tree.sync()
    print("✅ Global sync complete")

    await bot.close()

if __name__ == "__main__":
    bot.run(TOKEN)
