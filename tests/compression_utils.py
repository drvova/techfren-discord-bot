"""
Compression utilities for database storage optimization.
Uses gzip compression for text data to reduce storage space.
"""

import gzip
import base64
import logging
from typing import Optional, Any
import json

logger = logging.getLogger('discord_bot.compression')

# Minimum size threshold for compression (bytes)
# Only compress if the data is larger than this to avoid overhead
COMPRESSION_THRESHOLD = 100

# Marker to identify compressed data
COMPRESSION_MARKER = b"__GZIP__"

def compress_text(text: Optional[str]) -> Optional[str]:
    """
    Compress text data using gzip and encode as base64.
    Only compresses if data is larger than threshold.
    
    Args:
        text: The text to compress
        
    Returns:
        Compressed and encoded text, or original text if too small or None
    """
    if not text:
        return text
    
    try:
        # Check if text is already compressed
        # First check for base64-encoded compressed data
        try:
            decoded_bytes = base64.b64decode(text, validate=True)
            if decoded_bytes.startswith(COMPRESSION_MARKER):
                logger.debug("Text is already compressed (base64-encoded), skipping")
                return text
        except Exception:
            pass  # Not base64 or not compressed data, continue with normal flow

        # Check for plaintext marker (edge case for backward compatibility)
        if text.startswith(COMPRESSION_MARKER.decode('utf-8', errors='ignore')):
            logger.debug("Text is already compressed (plaintext marker), skipping")
            return text

        # Only compress if larger than threshold
        text_bytes = text.encode('utf-8')
        if len(text_bytes) < COMPRESSION_THRESHOLD:
            return text
        
        # Compress the data
        compressed = gzip.compress(text_bytes, compresslevel=6)
        
        # Only use compression if it actually reduces size
        if len(compressed) >= len(text_bytes):
            return text
        
        # Add marker and encode to base64 for safe storage
        marked_data = COMPRESSION_MARKER + compressed
        encoded = base64.b64encode(marked_data).decode('utf-8')
        
        compression_ratio = (1 - len(compressed) / len(text_bytes)) * 100
        logger.debug(f"Compressed text from {len(text_bytes)} to {len(compressed)} bytes ({compression_ratio:.1f}% reduction)")
        
        return encoded
    except Exception as e:
        logger.error(f"Error compressing text: {str(e)}", exc_info=True)
        return text

def decompress_text(text: Optional[str]) -> Optional[str]:
    """
    Decompress text data that was compressed with compress_text.
    Safely handles both compressed and uncompressed data.
    
    Args:
        text: The text to decompress
        
    Returns:
        Decompressed text, or original text if not compressed or None
    """
    if not text:
        return text
    
    try:
        # Try to decode from base64
        try:
            decoded = base64.b64decode(text.encode('utf-8'))
        except Exception:
            # Not base64 encoded, return as is
            return text
        
        # Check for compression marker
        if not decoded.startswith(COMPRESSION_MARKER):
            # Not compressed, return original
            return text
        
        # Remove marker and decompress
        compressed_data = decoded[len(COMPRESSION_MARKER):]
        decompressed = gzip.decompress(compressed_data)
        result = decompressed.decode('utf-8')
        
        logger.debug(f"Decompressed text from {len(compressed_data)} to {len(decompressed)} bytes")
        
        return result
    except Exception as e:
        logger.warning(f"Error decompressing text, returning original: {str(e)}")
        return text

def compress_json(data: Optional[Any]) -> Optional[str]:
    """
    Compress JSON-serializable data.
    Converts to JSON string first, then compresses.
    
    Args:
        data: JSON-serializable data (dict, list, etc.)
        
    Returns:
        Compressed JSON string, or None if data is None
    """
    if data is None:
        return None
    
    try:
        # Convert to JSON string
        json_str = json.dumps(data, separators=(',', ':'))  # Compact JSON
        
        # Compress the JSON string
        return compress_text(json_str)
    except Exception as e:
        logger.error(f"Error compressing JSON: {str(e)}", exc_info=True)
        # Fallback to uncompressed JSON
        return json.dumps(data)

def decompress_json(text: Optional[str]) -> Optional[Any]:
    """
    Decompress and parse JSON data that was compressed with compress_json.
    
    Args:
        text: Compressed JSON string
        
    Returns:
        Parsed JSON data, or None if text is None
    """
    if not text:
        return None
    
    try:
        # Decompress first
        decompressed = decompress_text(text)
        
        # Parse JSON
        return json.loads(decompressed)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON after decompression: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error decompressing JSON: {str(e)}", exc_info=True)
        return None

def get_compression_stats(original_size: int, compressed_size: int) -> dict:
    """
    Calculate compression statistics.
    
    Args:
        original_size: Original data size in bytes
        compressed_size: Compressed data size in bytes
        
    Returns:
        Dictionary with compression statistics
    """
    if original_size == 0:
        return {
            'original_size': 0,
            'compressed_size': 0,
            'saved_bytes': 0,
            'compression_ratio': 0.0
        }
    
    saved_bytes = original_size - compressed_size
    compression_ratio = (saved_bytes / original_size) * 100
    
    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'saved_bytes': saved_bytes,
        'compression_ratio': compression_ratio
    }

def format_size(size_bytes: int) -> str:
    """
    Format byte size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 KB", "2.3 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
