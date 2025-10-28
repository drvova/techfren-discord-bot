"""
Migration script to compress existing database records.
This script will go through all existing messages and channel summaries
and compress their text fields to save space.
"""

import sqlite3
import logging
import sys
from datetime import datetime
from typing import Tuple
from compression_utils import (
    compress_text, 
    decompress_text,
    compress_json, 
    decompress_json,
    get_compression_stats,
    format_size
)
from database import DB_FILE, get_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_compression_migration')

def is_already_compressed(text: str) -> bool:
    """Check if text is already compressed."""
    if not text:
        return False
    try:
        # Try to decompress - if it returns different text, it was compressed
        decompressed = decompress_text(text)
        return decompressed != text
    except Exception:
        return False

def compress_messages_table() -> Tuple[int, int, int]:
    """
    Compress text fields in the messages table.
    
    Returns:
        Tuple of (processed_count, compressed_count, bytes_saved)
    """
    logger.info("Starting compression of messages table...")
    
    processed_count = 0
    compressed_count = 0
    total_bytes_saved = 0
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count for progress tracking
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            logger.info(f"Found {total_messages} messages to process")
            
            # Fetch all messages
            cursor.execute("""
                SELECT id, content, scraped_content_summary, scraped_content_key_points
                FROM messages
            """)
            
            messages = cursor.fetchall()

            # Collect updates in batches for better performance
            batch_size = 1000  # Process 1000 messages at a time
            current_batch = []
            total_processed_in_batch = 0

            for row in messages:
                message_id = row['id']
                content = row['content']
                summary = row['scraped_content_summary']
                key_points = row['scraped_content_key_points']

                needs_update = False
                original_size = 0
                compressed_size = 0

                # Compress content if not already compressed
                new_content = content
                if content and not is_already_compressed(content):
                    original_size += len(content.encode('utf-8'))
                    new_content = compress_text(content)
                    if new_content != content:
                        compressed_size += len(new_content.encode('utf-8'))
                        needs_update = True

                # Compress summary if not already compressed
                new_summary = summary
                if summary and not is_already_compressed(summary):
                    original_size += len(summary.encode('utf-8'))
                    new_summary = compress_text(summary)
                    if new_summary != summary:
                        compressed_size += len(new_summary.encode('utf-8'))
                        needs_update = True

                # Compress key points if not already compressed
                new_key_points = key_points
                if key_points and not is_already_compressed(key_points):
                    original_size += len(key_points.encode('utf-8'))
                    new_key_points = compress_text(key_points)
                    if new_key_points != key_points:
                        compressed_size += len(new_key_points.encode('utf-8'))
                        needs_update = True

                # Collect update if needed
                if needs_update:
                    current_batch.append((new_content, new_summary, new_key_points, message_id))
                    compressed_count += 1
                    total_bytes_saved += (original_size - compressed_size)

                processed_count += 1

                # Process batch when it reaches the batch size
                if len(current_batch) >= batch_size:
                    cursor.executemany("""
                        UPDATE messages
                        SET content = ?,
                            scraped_content_summary = ?,
                            scraped_content_key_points = ?
                        WHERE id = ?
                    """, current_batch)

                    total_processed_in_batch += len(current_batch)
                    current_batch.clear()

                    # Log progress every batch
                    logger.info(f"Processed {processed_count}/{total_messages} messages ({compressed_count} compressed, {total_processed_in_batch} updated in current batch)")

            # Process remaining updates in the final batch
            if current_batch:
                cursor.executemany("""
                    UPDATE messages
                    SET content = ?,
                        scraped_content_summary = ?,
                        scraped_content_key_points = ?
                    WHERE id = ?
                """, current_batch)

                total_processed_in_batch += len(current_batch)
                logger.info(f"Processed final batch: {len(current_batch)} messages updated")

            conn.commit()
            logger.info(f"Successfully compressed {compressed_count} messages out of {processed_count} total")
            logger.info(f"Total space saved: {format_size(total_bytes_saved)}")
            
    except Exception as e:
        logger.error(f"Error compressing messages table: {str(e)}", exc_info=True)
        raise
    
    return processed_count, compressed_count, total_bytes_saved

