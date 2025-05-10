# TechFren Discord Bot

A simple Discord bot built with discord.py.

## Features

- Responds to `$hello` command with a greeting
- Processes `/bot <query>` commands and responds with AI-generated answers using OpenRouter API
- Summarizes channel conversations with `/sum-day` command to get a summary of the day's messages
- Rate limiting to prevent abuse (10 seconds between requests, max 6 requests per minute)
- Only responds in the #bot-talk channel
- Stores all messages in a SQLite database for logging and analysis

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   uv venv
   ```
3. Activate the virtual environment:
   ```
   source .venv/bin/activate  # On Unix/macOS
   .venv\Scripts\activate     # On Windows
   ```
4. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```
5. Create a `config.py` file with your Discord bot token and OpenRouter API key:
   ```python
   token = "YOUR_DISCORD_BOT_TOKEN"
   openrouter = "YOUR_OPENROUTER_API_KEY"
   ```
   You can get an OpenRouter API key by signing up at [OpenRouter.ai](https://openrouter.ai/)
6. Run the bot:
   ```
   python bot.py
   ```

## Discord Developer Portal Setup

To use the message content intent, you need to enable it in the Discord Developer Portal:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications/)
2. Select your application/bot
3. Navigate to the "Bot" tab
4. Scroll down to the "Privileged Gateway Intents" section
5. Enable the "Message Content Intent"
6. Save your changes
7. Uncomment the message_content intent in the bot.py file

## Commands

### Basic Commands

- `$hello`: A simple greeting command that responds with "Hello!"
- `/bot <query>`: Sends your query to an AI model via OpenRouter and returns the response

### Channel Summarization

- `/sum-day`: Summarizes all messages in the current channel for the current day
  - The bot retrieves all non-bot, non-command messages from the channel
  - Sends them to the AI model for summarization
  - Returns a formatted summary with the main topics and key points discussed

## Database

The bot stores all messages in a SQLite database located in the `data/` directory. This allows for:

- Message history tracking
- User activity analysis
- Command usage statistics
- Channel summarization functionality

### Database Utilities

You can use the `db_utils.py` script to interact with the database:

```bash
# List recent messages
python db_utils.py list -n 20

# Show message statistics
python db_utils.py stats
```

## License

MIT
