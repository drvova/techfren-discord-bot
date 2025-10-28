"""
Integration tests for database compression with real database operations.
Tests the entire flow: store compressed -> retrieve decompressed.
"""

import pytest
import os
import sqlite3
from datetime import datetime
from database import (
    init_database,
    store_message,
    get_all_channel_messages,
    store_channel_summary,
    get_scraped_content_by_url,
    DB_FILE
)


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    # Backup original DB_FILE
    original_db = DB_FILE
    
    # Create temporary database path
    test_db_path = tmp_path / "test_discord.db"
    
    # Monkey patch the DB_FILE
    import database
    database.DB_FILE = str(test_db_path)
    database.DB_DIRECTORY = str(tmp_path)
    
    # Initialize database
    init_database()
    
    yield str(test_db_path)
    
    # Restore original DB_FILE
    database.DB_FILE = original_db


class TestCompressionIntegration:
    """Integration tests for compression with database operations."""
    
    def test_store_and_retrieve_short_message(self, test_db):
        """Test storing and retrieving a short message (not compressed)."""
        message_id = "test_msg_1"
        content = "Short message"
        
        # Store message
        result = store_message(
            message_id=message_id,
            author_id="author_1",
            author_name="Test User",
            channel_id="channel_1",
            channel_name="test-channel",
            content=content,
            created_at=datetime.now()
        )
        
        assert result is True
        
        # Retrieve message
        messages = get_all_channel_messages("channel_1", limit=10)
        assert len(messages) == 1
        assert messages[0]['content'] == content
    
    def test_store_and_retrieve_long_message(self, test_db):
        """Test storing and retrieving a long message (compressed)."""
        message_id = "test_msg_2"
        content = "This is a very long message that should be compressed. " * 20
        
        # Store message
        result = store_message(
            message_id=message_id,
            author_id="author_1",
            author_name="Test User",
            channel_id="channel_1",
            channel_name="test-channel",
            content=content,
            created_at=datetime.now()
        )
        
        assert result is True
        
        # Retrieve message
        messages = get_all_channel_messages("channel_1", limit=10)
        
        # Find our message (there might be test messages from init)
        our_message = next((m for m in messages if content in m['content']), None)
        assert our_message is not None
        assert our_message['content'] == content
    
    def test_store_with_scraped_content(self, test_db):
        """Test storing message with scraped content."""
        message_id = "test_msg_3"
        scraped_summary = "This is a summary of scraped content. " * 10
        scraped_key_points = '["point 1", "point 2", "point 3"]'
        
        # Store message with scraped content
        result = store_message(
            message_id=message_id,
            author_id="author_1",
            author_name="Test User",
            channel_id="channel_1",
            channel_name="test-channel",
            content="Check out this link!",
            created_at=datetime.now(),
            scraped_url="https://example.com",
            scraped_content_summary=scraped_summary,
            scraped_content_key_points=scraped_key_points
        )
        
        assert result is True
        
        # Retrieve and verify
        scraped_data = get_scraped_content_by_url("https://example.com")
        assert scraped_data is not None
        assert scraped_data['summary'] == scraped_summary
        assert scraped_data['key_points'] == ["point 1", "point 2", "point 3"]
    
    def test_store_channel_summary(self, test_db):
        """Test storing and retrieving channel summary."""
        active_users = ["user1", "user2", "user3"] * 10
        summary_text = "Channel summary with lots of activity and discussion. " * 20
        metadata = {
            "topic": "Testing",
            "highlights": ["feature 1", "feature 2"] * 5
        }
        
        # Store summary
        result = store_channel_summary(
            channel_id="channel_1",
            channel_name="test-channel",
            date=datetime.now(),
            summary_text=summary_text,
            message_count=100,
            active_users=active_users,
            metadata=metadata
        )
        
        assert result is True
        
        # Verify data was stored (query directly)
        import database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT summary_text, active_users_list, metadata FROM channel_summaries WHERE channel_id = ?",
            ("channel_1",)
        )
        row = cursor.fetchone()
        conn.close()
        
        assert row is not None
        
        # Import decompression functions to manually verify
        from compression_utils import decompress_text, decompress_json
        
        # Decompress and verify
        decompressed_summary = decompress_text(row['summary_text'])
        assert decompressed_summary == summary_text
        
        decompressed_users = decompress_json(row['active_users_list'])
        assert decompressed_users == active_users
        
        decompressed_metadata = decompress_json(row['metadata'])
        assert decompressed_metadata == metadata
    
    def test_unicode_content(self, test_db):
        """Test compression with unicode content."""
        message_id = "test_msg_unicode"
        content = "Hello 世界! 🌍 Testing émojis and spëcial çharacters. " * 10
        
        # Store message
        result = store_message(
            message_id=message_id,
            author_id="author_1",
            author_name="Test User",
            channel_id="channel_1",
            channel_name="test-channel",
            content=content,
            created_at=datetime.now()
        )
        
        assert result is True
        
        # Retrieve and verify
        messages = get_all_channel_messages("channel_1", limit=100)
        unicode_message = next((m for m in messages if "世界" in m['content']), None)
        assert unicode_message is not None
        assert unicode_message['content'] == content
    
    def test_mixed_compressed_uncompressed(self, test_db):
        """Test database with both compressed and uncompressed messages."""
        # Store short message (not compressed)
        store_message(
            message_id="msg_short",
            author_id="author_1",
            author_name="Test User",
            channel_id="channel_1",
            channel_name="test-channel",
            content="Short",
            created_at=datetime.now()
        )
        
        # Store long message (compressed)
        long_content = "Long message content. " * 50
        store_message(
            message_id="msg_long",
            author_id="author_1",
            author_name="Test User",
            channel_id="channel_1",
            channel_name="test-channel",
            content=long_content,
            created_at=datetime.now()
        )
        
        # Retrieve all
        messages = get_all_channel_messages("channel_1", limit=100)
        
        # Should retrieve both correctly
        assert any(m['content'] == "Short" for m in messages)
        assert any(m['content'] == long_content for m in messages)
    
    def test_compression_actually_saves_space(self, test_db):
        """Verify that compression reduces stored data size."""
        # Store multiple long messages and measure the actual data size
        total_original_size = 0
        
        for i in range(10):
            content = f"Message {i}: " + ("This is repetitive content. " * 30)
            total_original_size += len(content.encode('utf-8'))
            
            store_message(
                message_id=f"msg_{i}",
                author_id="author_1",
                author_name="Test User",
                channel_id="channel_1",
                channel_name="test-channel",
                content=content,
                created_at=datetime.now()
            )
        
        # Query the actual stored size in the content column
        import database
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(LENGTH(content)) as total_size 
            FROM messages 
            WHERE id LIKE 'msg_%'
        """)
        row = cursor.fetchone()
        stored_size = row['total_size']
        conn.close()
        
        # With compression, stored size should be much less than original
        # We expect at least 30% compression for repetitive content
        compression_ratio = (total_original_size - stored_size) / total_original_size
        assert compression_ratio > 0.3, f"Compression ratio too low: {compression_ratio:.1%} (expected >30%)"
        
        # Verify all messages can still be retrieved
        messages = get_all_channel_messages("channel_1", limit=100)
        content_messages = [m for m in messages if "Message" in m['content']]
        assert len(content_messages) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
