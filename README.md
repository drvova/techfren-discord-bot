# TechFren Discord Bot

A simple Discord bot built with discord.py.

## Features

- Processes queries via mentions (`@botname <query>`) anywhere in messages and responds with AI-generated answers using Perplexity API
- Summarizes channel conversations with `/sum-day` command to get a summary of the day's messages
- Summarizes channel conversations with `/sum-hr <hours>` command to get a summary of the past N hours
- Automatically generates daily summaries for all active channels at a scheduled time
- Stores summaries in a dedicated database table and optionally posts them to a reports channel
- Automatically cleans up old message records after summarization to manage database size
- Automatically splits long messages into multiple parts to handle Discord's 2000 character limit
- Processes URLs shared in messages:
  - Uses Apify to scrape Twitter/X.com URLs, extracting tweet content, video URLs, and replies
  - Uses Firecrawl for all other URLs
  - Summarizes content and stores it in the database
- Rate limiting to prevent abuse (10 seconds between requests, max 6 requests per minute)
- Mention-based queries (e.g., `@botname <query>`) allow you to interact with the bot in any channel, with responses posted in threads attached to your original message. Mentions can appear anywhere in the message (beginning, middle, or end)
- `/sum-day` command works in any channel
- Stores all messages in a SQLite database for logging and analysis

## Setup

1. Clone the repository
2. Ensure you have Python 3.9 or later installed (required for asyncio.to_thread functionality)
3. Create a virtual environment:
   ```
   uv venv
   ```
4. Activate the virtual environment:
   ```
   source .venv/bin/activate  # On Unix/macOS
   .venv\Scripts\activate     # On Windows
   ```
5. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```
5. Configure the bot using environment variables:

   **Option A: Using .env file (Recommended)**
   ```bash
   # Copy the sample environment file
   cp .env.sample .env

   # Edit .env with your actual tokens and keys
   nano .env  # or use your preferred editor
   ```

   **Option B: Set environment variables directly**
   ```bash
   export DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN"
   export PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY"
   export FIRECRAWL_API_KEY="YOUR_FIRECRAWL_API_KEY"
   # ... other variables as needed
   ```

   **Required environment variables:**
   ```bash
   DISCORD_BOT_TOKEN=your_discord_bot_token
   PERPLEXITY_API_KEY=your_perplexity_api_key
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   ```

   **Optional environment variables:**
   ```bash
   LLM_MODEL=sonar  # Default model to use (Perplexity's web search model)
   APIFY_API_TOKEN=your_apify_token  # For Twitter/X.com link processing
   RATE_LIMIT_SECONDS=10  # Time between allowed requests per user
   MAX_REQUESTS_PER_MINUTE=6  # Maximum requests per user per minute
   SUMMARY_HOUR=0  # Hour of the day to run summarization (UTC, 0-23)
   SUMMARY_MINUTE=0  # Minute of the hour to run summarization (0-59)
   REPORTS_CHANNEL_ID=channel_id  # Optional: Channel to post daily summaries
   PERPLEXITY_BASE_URL=https://api.perplexity.ai  # Base URL for Perplexity API
   HTTP_REFERER=https://techfren.net  # HTTP Referer header for API requests
   X_TITLE=TechFren Discord Bot  # X-Title header for API requests
   ```
   - You can get a Perplexity API key by signing up at [Perplexity.ai](https://perplexity.ai/)
   - You can get a Firecrawl API key by signing up at [Firecrawl.dev](https://firecrawl.dev)
   - You can get an Apify API token by signing up at [Apify.com](https://apify.com)
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

- `@botname <query>`: Sends your query to an AI model via Perplexity and returns the response. This command works in any channel and creates a thread attached to your message where the bot's response is posted. The mention can appear anywhere in your message (e.g., "Hey everyone, @botname can you help with this?").

### Channel Summarization

- `/sum-day`: Summarizes all messages in the current channel for the current day
  - Works in any channel (not restricted to #bot-talk)
  - The bot retrieves all messages from the channel (including bot responses) except command messages
  - Sends them to the AI model for summarization
  - Returns a formatted summary with the main topics and key points discussed
  - Creates an efficient thread: the initial message is edited with the summary content and a thread is created from it
  - Additional summary parts (if content exceeds Discord's character limit) are posted within the thread

- `/sum-hr <hours>`: Summarizes all messages in the current channel for the past N hours
  - Usage: `/sum-hr 6` (summarizes past 6 hours), `/sum-hr 12` (summarizes past 12 hours)
  - Works in any channel (not restricted to #bot-talk)
  - Flexible time range allows for more granular summaries than daily summaries
  - Creates an efficient thread with an appropriate name (e.g., "Summary - channel-name - 2025-05-30")
  - Same formatting and thread creation features as `/sum-day` command

### Automated Daily Summarization

The bot automatically generates summaries for all active channels once per day:

- Runs at a configurable time (default: midnight UTC)
- Summarizes messages from the past 24 hours for each active channel
- Stores summaries in a dedicated database table with metadata including:
  - Channel information
  - Message count
  - Active users
  - Date
  - Summary text
- Optionally posts summaries to a designated reports channel
- Deletes messages older than 24 hours after successful summarization to manage database size

To configure the automated summarization:

```bash
# In .env file or environment variables
SUMMARY_HOUR=0  # Hour of the day to run summarization (UTC, 0-23)
SUMMARY_MINUTE=0  # Minute of the hour to run summarization (0-59)
REPORTS_CHANNEL_ID=CHANNEL_ID  # Optional: Channel to post daily summaries
```

## Database

The bot uses a SQLite database located in the `data/` directory with the following tables:

### Messages Table
Stores all messages processed by the bot, including:
- User messages
- Bot responses to commands
- Error messages
- Rate limit notifications

Each message is stored with metadata including author information, timestamps, and whether it's a command or bot response.

The messages table also includes fields for URL scraping functionality:
- `scraped_url`: URL extracted from the message
- `scraped_content_summary`: Summary of the content from the scraped URL
- `scraped_content_key_points`: Key points extracted from the scraped content

### Channel Summaries Table
Stores the daily automated summaries for each channel, including:
- Channel information (ID, name, guild)
- Date of the summary
- Summary text
- Message count
- Active users count and list
- Metadata (start/end times, summary type)

This comprehensive database structure allows for:

- Complete conversation history tracking
- User activity analysis
- Command usage statistics
- Channel summarization functionality
- Historical summary access
- Debugging and troubleshooting

The database is initialized when the bot starts up and is used throughout the application to store and retrieve messages and summaries.

### Database Migration

If you encounter database schema-related errors, you may need to run the database migration script:

```bash
python db_migration.py
```

This script will add any missing columns to the database tables that might have been added in newer versions of the bot.

### Database Utilities

You can use the `db_utils.py` script to interact with the database:

```bash
# List recent messages
python db_utils.py list -n 20

