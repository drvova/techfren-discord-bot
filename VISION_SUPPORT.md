# Vision Support - Image Analysis in Discord Bot

## Overview

The bot now supports vision capabilities, allowing it to analyze images sent by users. The LLM can see and describe images from:
- Direct message attachments
- Referenced messages (replies)
- Linked Discord messages

## How It Works

### 1. Image Detection
When a user mentions the bot, the system automatically detects images in:
- The current message
- Any referenced message (reply)
- Any linked Discord messages

### 2. Image Processing Pipeline
```
User sends message with image attachment
        ↓
Bot detects image in message context
        ↓
Downloads image from Discord CDN URL
        ↓
Converts image to base64 encoding
        ↓
Packages as data URL: "data:image/jpeg;base64,..."
        ↓
Sends to LLM API with both text query AND image(s)
        ↓
Vision-capable model analyzes image
        ↓
Returns response describing/analyzing the image
```

### 3. Supported Image Formats
- JPEG/JPG
- PNG
- GIF
- WebP
- BMP
- TIFF

### 4. Image Size Limits
- Maximum 5MB per image (for safety and performance)
- Multiple images can be sent in a single request

## Usage Examples

### Example 1: Direct Image Attachment
```
User: @Bot what's in this image? [attaches image]
Bot: [Analyzes and describes the image content]
```

### Example 2: Reply to Message with Image
```
User1: [Posts message with image]
User2: @Bot what's happening in this image? [replies to User1's message]
Bot: [Analyzes the image from User1's message]
```

### Example 3: Linked Message with Image
```
User1: [Posts message with image in another channel]
User2: @Bot analyze this: https://discord.com/channels/.../...
Bot: [Analyzes the image from the linked message]
```

### Example 4: Multiple Images
```
User: @Bot compare these images [attaches 2 images]
Bot: [Analyzes and compares both images]
```

## Technical Implementation

### New Module: `image_handler.py`
Core functions:
- `download_image(url)` - Downloads image from URL
- `encode_image_to_base64(image_bytes)` - Converts to base64
- `create_image_data_url(url)` - Creates data URL
- `extract_images_from_message(message)` - Gets images from Discord message
- `get_all_images_from_context(message_context)` - Aggregates all images from context

### Updated Module: `llm_handler.py`
- Modified `call_llm_api()` to support vision mode
- Detects images in message context
- Constructs multimodal API request with text + images
- Sends images as data URLs to the LLM

### Message Format for Vision API
When images are detected:
```python
{
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "User's query text"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,..."
            }
        }
        # ... more images if present
    ]
}
```

## Model Requirements

The vision feature requires a vision-capable LLM model such as:
- GPT-4V (OpenAI)
- Claude 3 (Anthropic) with vision
- Perplexity Sonar with vision support
- Other multimodal models

Ensure your configured model supports vision API calls. Check the model documentation for:
- Image format support
- Maximum image size
- Maximum number of images per request
- Token usage with images

## Configuration

No additional configuration is required. The feature automatically activates when:
1. Images are detected in message context
2. The configured LLM model supports vision

The system logs indicate when vision mode is enabled:
```
Vision mode enabled: sending N image(s) to LLM
```

## Error Handling

The system gracefully handles:
- Invalid image URLs
- Download failures
- Oversized images (>5MB)
- Non-image attachments
- Network errors

If image processing fails, the bot continues with text-only mode.

## Performance Considerations

- Images are downloaded asynchronously
- Base64 encoding is efficient for typical Discord image sizes
- Multiple images are batched in a single API request
- Failed image downloads don't block text processing

## Testing

Run the test suite:
```bash
python3 -m pytest test_image_vision.py -v
```

Tests cover:
- MIME type detection
- Base64 encoding
- Image extraction from messages
- Context image aggregation
- Error handling

## Limitations

1. **Image Size**: Maximum 5MB per image (Discord CDN limit is usually lower)
2. **API Limits**: Subject to LLM provider's vision API limits and token usage
3. **Processing Time**: Image processing adds latency to responses
4. **Model Support**: Requires vision-capable model

## Future Enhancements

Possible improvements:
- Image compression for large files
- OCR for text extraction
- Image metadata extraction
- Cached image analysis
- Image generation support
