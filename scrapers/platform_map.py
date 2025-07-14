# scrapers/platform_map.py

ROMSPURE_PLATFORM_MAP = {
    "3DO Interactive Multiplayer": "3do-interactive-multiplayer",
    "Atari 2600": "atari-2600",
    "Fujitsu FM Towns Marty": "fujitsu-fm-towns-marty",
    "Nintendo Entertainment System": "nintendo-entertainment-system",
    "Nintendo 3DS": "3ds",
    "Nintendo 64": "nintendo-64",
    "Nintendo DS": "nintendo-ds",
    "Nintendo Game Boy": "nintendo-game-boy",
    "Nintendo Game Boy Advance": "nintendo-game-boy-advance",
    "Nintendo Game Boy Color": "nintendo-game-boy-color",
    "Nintendo GameCube": "nintendo-gamecube",
    "Nintendo Wii": "nintendo-wii",
    "Nintendo Wii U": "wii-u",
    "Sony PlayStation 2": "sony-playstation-2",
    "Sega Dreamcast": "sega-dreamcast",
    "Sega Game Gear": "sega-game-gear",
    "Sega Genesis": "sega-genesis",
    "Sega Saturn": "sega-saturn",
    "Super Nintendo (SNES)": "super-nintendo-entertainment-system",
    "Super Nintendo Entertainment System": "super-nintendo-entertainment-system",
    "SNK Neo Geo AES": "snk-neo-geo-aes",
    "Sony PlayStation": "sony-playstation",
    "Sony Playstation 3": "sony-playstation-3",
    "Sony Playstation 4": "sony-playstation-4",
    "Sony Playstation Vita": "sony-playstation-vita",
    "Sony PSP": "sony-psp",
    "Microsoft Xbox": "microsoft-xbox",
    "Microsoft Xbox 360": "microsoft-xbox-360",
}

def get_romspure_subpath_exact(platform_name: str) -> str | None:
    """
    Returns the romspure subpath for the given TheGamesDB platform name.
    If there is no exact match, returns None.
    """
    return ROMSPURE_PLATFORM_MAP.get(platform_name)
