"""
Database module for the Discord bot.
Handles SQLite database operations for storing messages and channel summaries.
"""

import sqlite3
import os
import logging
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

# Set up logging
logger = logging.getLogger('discord_bot.database')

# Database constants
DB_DIRECTORY = "data"
DB_FILE = os.path.join(DB_DIRECTORY, "discord_messages.db")

# SQL statements
CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    author_id TEXT NOT NULL,
    author_name TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    guild_id TEXT,
    guild_name TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    is_bot INTEGER NOT NULL,
    is_command INTEGER NOT NULL,
    command_type TEXT,
    scraped_url TEXT,
    scraped_content_summary TEXT,
    scraped_content_key_points TEXT
);
"""

CREATE_CHANNEL_SUMMARIES_TABLE = """
CREATE TABLE IF NOT EXISTS channel_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    guild_id TEXT,
    guild_name TEXT,
    date TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    active_users INTEGER NOT NULL,
    active_users_list TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    metadata TEXT
);
"""

CREATE_INDEX_AUTHOR = "CREATE INDEX IF NOT EXISTS idx_author_id ON messages (author_id);"
CREATE_INDEX_CHANNEL = "CREATE INDEX IF NOT EXISTS idx_channel_id ON messages (channel_id);"
CREATE_INDEX_GUILD = "CREATE INDEX IF NOT EXISTS idx_guild_id ON messages (guild_id);"
CREATE_INDEX_CREATED = "CREATE INDEX IF NOT EXISTS idx_created_at ON messages (created_at);"
CREATE_INDEX_COMMAND = "CREATE INDEX IF NOT EXISTS idx_is_command ON messages (is_command);"
CREATE_INDEX_SUMMARY_CHANNEL = "CREATE INDEX IF NOT EXISTS idx_summary_channel_id ON channel_summaries (channel_id);"
CREATE_INDEX_SUMMARY_DATE = "CREATE INDEX IF NOT EXISTS idx_summary_date ON channel_summaries (date);"

INSERT_MESSAGE = """
INSERT INTO messages (
    id, author_id, author_name, channel_id, channel_name,
    guild_id, guild_name, content, created_at, is_bot, is_command, command_type,
    scraped_url, scraped_content_summary, scraped_content_key_points
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

INSERT_CHANNEL_SUMMARY = """
INSERT INTO channel_summaries (
    channel_id, channel_name, guild_id, guild_name, date,
    summary_text, message_count, active_users, active_users_list,
    created_at, metadata
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

def init_database() -> None:
    """
    Initialize the database by creating the necessary directory and tables.
    """
    try:
        # Create the data directory if it doesn't exist
        if not os.path.exists(DB_DIRECTORY):
            os.makedirs(DB_DIRECTORY)
            logger.info(f"Created database directory: {DB_DIRECTORY}")

        # Connect to the database and create tables using context manager
        with sqlite3.connect(DB_FILE) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Set a shorter timeout for better error reporting
            conn.execute("PRAGMA busy_timeout = 5000")  # 5 seconds

            cursor = conn.cursor()

            # Create tables and indexes
            cursor.execute(CREATE_MESSAGES_TABLE)
            cursor.execute(CREATE_CHANNEL_SUMMARIES_TABLE)

            # Create indexes for messages table
            cursor.execute(CREATE_INDEX_AUTHOR)
            cursor.execute(CREATE_INDEX_CHANNEL)
            cursor.execute(CREATE_INDEX_GUILD)
            cursor.execute(CREATE_INDEX_CREATED)
            cursor.execute(CREATE_INDEX_COMMAND)

            # Create indexes for channel_summaries table
            cursor.execute(CREATE_INDEX_SUMMARY_CHANNEL)
            cursor.execute(CREATE_INDEX_SUMMARY_DATE)

            # Insert a test message to ensure the database is working
            try:
                test_message_id = f"test-init-{datetime.now().timestamp()}"
                cursor.execute(
                    INSERT_MESSAGE,
                    (
                        test_message_id,
                        "system",
                        "System",
                        "system",
                        "System",
                        None,
                        None,
                        "Database initialization test message",
                        datetime.now().isoformat(),
                        1,  # is_bot
                        0,  # is_command
                        None,
                        None,
                        None,
                        None
                    )
                )
                logger.info("Successfully inserted test message during database initialization")
            except sqlite3.IntegrityError:
                # This is fine, it means the test message already exists
                logger.info("Test message already exists in database")
            except Exception as e:
                logger.warning(f"Failed to insert test message during initialization: {str(e)}")

            conn.commit()

        logger.info(f"Database initialized successfully at {DB_FILE}")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

def get_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    The connection supports context managers (with statements).

    Returns:
        sqlite3.Connection: A connection to the database.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # This enables column access by name

        # Set a shorter timeout for better error reporting
        conn.execute("PRAGMA busy_timeout = 5000")  # 5 seconds

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
        raise

def check_database_connection() -> bool:
    """
    Check if the database connection is working properly.

    Returns:
        bool: True if the connection is working, False otherwise
    """
    try:
        # First check if the database file exists
        if not os.path.exists(DB_FILE):
            logger.error(f"Database file does not exist: {DB_FILE}")
            return False

        # Check if the file is readable and writable
        if not os.access(DB_FILE, os.R_OK | os.W_OK):
            logger.error(f"Database file is not readable or writable: {DB_FILE}")
            return False

        # Check the file size
        file_size = os.path.getsize(DB_FILE)
        logger.info(f"Database file size: {file_size} bytes")

        # Try to connect and execute a simple query
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            # Check if the messages table exists and has the expected schema
            cursor.execute("PRAGMA table_info(messages)")
            columns = cursor.fetchall()
            if not columns:
                logger.error("Messages table does not exist in the database")
                return False

            # Log the schema
            column_names = [col['name'] for col in columns]
            logger.info(f"Messages table columns: {', '.join(column_names)}")

            return result is not None and result[0] == 1
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}", exc_info=True)
        return False

def store_message(
    message_id: str,
    author_id: str,
    author_name: str,
    channel_id: str,
    channel_name: str,
    content: str,
    created_at: datetime,
    guild_id: Optional[str] = None,
    guild_name: Optional[str] = None,
    is_bot: bool = False,
    is_command: bool = False,
    command_type: Optional[str] = None,
    scraped_url: Optional[str] = None,
    scraped_content_summary: Optional[str] = None,
    scraped_content_key_points: Optional[str] = None
) -> bool:
    """
    Store a message in the database.

    Args:
        message_id (str): The Discord message ID
        author_id (str): The Discord user ID of the message author
        author_name (str): The username of the message author
        channel_id (str): The Discord channel ID where the message was sent
        channel_name (str): The name of the channel where the message was sent
        content (str): The content of the message
        created_at (datetime): The timestamp when the message was created
        guild_id (Optional[str]): The Discord guild ID (if applicable)
        guild_name (Optional[str]): The name of the guild (if applicable)
        is_bot (bool): Whether the message was sent by a bot
        is_command (bool): Whether the message is a command
        command_type (Optional[str]): The type of command (if applicable)
        scraped_url (Optional[str]): The URL that was scraped from the message (if any)
        scraped_content_summary (Optional[str]): Summary of the scraped content (if any)
        scraped_content_key_points (Optional[str]): JSON string of key points from scraped content (if any)

    Returns:
        bool: True if the message was stored successfully, False otherwise
    """
    try:
        # Use context manager to ensure connection is properly closed
        with get_connection() as conn:
            cursor = conn.cursor()

# Ensure consistent datetime format for storage (always UTC, no timezone info for SQLite compatibility)
            created_at_str = created_at.replace(tzinfo=None).isoformat()
            
            cursor.execute(
                INSERT_MESSAGE,
                (
                    message_id,
                    author_id,
                    author_name,
                    channel_id,
                    channel_name,
                    guild_id,
                    guild_name,
                    content,
                    created_at_str,
                    1 if is_bot else 0,
                    1 if is_command else 0,
                    command_type,
                    scraped_url,
                    scraped_content_summary,
                    scraped_content_key_points
                )
            )

            conn.commit()

        logger.debug(f"Message {message_id} stored in database")
        return True
    except sqlite3.IntegrityError:
        # This could happen if we try to insert a message with the same ID twice
        # This is normal when the bot restarts and processes recent messages
        logger.debug(f"Message {message_id} already exists in database (skipping duplicate)")
        return False
    except Exception as e:
        logger.error(f"Error storing message {message_id}: {str(e)}", exc_info=True)
        return False

async def store_messages_batch(messages: List[Dict[str, Any]]) -> bool:
    """
    Store multiple messages in a single transaction for better performance and consistency.

    Args:
        messages (List[Dict[str, Any]]): List of message dictionaries with required fields

    Returns:
        bool: True if all messages were stored successfully, False otherwise
    """
    if not messages:
        return True
        
    try:
        def _store_batch():
            with get_connection() as conn:
                cursor = conn.cursor()
                
                for msg in messages:
                    # Ensure consistent datetime format for storage (always UTC, no timezone info for SQLite compatibility)
                    created_at = msg['created_at']
                    created_at_str = created_at.replace(tzinfo=None).isoformat()
                    
                    cursor.execute(
                        INSERT_MESSAGE,
                        (
                            msg['message_id'],
                            msg['author_id'],
                            msg['author_name'],
                            msg['channel_id'],
                            msg['channel_name'],
                            msg.get('guild_id'),
                            msg.get('guild_name'),
                            msg['content'],
                            created_at_str,
                            int(msg.get('is_bot', False)),
                            int(msg.get('is_command', False)),
                            msg.get('command_type'),
                            msg.get('scraped_url'),
                            msg.get('scraped_content_summary'),
                            msg.get('scraped_content_key_points')
                        )
                    )
                
                conn.commit()
                return True

        result = await asyncio.to_thread(_store_batch)
        logger.info(f"Stored {len(messages)} messages in batch transaction")
        return result
    except sqlite3.IntegrityError as e:
        logger.warning(f"Integrity error in batch message storage: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error storing message batch: {str(e)}", exc_info=True)
        return False

async def update_message_with_scraped_data(
    message_id: str,
    scraped_url: str,
    scraped_content_summary: str,
    scraped_content_key_points: str
) -> bool:
    """
    Update an existing message with scraped URL data.

    Args:
        message_id (str): The Discord message ID to update
        scraped_url (str): The URL that was scraped
        scraped_content_summary (str): Summary of the scraped content
        scraped_content_key_points (str): JSON string of key points from scraped content

    Returns:
        bool: True if the message was updated successfully, False otherwise
    """
    try:
        # Define a synchronous function to run in a thread pool
        def _update_message_sync():
            with get_connection() as conn:
                cursor = conn.cursor()

                # Update the message with scraped data
                cursor.execute(
                    """
                    UPDATE messages
                    SET scraped_url = ?,
                        scraped_content_summary = ?,
                        scraped_content_key_points = ?
                    WHERE id = ?
                    """,
                    (
                        scraped_url,
                        scraped_content_summary,
                        scraped_content_key_points,
                        message_id
                    )
                )

                # Check if any rows were affected
                rows_affected = cursor.rowcount == 0
                conn.commit()
                return rows_affected

        # Run the synchronous function in a thread pool to avoid blocking the event loop
        no_rows_affected = await asyncio.to_thread(_update_message_sync)

        if no_rows_affected:
            logger.warning(f"No message found with ID {message_id} to update with scraped data")
            return False

        logger.info(f"Message {message_id} updated with scraped data from URL: {scraped_url}")
        return True
    except Exception as e:
        logger.error(f"Error updating message {message_id} with scraped data: {str(e)}", exc_info=True)
        return False

def get_message_count() -> int:
    """
    Get the total number of messages in the database.

    Returns:
        int: The number of messages
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]

        return count
    except Exception as e:
        logger.error(f"Error getting message count: {str(e)}", exc_info=True)
        # Return 0 instead of -1 for consistency with other error cases
        return 0