def compress_channel_summaries_table() -> Tuple[int, int, int]:
    """
    Compress text fields in the channel_summaries table.
    
    Returns:
        Tuple of (processed_count, compressed_count, bytes_saved)
    """
    logger.info("Starting compression of channel_summaries table...")
    
    processed_count = 0
    compressed_count = 0
    total_bytes_saved = 0
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count for progress tracking
            cursor.execute("SELECT COUNT(*) FROM channel_summaries")
            total_summaries = cursor.fetchone()[0]
            logger.info(f"Found {total_summaries} summaries to process")
            
            # Fetch all summaries
            cursor.execute("""
                SELECT id, summary_text, active_users_list, metadata
                FROM channel_summaries
            """)
            
            summaries = cursor.fetchall()

            # Collect updates in batches for better performance
            batch_size = 1000  # Process 1000 summaries at a time
            current_batch = []
            total_processed_in_batch = 0

            for row in summaries:
                summary_id = row['id']
                summary_text = row['summary_text']
                active_users_list = row['active_users_list']
                metadata = row['metadata']

                needs_update = False
                original_size = 0
                compressed_size = 0

                # Compress summary text if not already compressed
                new_summary_text = summary_text
                if summary_text and not is_already_compressed(summary_text):
                    original_size += len(summary_text.encode('utf-8'))
                    new_summary_text = compress_text(summary_text)
                    if new_summary_text != summary_text:
                        compressed_size += len(new_summary_text.encode('utf-8'))
                        needs_update = True

                # Compress active users list if not already compressed
                new_active_users = active_users_list
                if active_users_list and not is_already_compressed(active_users_list):
                    original_size += len(active_users_list.encode('utf-8'))
                    new_active_users = compress_text(active_users_list)
                    if new_active_users != active_users_list:
                        compressed_size += len(new_active_users.encode('utf-8'))
                        needs_update = True

                # Compress metadata if not already compressed
                new_metadata = metadata
                if metadata and not is_already_compressed(metadata):
                    original_size += len(metadata.encode('utf-8'))
                    new_metadata = compress_text(metadata)
                    if new_metadata != metadata:
                        compressed_size += len(new_metadata.encode('utf-8'))
                        needs_update = True

                # Collect update if needed
                if needs_update:
                    current_batch.append((new_summary_text, new_active_users, new_metadata, summary_id))
                    compressed_count += 1
                    total_bytes_saved += (original_size - compressed_size)

                processed_count += 1

                # Process batch when it reaches the batch size
                if len(current_batch) >= batch_size:
                    cursor.executemany("""
                        UPDATE channel_summaries
                        SET summary_text = ?,
                            active_users_list = ?,
                            metadata = ?
                        WHERE id = ?
                    """, current_batch)

                    total_processed_in_batch += len(current_batch)
                    current_batch.clear()

                    # Log progress every batch
                    logger.info(f"Processed {processed_count}/{total_summaries} summaries ({compressed_count} compressed, {total_processed_in_batch} updated in current batch)")

            # Process remaining updates in the final batch
            if current_batch:
                cursor.executemany("""
                    UPDATE channel_summaries
                    SET summary_text = ?,
                        active_users_list = ?,
                        metadata = ?
                    WHERE id = ?
                """, current_batch)

                total_processed_in_batch += len(current_batch)
                logger.info(f"Processed final batch: {len(current_batch)} summaries updated")

            conn.commit()
            logger.info(f"Successfully compressed {compressed_count} summaries out of {processed_count} total")
            logger.info(f"Total space saved: {format_size(total_bytes_saved)}")
            
    except Exception as e:
        logger.error(f"Error compressing channel_summaries table: {str(e)}", exc_info=True)
        raise
    
    return processed_count, compressed_count, total_bytes_saved

def get_database_size() -> int:
    """Get the current database file size in bytes."""
    import os
    if os.path.exists(DB_FILE):
        return os.path.getsize(DB_FILE)
    return 0

def main():
    """Run the compression migration."""
    logger.info("=" * 80)
    logger.info("DATABASE COMPRESSION MIGRATION")
    logger.info("=" * 80)
    
    # Get initial database size
    initial_size = get_database_size()
    logger.info(f"Initial database size: {format_size(initial_size)}")
    
    try:
        # Compress messages table
        msg_processed, msg_compressed, msg_saved = compress_messages_table()
        
        # Compress channel summaries table
        sum_processed, sum_compressed, sum_saved = compress_channel_summaries_table()
        
        # Get final database size
        final_size = get_database_size()
        actual_saved = initial_size - final_size
        
        # Print summary
        logger.info("=" * 80)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Messages: {msg_compressed}/{msg_processed} compressed, {format_size(msg_saved)} saved")
        logger.info(f"Summaries: {sum_compressed}/{sum_processed} compressed, {format_size(sum_saved)} saved")
        logger.info(f"Total logical savings: {format_size(msg_saved + sum_saved)}")
        logger.info(f"Initial database size: {format_size(initial_size)}")
        logger.info(f"Final database size: {format_size(final_size)}")
        
        if actual_saved > 0:
            logger.info(f"Actual space saved: {format_size(actual_saved)} ({(actual_saved/initial_size)*100:.1f}% reduction)")
        else:
            logger.info("Database size may increase slightly due to SQLite overhead, run VACUUM to reclaim space")
            logger.info("Run: sqlite3 data/discord_messages.db 'VACUUM;'")
        
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
