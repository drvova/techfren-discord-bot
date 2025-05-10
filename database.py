"""
Database module for the Discord bot.
Handles SQLite database operations for storing messages.
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

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
    command_type TEXT
);
"""

CREATE_INDEX_AUTHOR = "CREATE INDEX IF NOT EXISTS idx_author_id ON messages (author_id);"
CREATE_INDEX_CHANNEL = "CREATE INDEX IF NOT EXISTS idx_channel_id ON messages (channel_id);"
CREATE_INDEX_GUILD = "CREATE INDEX IF NOT EXISTS idx_guild_id ON messages (guild_id);"
CREATE_INDEX_CREATED = "CREATE INDEX IF NOT EXISTS idx_created_at ON messages (created_at);"
CREATE_INDEX_COMMAND = "CREATE INDEX IF NOT EXISTS idx_is_command ON messages (is_command);"

INSERT_MESSAGE = """
INSERT INTO messages (
    id, author_id, author_name, channel_id, channel_name, 
    guild_id, guild_name, content, created_at, is_bot, is_command, command_type
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
        
        # Connect to the database and create tables
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create tables and indexes
        cursor.execute(CREATE_MESSAGES_TABLE)
        cursor.execute(CREATE_INDEX_AUTHOR)
        cursor.execute(CREATE_INDEX_CHANNEL)
        cursor.execute(CREATE_INDEX_GUILD)
        cursor.execute(CREATE_INDEX_CREATED)
        cursor.execute(CREATE_INDEX_COMMAND)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized successfully at {DB_FILE}")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

def get_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: A connection to the database.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}", exc_info=True)
        raise

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
    command_type: Optional[str] = None
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
        
    Returns:
        bool: True if the message was stored successfully, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
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
                created_at.isoformat(),
                1 if is_bot else 0,
                1 if is_command else 0,
                command_type
            )
        )
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Message {message_id} stored in database")
        return True
    except sqlite3.IntegrityError:
        # This could happen if we try to insert a message with the same ID twice
        logger.warning(f"Message {message_id} already exists in database")
        return False
    except Exception as e:
        logger.error(f"Error storing message {message_id}: {str(e)}", exc_info=True)
        return False

def get_message_count() -> int:
    """
    Get the total number of messages in the database.
    
    Returns:
        int: The number of messages
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting message count: {str(e)}", exc_info=True)
        return -1

def get_user_message_count(user_id: str) -> int:
    """
    Get the number of messages from a specific user.
    
    Args:
        user_id (str): The Discord user ID
        
    Returns:
        int: The number of messages from the user
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM messages WHERE author_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting message count for user {user_id}: {str(e)}", exc_info=True)
        return -1