def get_user_message_count(user_id: str) -> int:
    """
    Get the number of messages from a specific user.

    Args:
        user_id (str): The Discord user ID

    Returns:
        int: The number of messages from the user
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM messages WHERE author_id = ?", (user_id,))
            count = cursor.fetchone()[0]

        return count
    except Exception as e:
        logger.error(f"Error getting message count for user {user_id}: {str(e)}", exc_info=True)
        # Return 0 instead of -1 for consistency with other error cases
        return 0

def get_all_channel_messages(channel_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all messages from a specific channel, regardless of date.

    Args:
        channel_id (str): The Discord channel ID
        limit (int): Maximum number of messages to return

    Returns:
        List[Dict[str, Any]]: A list of messages as dictionaries
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Query all messages for the channel
            cursor.execute(
                """
                SELECT author_name, content, created_at, is_bot, is_command,
                       scraped_url, scraped_content_summary, scraped_content_key_points
                FROM messages
                WHERE channel_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (channel_id, limit)
            )

            # Convert rows to dictionaries
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'author_name': row['author_name'],
                    'content': row['content'],
                    'created_at': datetime.fromisoformat(row['created_at']),
                    'is_bot': bool(row['is_bot']),
                    'is_command': bool(row['is_command']),
                    'scraped_url': row['scraped_url'],
                    'scraped_content_summary': row['scraped_content_summary'],
                    'scraped_content_key_points': row['scraped_content_key_points']
                })

        logger.info(f"Retrieved {len(messages)} messages from channel {channel_id} (all time)")
        return messages
    except Exception as e:
        logger.error(f"Error getting all messages for channel {channel_id}: {str(e)}", exc_info=True)
        return []

