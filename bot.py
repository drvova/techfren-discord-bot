# This example requires the 'message_content' intent.

import discord

# Option 1: Use default intents without message_content (if you don't want to enable it in the portal)
intents = discord.Intents.default()

# Option 2: Use message_content intent (requires enabling in the Discord Developer Portal)
# intents = discord.Intents.default()
# intents.message_content = True  # Comment this line if using Option 1

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Note: Without message_content intent, the bot can only see message content in DMs
    # For guild messages, you'll need to enable message_content intent in the Discord Developer Portal
    try:
        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')
    except Exception as e:
        print(f"Error processing message: {e}")

try:
    import config
    client.run(config.token)
except ImportError:
    print("Error: config.py file not found or token not defined.")
    print("Please create a config.py file with your Discord bot token.")
    print("Example: token = 'YOUR_DISCORD_BOT_TOKEN'")
except Exception as e:
    print(f"Error: {e}")