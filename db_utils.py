"""
Utility script for interacting with the Discord bot database.
Provides command-line tools for querying and managing the database.
"""

import argparse
import sqlite3
import os
import sys
from datetime import datetime
from tabulate import tabulate
from typing import List, Dict, Any

# Database constants
DB_DIRECTORY = "data"
DB_FILE = os.path.join(DB_DIRECTORY, "discord_messages.db")

def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    if not os.path.exists(DB_FILE):
        print(f"Error: Database file not found at {DB_FILE}")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def list_recent_messages(limit: int = 10) -> None:
    """List the most recent messages in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT id, author_name, channel_name, guild_name, 
           substr(content, 1, 50) as content_preview, 
           created_at, is_command, command_type
    FROM messages
    ORDER BY created_at DESC
    LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    if not rows:
        print("No messages found in the database.")
        return
    
    # Convert rows to list of dicts for tabulate
    data = []
    for row in rows:
        data.append({
            "ID": row['id'],
            "Author": row['author_name'],
            "Channel": row['channel_name'],
            "Guild": row['guild_name'] or 'DM',
            "Content": row['content_preview'] + ('...' if len(row['content_preview']) >= 50 else ''),
            "Created At": row['created_at'],
            "Command": f"{row['command_type'] if row['is_command'] else 'No'}"
        })
    
    print(tabulate(data, headers="keys", tablefmt="grid"))
    print(f"\nTotal messages shown: {len(rows)}")
    
    conn.close()

def get_message_stats() -> None:
    """Get statistics about messages in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total message count
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_count = cursor.fetchone()[0]
    
    # Command count
    cursor.execute("SELECT COUNT(*) FROM messages WHERE is_command = 1")
    command_count = cursor.fetchone()[0]
    
    # Command type breakdown
    cursor.execute("""
    SELECT command_type, COUNT(*) as count 
    FROM messages 
    WHERE is_command = 1 
    GROUP BY command_type
    """)
    command_types = cursor.fetchall()
    
    # User message count
    cursor.execute("""
    SELECT author_name, COUNT(*) as count 
    FROM messages 
    GROUP BY author_id 
    ORDER BY count DESC 
    LIMIT 10
    """)
    top_users = cursor.fetchall()
    
    # Channel message count
    cursor.execute("""
    SELECT channel_name, COUNT(*) as count 
    FROM messages 
    GROUP BY channel_id 
    ORDER BY count DESC 
    LIMIT 10
    """)
    top_channels = cursor.fetchall()
    
    # Print statistics
    print("\n=== Message Statistics ===")
    print(f"Total messages: {total_count}")
    print(f"Commands: {command_count} ({command_count/total_count*100:.1f}% of total)")
    
    print("\n--- Command Types ---")
    for cmd in command_types:
        print(f"{cmd['command_type']}: {cmd['count']} ({cmd['count']/command_count*100:.1f}% of commands)")
    
    print("\n--- Top Users ---")
    user_data = [{"User": row['author_name'], "Messages": row['count']} for row in top_users]
    print(tabulate(user_data, headers="keys", tablefmt="simple"))
    
    print("\n--- Top Channels ---")
    channel_data = [{"Channel": row['channel_name'], "Messages": row['count']} for row in top_channels]
    print(tabulate(channel_data, headers="keys", tablefmt="simple"))
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Discord Bot Database Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List recent messages command
    list_parser = subparsers.add_parser("list", help="List recent messages")
    list_parser.add_argument("-n", "--limit", type=int, default=10, help="Number of messages to show")
    
    # Stats command
    subparsers.add_parser("stats", help="Show message statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "list":
        list_recent_messages(args.limit)
    elif args.command == "stats":
        get_message_stats()

if __name__ == "__main__":
    main()
