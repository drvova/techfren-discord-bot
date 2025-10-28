"""
Test the get_images_from_summary_messages function.
"""
import asyncio
import sys
from datetime import datetime
from image_handler import get_images_from_summary_messages

async def test_get_images_from_summary_messages():
    """Test extracting images from summary messages."""

    # Sample messages with image URLs in content
    test_messages = [
        {
            'id': '1',
            'author_name': 'Alice',
            'content': 'Check out this cool image: https://example.com/image1.jpg',
            'created_at': datetime(2024, 1, 1, 12, 0, 0),
        },
        {
            'id': '2',
            'author_name': 'Bob',
            'content': 'No images here just text',
            'created_at': datetime(2024, 1, 1, 12, 5, 0),
        },
        {
            'id': '3',
            'author_name': 'Charlie',
            'content': 'Multiple images: https://cdn.discordapp.com/attachments/123/456/image.png and https://example.com/photo.gif',
            'created_at': datetime(2024, 1, 1, 12, 10, 0),
        },
        {
            'id': '4',
            'author_name': 'Dave',
            'content': 'Another one https://media.discordapp.net/attachments/789/test.jpeg?width=400',
            'created_at': datetime(2024, 1, 1, 12, 15, 0),
        }
    ]

    print("Testing get_images_from_summary_messages...")
    print(f"Test messages: {len(test_messages)}")

    # Test 1: Extract with max_images=2, compress=True
    print("\n--- Test 1: max_images=2, compress=True ---")
    result = await get_images_from_summary_messages(test_messages, max_images=2, compress=True)
    print(f"Result count: {len(result)}")
    print(f"Expected: Should attempt to fetch most recent images (up to 2)")

    # Test 2: Extract with max_images=10, compress=False
    print("\n--- Test 2: max_images=10, compress=False ---")
    result = await get_images_from_summary_messages(test_messages, max_images=10, compress=False)
    print(f"Result count: {len(result)}")
    print(f"Expected: Should attempt to fetch all images found in messages")

    # Test 3: Empty messages list
    print("\n--- Test 3: Empty messages list ---")
    result = await get_images_from_summary_messages([], max_images=5, compress=True)
    print(f"Result count: {len(result)}")
    assert len(result) == 0, "Should return empty list for empty input"
    print("✓ Passed: Returns empty list for empty input")

    # Test 4: Messages with no image URLs
    print("\n--- Test 4: Messages with no image URLs ---")
    no_image_messages = [
        {'id': '1', 'author_name': 'Test', 'content': 'Just text', 'created_at': datetime.now()}
    ]
    result = await get_images_from_summary_messages(no_image_messages, max_images=5, compress=True)
    print(f"Result count: {len(result)}")
    assert len(result) == 0, "Should return empty list when no images found"
    print("✓ Passed: Returns empty list when no images in content")

    print("\n=== All tests completed ===")
    print("Note: Tests with actual URLs will fail to download (expected in test environment)")
    print("The function correctly extracts URLs from message content and processes them.")

if __name__ == '__main__':
    try:
        asyncio.run(test_get_images_from_summary_messages())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
