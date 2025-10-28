"""
Tests for database compression functionality.
"""

import pytest
import json
from compression_utils import (
    compress_text,
    decompress_text,
    compress_json,
    decompress_json,
    get_compression_stats,
    format_size,
    COMPRESSION_THRESHOLD
)

class TestCompressionUtils:
    """Test compression utility functions."""
    
    def test_compress_small_text(self):
        """Small text should not be compressed."""
        small_text = "Hello world"
        result = compress_text(small_text)
        # Should return original text since it's below threshold
        assert result == small_text
    
    def test_compress_large_text(self):
        """Large text should be compressed."""
        # Create text larger than threshold
        large_text = "This is a test message. " * 20  # ~480 characters
        result = compress_text(large_text)
        
        # Result should be different (compressed)
        assert result != large_text
        # Should be shorter after compression
        assert len(result) < len(large_text)
    
    def test_compress_decompress_roundtrip(self):
        """Test that compression and decompression preserves data."""
        original_text = "This is a longer test message that should be compressed. " * 10
        
        compressed = compress_text(original_text)
        decompressed = decompress_text(compressed)
        
        # Should get back original text
        assert decompressed == original_text
    
    def test_decompress_uncompressed_text(self):
        """Decompressing uncompressed text should return it unchanged."""
        text = "This is not compressed"
        result = decompress_text(text)
        assert result == text
    
    def test_compress_none(self):
        """Compressing None should return None."""
        assert compress_text(None) is None
    
    def test_decompress_none(self):
        """Decompressing None should return None."""
        assert decompress_text(None) is None
    
    def test_compress_empty_string(self):
        """Compressing empty string should return empty string."""
        assert compress_text("") == ""
    
    def test_decompress_empty_string(self):
        """Decompressing empty string should return empty string."""
        assert decompress_text("") == ""
    
    def test_compress_unicode(self):
        """Test compression with unicode characters."""
        unicode_text = "Hello 世界! 🌍 Testing émojis and spëcial çharacters. " * 5
        
        compressed = compress_text(unicode_text)
        decompressed = decompress_text(compressed)
        
        assert decompressed == unicode_text
    
    def test_compress_json_dict(self):
        """Test JSON compression with dictionary."""
        data = {
            "users": ["Alice", "Bob", "Charlie"],
            "count": 42,
            "metadata": {"key": "value", "nested": {"data": "here"}}
        }
        
        compressed = compress_json(data)
        decompressed = decompress_json(compressed)
        
        assert decompressed == data
    
    def test_compress_json_list(self):
        """Test JSON compression with list."""
        data = ["item1", "item2", "item3"] * 10
        
        compressed = compress_json(data)
        decompressed = decompress_json(compressed)
        
        assert decompressed == data
    
    def test_compress_json_none(self):
        """Compressing None JSON should return None."""
        assert compress_json(None) is None
    
    def test_decompress_json_none(self):
        """Decompressing None JSON should return None."""
        assert decompress_json(None) is None
    
    def test_compress_already_compressed(self):
        """Compressing already compressed data should not double-compress."""
        original_text = "This is a test message. " * 20
        
        first_compression = compress_text(original_text)
        second_compression = compress_text(first_compression)
        
        # Should detect it's already compressed and return as-is
        assert first_compression == second_compression
    
    def test_compression_stats(self):
        """Test compression statistics calculation."""
        original_size = 1000
        compressed_size = 400
        
        stats = get_compression_stats(original_size, compressed_size)
        
        assert stats['original_size'] == 1000
        assert stats['compressed_size'] == 400
        assert stats['saved_bytes'] == 600
        assert stats['compression_ratio'] == 60.0
    
    def test_compression_stats_zero(self):
        """Test compression statistics with zero size."""
        stats = get_compression_stats(0, 0)
        
        assert stats['original_size'] == 0
        assert stats['compressed_size'] == 0
        assert stats['saved_bytes'] == 0
        assert stats['compression_ratio'] == 0.0
    
    def test_format_size_bytes(self):
        """Test byte size formatting."""
        assert "512.0 B" in format_size(512)
    
    def test_format_size_kilobytes(self):
        """Test kilobyte size formatting."""
        assert "KB" in format_size(2048)
    
    def test_format_size_megabytes(self):
        """Test megabyte size formatting."""
        assert "MB" in format_size(2 * 1024 * 1024)
    
    def test_real_world_message(self):
        """Test with real-world message content."""
        message = """
        Hey everyone, I wanted to share this interesting article I found about 
        database optimization techniques. The article discusses various approaches
        including indexing strategies, query optimization, and data compression.
        It's particularly relevant to what we're working on right now.
        
        Here are the key takeaways:
        1. Proper indexing can improve query performance by 10-100x
        2. Compression can reduce storage costs by 50-80%
        3. Query optimization should be data-driven
        
        Let me know what you think!
        """
        
        compressed = compress_text(message)
        decompressed = decompress_text(compressed)
        
        # Should preserve the message
        assert decompressed == message
        # Should achieve some compression
        assert len(compressed) < len(message)
    
    def test_real_world_scraped_content(self):
        """Test with real-world scraped content structure."""
        scraped_data = {
            "title": "Understanding Database Compression",
            "summary": "This article explores various database compression techniques " * 10,
            "key_points": [
                "Compression reduces storage costs",
                "Multiple compression algorithms available",
                "Trade-off between compression ratio and CPU usage"
            ] * 5,
            "metadata": {
                "author": "John Doe",
                "date": "2024-01-01",
                "source": "Tech Blog"
            }
        }
        
        compressed = compress_json(scraped_data)
        decompressed = decompress_json(compressed)
        
        assert decompressed == scraped_data
    
    def test_compression_efficiency(self):
        """Test that compression is efficient for repetitive data."""
        # Repetitive data should compress well
        repetitive_text = "This is repeated text. " * 100
        
        compressed = compress_text(repetitive_text)
        original_size = len(repetitive_text.encode('utf-8'))
        
        # Estimate compressed size (base64 adds ~33% overhead)
        # But gzip should compress the repetitive content significantly
        # We expect at least 50% reduction even with base64 overhead
        assert len(compressed) < original_size * 0.5
    
    def test_large_json_compression(self):
        """Test compression of large JSON structures."""
        large_json = {
            "messages": [
                {
                    "id": i,
                    "content": f"Message content {i}",
                    "author": f"User {i % 10}",
                    "timestamp": "2024-01-01T00:00:00"
                }
                for i in range(100)
            ]
        }
        
        compressed = compress_json(large_json)
        decompressed = decompress_json(compressed)
        
        assert decompressed == large_json
        # Should achieve compression
        original_size = len(json.dumps(large_json).encode('utf-8'))
        compressed_size = len(compressed.encode('utf-8'))
        assert compressed_size < original_size


