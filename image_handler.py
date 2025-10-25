"""
Image processing and understanding for Discord bot.
Handles downloading images and preparing them for LLM analysis.
"""

import base64
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from logging_config import logger


class ImageContent:
    """Builder pattern for image content in LLM requests."""

    def __init__(self):
        self._images: List[Dict[str, Any]] = []

    def add_image_url(self, url: str, detail: str = "auto") -> "ImageContent":
        """Add an image from a URL."""
        self._images.append({"type": "image_url", "image_url": {"url": url, "detail": detail}})
        return self

    def add_image_base64(self, base64_data: str, media_type: str = "image/jpeg", detail: str = "auto") -> "ImageContent":
        """Add an image from base64 data."""
        data_url = f"data:{media_type};base64,{base64_data}"
        self._images.append({"type": "image_url", "image_url": {"url": data_url, "detail": detail}})
        return self

    def build(self) -> List[Dict[str, Any]]:
        """Build the image content list."""
        return self._images

    def has_images(self) -> bool:
        """Check if any images have been added."""
        return len(self._images) > 0


async def download_image_as_base64(url: str) -> Optional[tuple[str, str]]:
    """
    Download an image and convert to base64.

    Args:
        url: The image URL to download

    Returns:
        Optional[tuple[str, str]]: (base64_data, media_type) or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.warning("Failed to download image from %s: HTTP %s", url, response.status)
                    return None

                content_type = response.headers.get("Content-Type", "image/jpeg")
                if not content_type.startswith("image/"):
                    logger.warning("URL %s is not an image (Content-Type: %s)", url, content_type)
                    return None

                image_data = await response.read()
                base64_data = base64.b64encode(image_data).decode("utf-8")
                logger.info("Successfully downloaded and encoded image from %s", url)
                return base64_data, content_type

    except asyncio.TimeoutError:
        logger.warning("Timeout downloading image from %s", url)
        return None
    except Exception as e:
        logger.error("Error downloading image from %s: %s", url, e)
        return None


async def process_images_from_context(message_context) -> Optional[ImageContent]:
    """Extract and process images from message context."""
    if not message_context:
        logger.debug("No message context provided for image processing")
        return None

    logger.debug("Processing images from context. Keys: %s", list(message_context.keys()))

    image_content = ImageContent()
    total_images_found = 0

    # Process referenced message images
    if message_context.get("referenced_message"):
        ref_msg = message_context["referenced_message"]
        if hasattr(ref_msg, "attachments"):
            for attachment in ref_msg.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    result = await download_image_as_base64(attachment.url)
                    if result:
                        base64_data, media_type = result
                        image_content.add_image_base64(base64_data, media_type)
                        total_images_found += 1
                        logger.info("Added image from referenced message: %s", attachment.filename)

    # Process linked messages images
    if message_context.get("linked_messages"):
        for linked_msg in message_context["linked_messages"]:
            if hasattr(linked_msg, "attachments"):
                for attachment in linked_msg.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        result = await download_image_as_base64(attachment.url)
                        if result:
                            base64_data, media_type = result
                            image_content.add_image_base64(base64_data, media_type)
                            total_images_found += 1
                            logger.info("Added image from linked message: %s", attachment.filename)

    # Process current message images
    if message_context.get("current_message"):
        current_msg = message_context["current_message"]
        logger.debug("Checking current_message for attachments")
        if hasattr(current_msg, "attachments"):
            logger.debug("Current message has %d attachment(s)", len(current_msg.attachments))
            for attachment in current_msg.attachments:
                logger.debug("Processing attachment: %s, content_type: %s", 
                           attachment.filename, attachment.content_type)
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    result = await download_image_as_base64(attachment.url)
                    if result:
                        base64_data, media_type = result
                        image_content.add_image_base64(base64_data, media_type)
                        total_images_found += 1
                        logger.info("Added image from current message: %s", attachment.filename)

    if image_content.has_images():
        logger.info("Processed %s image(s) from message context for LLM", total_images_found)
        return image_content
    
    return None
