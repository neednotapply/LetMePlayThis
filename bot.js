const { Client, GatewayIntentBits, SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const axios = require('axios');
const cheerio = require('cheerio');
const { token } = require('./config.json');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.MessageContent
    ]
});

// Function to truncate a string to a maximum length
function truncateString(str, maxLen) {
    return str.length > maxLen ? str.slice(0, maxLen - 3) + '...' : str;
}

// Function to scrape MobyGames for game details
async function scrapeMobyGames(query) {
    try {
        // Make a GET request to the MobyGames search page
        const response = await axios.get(`https://www.mobygames.com/search/?q=${encodeURIComponent(query)}&type=game`);
        
        // Load HTML data into Cheerio
        const $ = cheerio.load(response.data);

        // Extract data from the first search result
        const firstSearchResult = {
            coverArt: $('tr:nth-of-type(1) > td:nth-of-type(1) a img').attr('src'),
            gameTitle: $('tr:nth-of-type(1) > td:nth-of-type(2) > b').text().trim(),
            gameLink: $('tr:nth-of-type(1) > td:nth-of-type(2) > b > a').attr('href'),
            releaseDate: $('tr:nth-of-type(1) > td:nth-of-type(2) > span.text-muted').text().trim(),
            alternateTitles: $('tr:nth-of-type(1) > td:nth-of-type(2) > small.text-muted').text().replace('AKA: ', '').trim(),
            platforms: $('tr:nth-of-type(1) > td:nth-of-type(2) > small:nth-of-type(3)').text().trim()
        };

        // If the 'Platforms' field is not found, check the alternate selector
        if (!firstSearchResult.platforms) {
            firstSearchResult.platforms = $('tr:nth-of-type(1) > td:nth-of-type(2) > small:nth-of-type(2)').text().trim();
        }

        // Return the extracted data
        return firstSearchResult;
    } catch (error) {
        console.error('Error scraping MobyGames:', error);
        throw new Error('An error occurred while scraping MobyGames.');
    }
}

// Function to check if a string is a partial match of another string (case insensitive)
function isPartialMatch(str, target) {
    return str.toLowerCase().includes(target.toLowerCase());
}

// Function to scrape GOG-Games for download details
async function scrapeGOGGames(query, mobyGamesTitle, mobyGamesAlternateTitle) {
    try {
        // Make a GET request to the GOG-Games search page
        const response = await axios.get(`https://gog-games.to/search/${encodeURIComponent(query)}`);
        
        // Load HTML data into Cheerio
        const $ = cheerio.load(response.data);

        // Check if there are no search results
        if ($('.fa-frown.fa-8x.far').length > 0) {
            return { downloadLink: null }; // Return null to indicate no results found
        }

        // Extract data from the first search result
        const firstSearchResultTitle = $('a.block:nth-of-type(1) > .info > .title').text();
        if (!isPartialMatch(firstSearchResultTitle, mobyGamesTitle) && !isPartialMatch(firstSearchResultTitle, mobyGamesAlternateTitle)) {
            // If the first search result title is not a partial match with both original and alternate titles, return null
            return { downloadLink: null };
        }

        const firstSearchResult = {
            downloadLink: `https://gog-games.to${$('a.block:nth-of-type(1)').attr('href')}`
        };

        // Return the extracted data
        return firstSearchResult;
    } catch (error) {
        console.error('Error scraping GOG-Games:', error);
        throw new Error('An error occurred while scraping GOG-Games.');
    }
}

// Function to scrape FitGirl Repacks for download details
async function scrapeFitGirlRepacks(query, mobyGamesTitle, mobyGamesAlternateTitle) {
    try {
        // Make a GET request to the FitGirl Repacks search page
        const response = await axios.get(`https://fitgirl-repacks.site/?s=${encodeURIComponent(query)}`);
        
        // Load HTML data into Cheerio
        const $ = cheerio.load(response.data);

        // Extract data from the first search result
        const firstSearchResultTitle = $('.entry-title > a').text().split(':')[0].trim();
        if (!isPartialMatch(firstSearchResultTitle, mobyGamesTitle) && !isPartialMatch(firstSearchResultTitle, mobyGamesAlternateTitle)) {
            // If the first search result title is not a partial match with both original and alternate titles, return null
            return { downloadLink: null };
        }

        const firstSearchResult = {
            downloadLink: $('.entry-title > a').attr('href')
        };

        // Return the extracted data
        return firstSearchResult;
    } catch (error) {
        console.error('Error scraping FitGirl Repacks:', error);
        throw new Error('An error occurred while scraping FitGirl Repacks.');
    }
}