class TestDatabaseIntegration:
    """Test compression integration with database operations."""
    
    @pytest.fixture
    def test_db_connection(self, tmp_path):
        """Create a temporary test database."""
        import sqlite3
        import os
        
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        
        # Create test table
        conn.execute("""
            CREATE TABLE test_messages (
                id INTEGER PRIMARY KEY,
                content TEXT,
                summary TEXT
            )
        """)
        conn.commit()
        
        yield conn
        
        conn.close()
    
    def test_database_compression_storage(self, test_db_connection):
        """Test storing compressed data in database."""
        message = "This is a test message. " * 20
        compressed = compress_text(message)
        
        # Store compressed data
        test_db_connection.execute(
            "INSERT INTO test_messages (content) VALUES (?)",
            (compressed,)
        )
        test_db_connection.commit()
        
        # Retrieve and decompress
        cursor = test_db_connection.execute("SELECT content FROM test_messages WHERE id = 1")
        row = cursor.fetchone()
        decompressed = decompress_text(row[0])
        
        assert decompressed == message
    
    def test_database_mixed_storage(self, test_db_connection):
        """Test database with both compressed and uncompressed data."""
        compressed_msg = "This is a longer message. " * 20
        short_msg = "Short"
        
        # Store both (short won't be compressed)
        compressed = compress_text(compressed_msg)
        short_stored = compress_text(short_msg)
        
        test_db_connection.execute(
            "INSERT INTO test_messages (id, content) VALUES (?, ?)",
            (1, compressed)
        )
        test_db_connection.execute(
            "INSERT INTO test_messages (id, content) VALUES (?, ?)",
            (2, short_stored)
        )
        test_db_connection.commit()
        
        # Retrieve both
        cursor = test_db_connection.execute("SELECT id, content FROM test_messages ORDER BY id")
        rows = cursor.fetchall()
        
        # Both should decompress correctly
        assert decompress_text(rows[0][1]) == compressed_msg
        assert decompress_text(rows[1][1]) == short_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
