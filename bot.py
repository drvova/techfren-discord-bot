# This example requires the 'message_content' intent.

import discord
import logging
import os
from datetime import datetime

# Set up logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Create a unique log file name with timestamp
log_filename = f"{log_directory}/bot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('discord_bot')

# Using message_content intent (requires enabling in the Discord Developer Portal)
intents = discord.Intents.default()
intents.message_content = True  # This is required to read message content in guild channels

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f'Bot has successfully connected as {client.user}')
    logger.info(f'Bot ID: {client.user.id}')
    logger.info(f'Connected to {len(client.guilds)} guilds')

    # Log details about each connected guild
    for guild in client.guilds:
        logger.info(f'Connected to guild: {guild.name} (ID: {guild.id}) - {len(guild.members)} members')
        # Check if bot-talk channel exists
        bot_talk_exists = any(channel.name == 'bot-talk' for channel in guild.text_channels)
        if not bot_talk_exists:
            logger.warning(f'Guild {guild.name} does not have a #bot-talk channel. Bot will not respond to any messages in this guild.')

@client.event
async def on_guild_join(guild):
    """Log when the bot joins a new guild"""
    logger.info(f'Bot joined new guild: {guild.name} (ID: {guild.id}) - {len(guild.members)} members')
    # Check if bot-talk channel exists
    bot_talk_exists = any(channel.name == 'bot-talk' for channel in guild.text_channels)
    if not bot_talk_exists:
        logger.warning(f'Guild {guild.name} does not have a #bot-talk channel. Bot will not respond to any messages in this guild.')

@client.event
async def on_guild_remove(guild):
    """Log when the bot is removed from a guild"""
    logger.info(f'Bot removed from guild: {guild.name} (ID: {guild.id})')

@client.event
async def on_error(event, *args, **kwargs):
    """Log Discord API errors"""
    logger.error(f'Discord error in {event}', exc_info=True)
    # Log additional context if available
    if args:
        logger.error(f'Error context args: {args}')
    if kwargs:
        logger.error(f'Error context kwargs: {kwargs}')

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Log message details
    guild_name = message.guild.name if message.guild else "DM"
    channel_name = message.channel.name if hasattr(message.channel, 'name') else "Direct Message"
    logger.info(f"Message received - Guild: {guild_name} | Channel: {channel_name} | Author: {message.author} | Content: {message.content[:50]}{'...' if len(message.content) > 50 else ''}")

    # Only respond in the #bot-talk channel
    if hasattr(message.channel, 'name') and message.channel.name != 'bot-talk':
        logger.debug(f"Ignoring message in channel #{message.channel.name} - bot only responds in #bot-talk")
        return

    # Process commands
    try:
        if message.content.startswith('$hello'):
            logger.info(f"Executing command: $hello - Requested by {message.author}")
            await message.channel.send('Hello!')
            logger.info(f"Command executed successfully: $hello")
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # Optionally notify about the error in the channel
        # await message.channel.send("Sorry, an error occurred while processing your command.")

try:
    logger.info("Starting bot...")
    import config

    # Check if token exists and is valid
    if not hasattr(config, 'token') or not config.token:
        logger.error("Token not found in config.py or is empty")
        raise ValueError("Bot token is missing or empty")

    # Log startup (but mask the actual token)
    token_preview = config.token[:5] + "..." + config.token[-5:] if len(config.token) > 10 else "***masked***"
    logger.info(f"Bot token loaded: {token_preview}")
    logger.info("Connecting to Discord...")

    # Run the bot
    client.run(config.token)
except ImportError:
    logger.critical("Config file not found or token not defined", exc_info=True)
    logger.error("Please create a config.py file with your Discord bot token.")
    logger.error("Example: token = 'YOUR_DISCORD_BOT_TOKEN'")
except discord.LoginFailure:
    logger.critical("Invalid Discord token. Please check your token in config.py", exc_info=True)
except Exception as e:
    logger.critical(f"Unexpected error during bot startup: {e}", exc_info=True)