import discord
import aiohttp
import base64
from typing import Optional, List, Dict, Any
from logging_config import logger

async def download_image(url: str) -> Optional[bytes]:
    """
    Download an image from a URL.
    
    Args:
        url (str): The URL of the image to download
        
    Returns:
        Optional[bytes]: The image bytes if successful, None otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if not content_type.startswith('image/'):
                        logger.warning(f"URL does not point to an image: {url} (Content-Type: {content_type})")
                        return None
                    
                    # Check file size (max 5MB for safety)
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > 5 * 1024 * 1024:
                        logger.warning(f"Image too large: {url} ({content_length} bytes)")
                        return None
                    
                    return await response.read()
                else:
                    logger.warning(f"Failed to download image: {url} (status: {response.status})")
                    return None
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {str(e)}", exc_info=True)
        return None

def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string.
    
    Args:
        image_bytes (bytes): The image bytes to encode
        
    Returns:
        str: Base64 encoded string
    """
    return base64.b64encode(image_bytes).decode('utf-8')

def get_image_mime_type(url: str) -> str:
    """
    Get the MIME type of an image from its URL extension.
    
    Args:
        url (str): The image URL
        
    Returns:
        str: The MIME type (defaults to 'image/jpeg')
    """
    url_lower = url.lower()
    if url_lower.endswith('.png'):
        return 'image/png'
    elif url_lower.endswith('.gif'):
        return 'image/gif'
    elif url_lower.endswith('.webp'):
        return 'image/webp'
    elif url_lower.endswith('.bmp'):
        return 'image/bmp'
    elif url_lower.endswith('.tiff') or url_lower.endswith('.tif'):
        return 'image/tiff'
    else:
        return 'image/jpeg'

async def create_image_data_url(url: str) -> Optional[str]:
    """
    Download an image and convert it to a data URL.
    
    Args:
        url (str): The URL of the image
        
    Returns:
        Optional[str]: Data URL string in format "data:image/jpeg;base64,..." or None if failed
    """
    try:
        image_bytes = await download_image(url)
        if not image_bytes:
            return None
        
        base64_str = encode_image_to_base64(image_bytes)
        mime_type = get_image_mime_type(url)
        
        data_url = f"data:{mime_type};base64,{base64_str}"
        logger.info(f"Created image data URL from {url} (size: {len(image_bytes)} bytes)")
        
        return data_url
    except Exception as e:
        logger.error(f"Error creating image data URL from {url}: {str(e)}", exc_info=True)
        return None

async def extract_images_from_message(message: discord.Message) -> List[str]:
    """
    Extract image URLs from a Discord message's attachments.
    
    Args:
        message (discord.Message): The Discord message to check
        
    Returns:
        List[str]: List of image URLs
    """
    image_urls = []
    
    if message.attachments:
        logger.debug(f"Message has {len(message.attachments)} attachment(s)")
        for attachment in message.attachments:
            logger.debug(f"Attachment: {attachment.filename}, type: {attachment.content_type}")
            # Check if attachment is an image
            if attachment.content_type and attachment.content_type.startswith('image/'):
                image_urls.append(attachment.url)
                logger.info(f"Found image attachment: {attachment.filename} ({attachment.content_type})")
    else:
        logger.debug(f"Message has no attachments")
    
    return image_urls

async def get_all_images_from_context(message_context: Optional[Dict[str, Any]]) -> List[str]:
    """
    Get all image data URLs from message context (current, referenced, and linked messages).
    
    Args:
        message_context (Optional[Dict[str, Any]]): Message context containing referenced and linked messages
        
    Returns:
        List[str]: List of image data URLs
    """
    image_data_urls = []
    
    if not message_context:
        return image_data_urls
    
    # Check referenced message (reply)
    if message_context.get('referenced_message'):
        ref_msg = message_context['referenced_message']
        image_urls = await extract_images_from_message(ref_msg)
        for url in image_urls:
            data_url = await create_image_data_url(url)
            if data_url:
                image_data_urls.append(data_url)
                logger.info(f"Added image from referenced message")
    
    # Check linked messages
    if message_context.get('linked_messages'):
        for linked_msg in message_context['linked_messages']:
            image_urls = await extract_images_from_message(linked_msg)
            for url in image_urls:
                data_url = await create_image_data_url(url)
                if data_url:
                    image_data_urls.append(data_url)
                    logger.info(f"Added image from linked message")
    
    # Check original message
    if message_context.get('original_message'):
        orig_msg = message_context['original_message']
        image_urls = await extract_images_from_message(orig_msg)
        for url in image_urls:
            data_url = await create_image_data_url(url)
            if data_url:
                image_data_urls.append(data_url)
                logger.info(f"Added image from original message")
    
    logger.info(f"Total images extracted from context: {len(image_data_urls)}")
    return image_data_urls