def get_channel_messages_for_day(channel_id: str, date: datetime) -> List[Dict[str, Any]]:
    """
    Get all messages from a specific channel for the past 24 hours from the given date.

    Args:
        channel_id (str): The Discord channel ID
        date (datetime): The reference date (will get messages for 24 hours before this date)

    Returns:
        List[Dict[str, Any]]: A list of messages as dictionaries
    """
    return get_channel_messages_for_hours(channel_id, date, 24)

def get_channel_messages_for_hours(channel_id: str, date: datetime, hours: int) -> List[Dict[str, Any]]:
    """
    Get all messages from a specific channel for the past specified hours from the given date.

    Args:
        channel_id (str): The Discord channel ID
        date (datetime): The reference date (will get messages for specified hours before this date)
        hours (int): Number of hours to look back

    Returns:
        List[Dict[str, Any]]: A list of messages as dictionaries
    """
    try:
        # Ensure we're working with UTC timezone
        if date.tzinfo is None:
            # If naive datetime, assume it's UTC
            date = date.replace(tzinfo=timezone.utc)
        elif date.tzinfo != timezone.utc:
            # Convert to UTC if it's in a different timezone
            date = date.astimezone(timezone.utc)

        # Calculate the time range for the past specified hours
        # Add a small buffer (1 minute) to ensure we capture very recent messages
        end_date = date + timedelta(minutes=1)
        start_date = date - timedelta(hours=hours)

        # Convert to ISO format for database query (remove timezone info for SQLite compatibility)
        # For SQLite, we need to handle timezone-aware datetime strings properly
        start_date_str = start_date.replace(tzinfo=None).isoformat()
        end_date_str = end_date.replace(tzinfo=None).isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Query messages for the channel within the time range
            # Use datetime comparison that works with SQLite's text storage
            # Handle both timezone-aware and naive datetime strings in the database
            cursor.execute(
                """
                SELECT id, author_name, content, created_at, is_bot, is_command,
                       scraped_url, scraped_content_summary, scraped_content_key_points,
                       guild_id
                FROM messages
                WHERE channel_id = ? 
                AND (
                    datetime(created_at) BETWEEN datetime(?) AND datetime(?)
                    OR datetime(substr(created_at, 1, 19)) BETWEEN datetime(?) AND datetime(?)
                )
                ORDER BY created_at ASC
                """,
                (channel_id, start_date_str, end_date_str, start_date_str, end_date_str)
            )

            # Convert rows to dictionaries
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row['id'],
                    'author_name': row['author_name'],
                    'content': row['content'],
                    'created_at': datetime.fromisoformat(row['created_at']),
                    'is_bot': bool(row['is_bot']),
                    'is_command': bool(row['is_command']),
                    'scraped_url': row['scraped_url'],
                    'scraped_content_summary': row['scraped_content_summary'],
                    'scraped_content_key_points': row['scraped_content_key_points'],
                    'guild_id': row['guild_id'],
                    'channel_id': channel_id
                })

        logger.info(f"Retrieved {len(messages)} messages from channel {channel_id} for the past {hours} hours from {start_date.isoformat()} to {end_date.isoformat()}")
        return messages
    except Exception as e:
        logger.error(f"Error getting messages for channel {channel_id} for the past {hours} hours from {date.isoformat()}: {str(e)}", exc_info=True)
        return []

