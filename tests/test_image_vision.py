import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from image_handler import (
    download_image,
    encode_image_to_base64,
    get_image_mime_type,
    create_image_data_url,
    extract_images_from_message,
    get_all_images_from_context
)

@pytest.mark.asyncio
async def test_get_image_mime_type():
    """Test MIME type detection from URL"""
    assert get_image_mime_type("https://example.com/image.png") == "image/png"
    assert get_image_mime_type("https://example.com/image.jpg") == "image/jpeg"
    assert get_image_mime_type("https://example.com/image.jpeg") == "image/jpeg"
    assert get_image_mime_type("https://example.com/image.gif") == "image/gif"
    assert get_image_mime_type("https://example.com/image.webp") == "image/webp"
    assert get_image_mime_type("https://example.com/image.bmp") == "image/bmp"
    assert get_image_mime_type("https://example.com/image.unknown") == "image/jpeg"  # default

@pytest.mark.asyncio
async def test_encode_image_to_base64():
    """Test base64 encoding"""
    test_bytes = b"test image data"
    encoded = encode_image_to_base64(test_bytes)
    assert isinstance(encoded, str)
    assert len(encoded) > 0
    # Verify it's valid base64
    import base64
    decoded = base64.b64decode(encoded)
    assert decoded == test_bytes

@pytest.mark.asyncio
async def test_extract_images_from_message():
    """Test extracting images from Discord message attachments"""
    # Mock Discord message with image attachment
    mock_attachment = Mock()
    mock_attachment.content_type = "image/png"
    mock_attachment.url = "https://cdn.discordapp.com/attachments/123/456/test.png"
    
    mock_message = Mock()
    mock_message.attachments = [mock_attachment]
    
    urls = await extract_images_from_message(mock_message)
    assert len(urls) == 1
    assert urls[0] == "https://cdn.discordapp.com/attachments/123/456/test.png"

@pytest.mark.asyncio
async def test_extract_images_from_message_no_images():
    """Test extracting images when there are no image attachments"""
    # Mock Discord message with non-image attachment
    mock_attachment = Mock()
    mock_attachment.content_type = "application/pdf"
    mock_attachment.url = "https://cdn.discordapp.com/attachments/123/456/file.pdf"
    
    mock_message = Mock()
    mock_message.attachments = [mock_attachment]
    
    urls = await extract_images_from_message(mock_message)
    assert len(urls) == 0

@pytest.mark.asyncio
async def test_extract_images_from_message_empty():
    """Test extracting images from message with no attachments"""
    mock_message = Mock()
    mock_message.attachments = []
    
    urls = await extract_images_from_message(mock_message)
    assert len(urls) == 0

@pytest.mark.asyncio
async def test_get_all_images_from_context_with_referenced_message():
    """Test getting images from referenced message"""
    # Mock attachment
    mock_attachment = Mock()
    mock_attachment.content_type = "image/jpeg"
    mock_attachment.url = "https://cdn.discordapp.com/attachments/123/456/image.jpg"
    
    # Mock referenced message with image
    mock_ref_message = Mock()
    mock_ref_message.attachments = [mock_attachment]
    
    # Mock message context
    message_context = {
        'referenced_message': mock_ref_message,
        'linked_messages': [],
        'original_message': None
    }
    
    with patch('image_handler.create_image_data_url', new_callable=AsyncMock) as mock_create_data_url:
        mock_create_data_url.return_value = "data:image/jpeg;base64,test123"
        
        data_urls = await get_all_images_from_context(message_context)
        
        assert len(data_urls) == 1
        assert data_urls[0] == "data:image/jpeg;base64,test123"
        mock_create_data_url.assert_called_once_with("https://cdn.discordapp.com/attachments/123/456/image.jpg")

@pytest.mark.asyncio
async def test_get_all_images_from_context_with_multiple_sources():
    """Test getting images from multiple sources (original, referenced, linked)"""
    # Mock attachments
    mock_attachment1 = Mock()
    mock_attachment1.content_type = "image/png"
    mock_attachment1.url = "https://cdn.discordapp.com/attachments/123/456/img1.png"
    
    mock_attachment2 = Mock()
    mock_attachment2.content_type = "image/jpeg"
    mock_attachment2.url = "https://cdn.discordapp.com/attachments/123/456/img2.jpg"
    
    mock_attachment3 = Mock()
    mock_attachment3.content_type = "image/gif"
    mock_attachment3.url = "https://cdn.discordapp.com/attachments/123/456/img3.gif"
    
    # Mock messages
    mock_ref_message = Mock()
    mock_ref_message.attachments = [mock_attachment1]
    
    mock_linked_message = Mock()
    mock_linked_message.attachments = [mock_attachment2]
    
    mock_original_message = Mock()
    mock_original_message.attachments = [mock_attachment3]
    
    # Mock message context
    message_context = {
        'referenced_message': mock_ref_message,
        'linked_messages': [mock_linked_message],
        'original_message': mock_original_message
    }
    
    with patch('image_handler.create_image_data_url', new_callable=AsyncMock) as mock_create_data_url:
        mock_create_data_url.side_effect = [
            "data:image/png;base64,data1",
            "data:image/jpeg;base64,data2",
            "data:image/gif;base64,data3"
        ]
        
        data_urls = await get_all_images_from_context(message_context)
        
        assert len(data_urls) == 3
        assert "data:image/png;base64,data1" in data_urls
        assert "data:image/jpeg;base64,data2" in data_urls
        assert "data:image/gif;base64,data3" in data_urls

@pytest.mark.asyncio
async def test_get_all_images_from_context_no_context():
    """Test getting images when context is None"""
    data_urls = await get_all_images_from_context(None)
    assert len(data_urls) == 0

@pytest.mark.asyncio
async def test_get_all_images_from_context_no_images():
    """Test getting images when context has no images"""
    mock_message = Mock()
    mock_message.attachments = []
    
    message_context = {
        'referenced_message': mock_message,
        'linked_messages': [mock_message],
        'original_message': mock_message
    }
    
    data_urls = await get_all_images_from_context(message_context)
    assert len(data_urls) == 0

@pytest.mark.asyncio
async def test_create_image_data_url_with_mock():
    """Test creating image data URL with mocked download"""
    test_image_data = b"\x89PNG\r\n\x1a\n"  # PNG header
    
    with patch('image_handler.download_image', new_callable=AsyncMock) as mock_download:
        mock_download.return_value = test_image_data
        
        data_url = await create_image_data_url("https://example.com/test.png")

        assert data_url is not None
        assert data_url.startswith("data:image/jpeg;base64,")
        assert len(data_url) > 30
        mock_download.assert_called_once_with("https://example.com/test.png")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