client.once('ready', async () => {
    console.log('Bot is ready!');

    // Register slash commands
    const commands = [
        new SlashCommandBuilder()
            .setName('ping')
            .setDescription('Replies with Pong!'),
        new SlashCommandBuilder()
            .setName('play')
            .setDescription('Searches for a game on MobyGames, GOG-Games, and FitGirl Repacks')
            .addStringOption(option =>
                option.setName('title')
                    .setDescription('Title of the game')
                    .setRequired(true))
    ];

    const commandData = commands.map(command => command.toJSON());
    try {
        await client.application.commands.set(commandData);
        console.log('Slash commands registered successfully!');
    } catch (error) {
        console.error('Error registering slash commands:', error);
    }
});

client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    const { commandName, options } = interaction;

    if (commandName === 'ping') {
        await interaction.reply('Pong!');
    } else if (commandName === 'play') {
        const gameTitle = options.getString('title');
        if (!gameTitle) {
            await interaction.reply('Please provide a game title.');
            return;
        }

        try {
            // Scrape MobyGames for game details
            const mobyGamesDetails = await scrapeMobyGames(gameTitle);

            // Scrape GOG-Games for download details
            const gogGamesDetails = await scrapeGOGGames(gameTitle, mobyGamesDetails.gameTitle, mobyGamesDetails.alternateTitles);

            // Scrape FitGirl Repacks for download details
            const fitGirlRepacksDetails = await scrapeFitGirlRepacks(gameTitle, mobyGamesDetails.gameTitle, mobyGamesDetails.alternateTitles);

            // Construct the embed with game details
            const embed = new EmbedBuilder()
                .setColor(0x0099FF);

            // Add game title as the embed title with a hyperlink
            if (mobyGamesDetails.gameTitle && mobyGamesDetails.gameLink) {
                embed.setTitle(mobyGamesDetails.gameTitle)
                     .setURL(mobyGamesDetails.gameLink);
            }

            // Add cover art as thumbnail if available, otherwise use a placeholder
            embed.setThumbnail(mobyGamesDetails.coverArt || 'https://via.placeholder.com/150');

            // Check if release date is empty before adding it
            if (mobyGamesDetails.releaseDate) {
                embed.addFields(
                    { name: 'Release Date', value: mobyGamesDetails.releaseDate }
                );
            }

            // Check if alternate titles are empty before adding them
            if (mobyGamesDetails.alternateTitles) {
                embed.addFields(
                    { name: 'Alternate Titles', value: mobyGamesDetails.alternateTitles }
                );
            }

            // Check if platforms are empty before adding them
            if (mobyGamesDetails.platforms) {
                // Truncate platforms list to include only the top three platforms
                const platformsArray = mobyGamesDetails.platforms.split(',').map(platform => platform.trim());
                const truncatedPlatforms = platformsArray.slice(0, 3).join(', ');
                const displayPlatforms = `${truncatedPlatforms}${platformsArray.length > 3 ? ' ...' : ''}`;
                embed.addFields(
                    { name: 'Platforms', value: displayPlatforms }
                );
            }

            // Add GOG-Games download link if available
            if (gogGamesDetails.downloadLink) {
                embed.addFields(
                    { name: 'Downloads', value: `[Download from GOG-Games](${gogGamesDetails.downloadLink})` }
                );
            }

            // Add FitGirl Repacks download link if available
            if (fitGirlRepacksDetails.downloadLink) {
                embed.addFields(
                    { name: 'Downloads', value: `[Download from FitGirl Repacks](${fitGirlRepacksDetails.downloadLink})` }
                );
            }

            // Set timestamp and footer
            embed.setTimestamp()
                .setFooter({ text: 'Data from MobyGames, GOG-Games, and FitGirl Repacks' });

            await interaction.reply({ embeds: [embed] });
        } catch (error) {
            console.error('Error fetching game data:', error);
            await interaction.reply('An error occurred while fetching game data.');
        }
    }
});

client.login(token);