def get_messages_for_time_range(start_time: datetime, end_time: datetime) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all messages from all channels within a specific time range, grouped by channel.

    Args:
        start_time (datetime): The start time for the range
        end_time (datetime): The end time for the range

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary mapping channel_id to a list of messages
    """
    try:
        start_date_str = start_time.isoformat()
        end_date_str = end_time.isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Query messages within the time range
            cursor.execute(
                """
                SELECT
                    id, author_id, author_name, channel_id, channel_name,
                    guild_id, guild_name, content, created_at, is_bot, is_command
                FROM messages
                WHERE created_at BETWEEN ? AND ?
                ORDER BY channel_id, created_at ASC
                """,
                (start_date_str, end_date_str)
            )

            # Group messages by channel
            messages_by_channel = {}
            for row in cursor.fetchall():
                channel_id = row['channel_id']

                if channel_id not in messages_by_channel:
                    messages_by_channel[channel_id] = {
                        'channel_id': channel_id,
                        'channel_name': row['channel_name'],
                        'guild_id': row['guild_id'],
                        'guild_name': row['guild_name'],
                        'messages': []
                    }

                messages_by_channel[channel_id]['messages'].append({
                    'id': row['id'],
                    'author_id': row['author_id'],
                    'author_name': row['author_name'],
                    'content': row['content'],
                    'created_at': datetime.fromisoformat(row['created_at']),
                    'is_bot': bool(row['is_bot']),
                    'is_command': bool(row['is_command'])
                })

        total_messages = sum(len(channel_data['messages']) for channel_data in messages_by_channel.values())
        logger.info(f"Retrieved {total_messages} messages from {len(messages_by_channel)} channels between {start_time} and {end_time}")
        return messages_by_channel
    except Exception as e:
        logger.error(f"Error getting messages between {start_time} and {end_time}: {str(e)}", exc_info=True)
        return {}

def store_channel_summary(
    channel_id: str,
    channel_name: str,
    date: datetime,
    summary_text: str,
    message_count: int,
    active_users: List[str],
    guild_id: Optional[str] = None,
    guild_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Store a channel summary in the database.

    Args:
        channel_id (str): The Discord channel ID
        channel_name (str): The name of the channel
        date (datetime): The date of the summary
        summary_text (str): The summary text
        message_count (int): The number of messages summarized
        active_users (List[str]): List of active user names
        guild_id (Optional[str]): The Discord guild ID (if applicable)
        guild_name (Optional[str]): The name of the guild (if applicable)
        metadata (Optional[Dict[str, Any]]): Additional metadata for the summary

    Returns:
        bool: True if the summary was stored successfully, False otherwise
    """
    try:
        # Convert active_users list to JSON string
        active_users_json = json.dumps(active_users)

        # Convert metadata to JSON string if provided
        metadata_json = json.dumps(metadata) if metadata else None

        # Format date as YYYY-MM-DD
        date_str = date.strftime('%Y-%m-%d')

        # Current timestamp
        created_at = datetime.now().isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                INSERT_CHANNEL_SUMMARY,
                (
                    channel_id,
                    channel_name,
                    guild_id,
                    guild_name,
                    date_str,
                    summary_text,
                    message_count,
                    len(active_users),
                    active_users_json,
                    created_at,
                    metadata_json
                )
            )

            conn.commit()

        logger.info(f"Stored summary for channel {channel_name} ({channel_id}) for {date_str}")
        return True
    except Exception as e:
        logger.error(f"Error storing summary for channel {channel_id} on {date.strftime('%Y-%m-%d')}: {str(e)}", exc_info=True)
        return False

