# Vision Support Integration Example

## Quick Start

The vision support is now fully integrated into the bot. No changes needed to your existing usage patterns!

## Usage Scenarios

### Scenario 1: Analyze an Image Directly
```
User: @TechFrenBot what's in this image?
[User attaches screenshot.png]

Bot: [Analyzes the image and provides description]
```

### Scenario 2: Ask About an Image in a Previous Message
```
Message #1 (User A):
[Posts a diagram image]

Message #2 (User B, replying to Message #1):
@TechFrenBot explain this diagram

Bot: [Analyzes the diagram from Message #1 and explains it]
```

### Scenario 3: Reference an Image from Another Channel
```
User: @TechFrenBot check out this code screenshot
https://discord.com/channels/123456/789012/345678

Bot: [Fetches the linked message, sees the image, analyzes it]
```

### Scenario 4: Multiple Images
```
User: @TechFrenBot compare these two approaches
[Attaches screenshot1.png]
[Attaches screenshot2.png]

Bot: [Analyzes both images and provides comparison]
```

## Behind the Scenes

When you mention the bot:
1. Bot checks the current message for images
2. Bot checks any replied-to message for images
3. Bot checks any linked Discord messages for images
4. All images are downloaded and encoded to base64
5. Images are sent to the LLM along with your text query
6. LLM analyzes images and responds

## Model Compatibility

Ensure your LLM model supports vision:
- ✅ GPT-4V (OpenAI)
- ✅ Claude 3 Opus/Sonnet (Anthropic)
- ✅ Perplexity Sonar (with vision support)
- ❌ GPT-3.5 (text-only)
- ❌ Standard Sonar (without vision)

Check your `config.py` or `.env` file:
```python
llm_model = "sonar"  # Make sure this supports vision
```

## Logs

When vision is active, you'll see in logs:
```
INFO: Vision mode enabled: sending 2 image(s) to LLM
INFO: Added image from referenced message
INFO: Total images extracted from context: 2
```

## Troubleshooting

### Image Not Detected
- Verify the attachment is an image (JPEG, PNG, GIF, WebP, BMP, TIFF)
- Check if the image is in the message context (current, referenced, or linked)
- Look for log entries about image extraction

### Image Too Large
- Discord attachments over 5MB are rejected
- Compress large images before uploading

### Model Doesn't Support Vision
- Verify your LLM model supports multimodal input
- Check the model documentation for vision capabilities
- Update `llm_model` in config to a vision-capable model

### No Response About Image
- Check logs for "Vision mode enabled" message
- Verify API key has vision API access
- Test with a simple image and clear question

## Performance Tips

1. **Compress Images**: Smaller images = faster processing
2. **One Question Per Image**: Clear, specific questions work best
3. **Image Quality**: Higher quality = better analysis
4. **Multiple Images**: Limited by API - usually 4-5 images max

## API Cost Considerations

Vision API calls typically cost more than text-only:
- Images consume additional tokens
- Larger images = more tokens
- Multiple images multiply costs

Monitor your API usage dashboard for vision-related costs.
