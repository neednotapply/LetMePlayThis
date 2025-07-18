# Installation Instructions
Create a new application at https://discord.com/developers/applications  

### General Information
Add a Name and App Icon.  
If you intend to make the bot public, upload the ToS and Privacy Policy to `https://gist.github.com/` or `https://pastebin.com/` and update the URLs appropriately.

### Installation
Take note of your installation link, this is how you can add your bot to a server.  
The bot requires the following SCOPES: `applications.commands` `bot`  
The bot requires the following Permissions: `Embed Links` `Send Messages`

### Oauth2
This section can be ignored.

### Bot
Add the Banner and make any necessary adjustments to the Name / Icon.  
Take note of your `Token`, you will need it later. Do not share this with anyone.  
Ensure that `Message Content Intent` is enabled.  
If you intend to make the bot public, ensure that `Public Bot` is enabled.

## MobyGames API
This bot uses the MobyGames API to fetch information on media.  
You need an API key which you can acquire for free here `https://www.mobygames.com/info/api/#how-to-get-access`

## Config.json
Either clone the repository or download as a zip.  
Open `config.json` and enter your Bot Token, Guild ID, MobyGames API Key, and Owner ID (Discord name).
Optionally set `emulatorJsBaseUrl` to the base URL of your EmulatorJS server if you want **Play Now** links.

## Bot.js
Download and Install Node.js  
Ensure you have the prerequisite packages installed from NPM: `npm install discord.js axios cheerio`  
Navigate to your installation directory and open a terminal, run the bot with `node bot.js`  

Enjoy 👍

## Myrient Index and Download Tips
This bot can use the open directory at [Myrient](https://myrient.erista.me/) to fetch download links. Because the site does not provide search, run `scripts/update_myrient_index.py` to build a local index of all files. The script crawls the site using Python and requires network access. The generated file is stored at `data/myrient_index.txt`.
If a crawl is interrupted, rerunning the script will prompt you to resume from the last saved location or start over. If the index file ends up empty (e.g., due to an interrupted crawl), delete it and run the script again so Myrient links appear correctly.

Large files can be downloaded with any of the managers recommended on Myrient's wiki:

- DownThemAll (recommended)
- JDownloader or Motrix
- aria2 or wget
- Searches restrict matches to the exact console directory to avoid cross-platform results
- Common aliases like "PS2" or "N64" are recognized automatically
- N64 titles are stored in the "BigEndian" set and GameCube uses the NKit RVZ collection
- If a game spans multiple discs, download links for each disc are returned

## EmulatorJS Play-Now
To enable the optional **Play Now** links, export your EmulatorJS system config files and place them next to `scripts/update_emulatorjs_index.py` (or pass the directory as an argument). Run `scripts/update_emulatorjs_index.py` to create `data/emulatorjs_index.json`.
Add an `emulatorJsBaseUrl` entry to `config.json` pointing at your server (for example `http://blackbox:81/#`).
When the value is blank, Play Now links are disabled. When set and a matching title is found, the bot includes a **Play Now** link in the embed.