# Show message statistics
python db_utils.py stats

# List channel summaries
python db_utils.py summaries -n 10

# Filter summaries by channel name
python db_utils.py summaries -c general

# Filter summaries by date
python db_utils.py summaries -d 2023-05-30

# View a specific summary in full
python db_utils.py view-summary 1
```

### Troubleshooting

If you encounter database-related errors:

1. Make sure the `data/` directory exists and is writable
2. Check that the database is properly initialized in the `on_ready` event
3. Avoid importing the database module multiple times in different scopes
4. Check the logs for detailed error messages

## Changelog

### 2025-06-25
- **Enhanced Mention Detection**: Bot now responds to mentions anywhere in messages, not just at the beginning
  - **Flexible Positioning**: Mentions can appear at the start, middle, or end of messages (e.g., "Hey everyone, @botname can you help?")
  - **Backward Compatible**: Existing mention patterns continue to work as before
  - **Improved User Experience**: More natural conversation flow when mentioning the bot in context
  - **Added Test Coverage**: New test case to verify mention detection in middle of messages

### 2025-01-27
- **Thread-based replies for mention commands**: Bot responses to `@botname <query>` commands are now posted in threads attached to the user's original message
- **Removed channel restrictions**: All mention commands now work in any channel without restrictions
- **Improved user experience**: Bot responses are organized in threads, keeping main channels cleaner
- **Maintained existing functionality**: Message storage, character limit handling, and user mention protections continue to work as expected

### 2025-05-30
- **Thread Optimization**: Improved summary command efficiency and user experience
  - **Clean Channel View**: Main message shows only a title (e.g., "Summary of #channel for the past 24 hours")
  - **Content in Thread**: All summary content is posted within the thread to keep channels uncluttered
  - **Unified Approach**: Both message-based (`/sum-day` typed) and slash commands work identically
  - **Guild Info Fix**: Automatically fetch messages with proper guild information when needed for thread creation
  - **Smart Fallback**: If thread creation fails, summary content is included in the main message
  - Reduced visual clutter while maintaining full functionality

### 2025-01-25
- **Documentation Update**: Added missing `/sum-hr <hours>` command documentation to README
- **Code Cleanup**: Removed unused imports from bot.py (time, sqlite3, json, collections.defaultdict)
- **Code Cleanup**: Fixed duplicate comments in config.py
- **Code Cleanup**: Removed unreachable code in command processing logic
- **Feature Clarification**: The `/sum-hr` command was already implemented but not documented

### 2025-05-21
- Added Apify integration for Twitter/X.com URL processing:
  - Uses Apify API to fetch tweet content and replies
  - Extracts video URLs from tweets when available
  - Falls back to Firecrawl if Apify is not configured or fails
- Added database migration script to handle schema updates
- Added URL scraping functionality with new database columns:
  - `scraped_url`
  - `scraped_content_summary`
  - `scraped_content_key_points`
- Fixed issue with missing columns in the messages table

### 2023-05-30
- Added automated daily channel summarization feature
- Created a new channel_summaries table in the database
- Implemented scheduled task to run summarization at a configurable time
- Added functionality to delete old messages after summarization
- Added optional feature to post summaries to a designated reports channel
- Updated documentation with new configuration options

### 2023-05-25
- Modified the `/sum-day` command to work in any channel
- Mention-based queries (`@botname <query>`) are available in all channels with thread-based responses
- Updated documentation to reflect these changes

### 2023-05-20
- Removed the `$hello` command feature
- Simplified command handling in the bot

### 2023-05-15
- Fixed issue where bot responses to mention-based queries (`@botname <query>`) were not being stored in the database
- Now storing all bot responses in the database, including error messages and rate limit notifications
- Modified `/sum-day` command to include bot responses in the summary
- Improved error handling and logging for database operations

### 2023-05-10
- Added message splitting functionality to handle responses that exceed Discord's 2000 character limit
- Fixed an `UnboundLocalError` in the `/sum-day` command that was causing database access issues
- Improved error handling for database operations
- Added additional database troubleshooting information to the README

## License

MIT
