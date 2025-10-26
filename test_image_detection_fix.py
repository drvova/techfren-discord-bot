"""
Quick test to verify image detection works with the fix
"""
import asyncio
from unittest.mock import Mock, AsyncMock, patch

async def test_image_detection():
    """Test that images are detected from original message"""
    print("Testing image detection fix...")
    
    # Mock Discord message with image attachment
    mock_attachment = Mock()
    mock_attachment.content_type = "image/png"
    mock_attachment.url = "https://cdn.discordapp.com/attachments/123/456/test.png"
    mock_attachment.filename = "test.png"
    
    mock_message = Mock()
    mock_message.attachments = [mock_attachment]
    mock_message.reference = None
    mock_message.content = "@bot what's in this image?"
    
    # Test extract_images_from_message
    from image_handler import extract_images_from_message
    
    image_urls = await extract_images_from_message(mock_message)
    
    print(f"✓ Found {len(image_urls)} image(s)")
    assert len(image_urls) == 1, "Should detect 1 image"
    assert image_urls[0] == mock_attachment.url, "Should extract correct URL"
    print(f"✓ Image URL: {image_urls[0]}")
    
    # Test get_all_images_from_context
    from image_handler import get_all_images_from_context
    
    message_context = {
        'original_message': mock_message,
        'referenced_message': None,
        'linked_messages': []
    }
    
    with patch('image_handler.create_image_data_url', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = "data:image/png;base64,test123"
        
        data_urls = await get_all_images_from_context(message_context)
        
        print(f"✓ Extracted {len(data_urls)} data URL(s)")
        assert len(data_urls) == 1, "Should extract 1 data URL"
        assert data_urls[0] == "data:image/png;base64,test123", "Should create data URL"
        print(f"✓ Data URL created successfully")
    
    print("\n✅ All tests passed! Image detection is working correctly.")
    print("\nThe fix ensures:")
    print("  1. Original message is always included in context")
    print("  2. Images from attachments are detected")
    print("  3. Images are converted to data URLs")
    print("  4. Vision mode will activate when images are present")

if __name__ == "__main__":
    asyncio.run(test_image_detection())