def delete_messages_older_than(cutoff_time: datetime) -> int:
    """
    Delete messages older than the specified cutoff time.

    Args:
        cutoff_time (datetime): Messages older than this time will be deleted

    Returns:
        int: The number of messages deleted
    """
    try:
        cutoff_time_str = cutoff_time.isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()

            # First, count how many messages will be deleted
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE created_at < ?",
                (cutoff_time_str,)
            )
            count = cursor.fetchone()[0]

            # Then delete them
            cursor.execute(
                "DELETE FROM messages WHERE created_at < ?",
                (cutoff_time_str,)
            )

            conn.commit()

        logger.info(f"Deleted {count} messages older than {cutoff_time}")
        return count
    except Exception as e:
        logger.error(f"Error deleting messages older than {cutoff_time}: {str(e)}", exc_info=True)
        return 0

def get_active_channels(hours: int = 24) -> List[Dict[str, Any]]:
    """
    Get a list of channels that have had activity in the last specified hours.

    Args:
        hours (int): Number of hours to look back for activity

    Returns:
        List[Dict[str, Any]]: A list of active channels with their details
    """
    try:
        # Calculate the cutoff time
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        with get_connection() as conn:
            cursor = conn.cursor()

            # Query for active channels
            cursor.execute(
                """
                SELECT
                    channel_id,
                    channel_name,
                    guild_id,
                    guild_name,
                    COUNT(*) as message_count
                FROM messages
                WHERE created_at >= ?
                GROUP BY channel_id
                ORDER BY message_count DESC
                """,
                (cutoff_time,)
            )

            # Convert rows to dictionaries
            channels = []
            for row in cursor.fetchall():
                channels.append({
                    'channel_id': row['channel_id'],
                    'channel_name': row['channel_name'],
                    'guild_id': row['guild_id'],
                    'guild_name': row['guild_name'],
                    'message_count': row['message_count']
                })

        logger.info(f"Found {len(channels)} active channels in the last {hours} hours")
        return channels
    except Exception as e:
        logger.error(f"Error getting active channels for the last {hours} hours: {str(e)}", exc_info=True)
        return []

def get_scraped_content_by_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve scraped content for a specific URL from the database.
    
    Args:
        url (str): The URL to search for
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing scraped content if found, None otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query for messages with scraped content for this URL
            cursor.execute(
                """
                SELECT 
                    scraped_url,
                    scraped_content_summary,
                    scraped_content_key_points,
                    created_at
                FROM messages 
                WHERE scraped_url = ? AND scraped_content_summary IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (url,)
            )
            
            row = cursor.fetchone()
            if not row:
                logger.debug(f"No scraped content found for URL: {url}")
                return None
            
            # Parse key points JSON
            key_points = []
            if row['scraped_content_key_points']:
                try:
                    key_points = json.loads(row['scraped_content_key_points'])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in scraped_content_key_points for URL {url}")
            
            result = {
                'url': row['scraped_url'],
                'summary': row['scraped_content_summary'],
                'key_points': key_points,
                'created_at': row['created_at']
            }
            
            logger.debug(f"Retrieved scraped content for URL: {url}")
            return result
            
    except Exception as e:
        logger.error(f"Error retrieving scraped content for URL {url}: {str(e)}", exc_info=True)
        return None
