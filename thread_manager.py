"""
Centralized thread management - Single Source of Truth for all thread operations.

Constitutional Compliance:
- AMENDMENT III: Single source of truth for thread creation
- AMENDMENT I: Builder pattern for flexible thread management
- ARTICLE II: Net reduction by consolidating scattered logic
"""

import discord
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class ThreadManager:
    """
    Unified thread manager - handles all thread creation/retrieval across the bot.

    This class eliminates circular thread creation patterns by providing one
    authoritative method for ensuring thread existence.
    """

    # Class-level cache to prevent race conditions
    _thread_cache: Dict[int, discord.Thread] = {}
    _cache_expiry: Dict[int, datetime] = {}
    _CACHE_TTL = timedelta(minutes=5)

    def __init__(
        self, channel: discord.TextChannel, guild: Optional[discord.Guild] = None
    ):
        self.channel = channel
        self.guild = guild or (channel.guild if hasattr(channel, "guild") else None)

    @classmethod
    def _clean_expired_cache(cls) -> None:
        """Remove expired entries from thread cache."""
        now = datetime.now(timezone.utc)
        expired_ids = [
            msg_id for msg_id, expiry in cls._cache_expiry.items() if expiry <= now
        ]
        for msg_id in expired_ids:
            cls._thread_cache.pop(msg_id, None)
            cls._cache_expiry.pop(msg_id, None)

    async def ensure_thread(
        self, name: str, message: Optional[discord.Message] = None
    ) -> Optional[discord.Thread]:
        """
        Single method to ensure a thread exists - either retrieves existing or creates new.

        This is the ONLY method that should be called for thread creation across the bot.

        Args:
            name: Name for the thread
            message: Optional message to create thread from (if None, creates standalone thread)

        Returns:
            Thread object or None if creation failed
        """
        if not self.guild:
            logger.warning("Cannot create thread without guild context")
            return None

        # Clean expired cache entries
        self._clean_expired_cache()

        # If message provided, check cache and existing threads first
        if message:
            # Check cache first
            if message.id in self._thread_cache:
                cached_thread = self._thread_cache[message.id]
                logger.debug(
                    f"Returning cached thread '{cached_thread.name}' for message {message.id}"
                )
                return cached_thread

            # Check if thread already exists
            existing_thread = await self._get_existing_thread(message)
            if existing_thread:
                self._cache_thread(message.id, existing_thread)
                logger.info(
                    f"Found existing thread '{existing_thread.name}' for message {message.id}"
                )
                return existing_thread

            # Create thread from message
            thread = await self._create_thread_from_message(message, name)
            if thread:
                self._cache_thread(message.id, thread)
            return thread
        else:
            # Create standalone thread
            return await self._create_standalone_thread(name)

    def _cache_thread(self, message_id: int, thread: discord.Thread) -> None:
        """Cache a thread with expiry."""
        self._thread_cache[message_id] = thread
        self._cache_expiry[message_id] = datetime.now(timezone.utc) + self._CACHE_TTL
        logger.debug(f"Cached thread '{thread.name}' for message {message_id}")

    async def _get_existing_thread(
        self, message: discord.Message
    ) -> Optional[discord.Thread]:
        """Check if a message already has an associated thread."""
        try:
            # Check message.thread attribute
            if hasattr(message, "thread") and message.thread:
                logger.debug(f"Found thread via message.thread: {message.thread.name}")
                return message.thread

            # Search active threads (thread.id == starter_message.id in Discord API)
            try:
                active_threads = await self.channel.guild.active_threads()
                for thread in active_threads:
                    if (
                        hasattr(thread, "parent_id")
                        and thread.parent_id == self.channel.id
                        and thread.id == message.id
                    ):
                        logger.debug(f"Found thread via active_threads: {thread.name}")
                        return thread
            except (AttributeError, discord.HTTPException) as e:
                logger.debug(f"Could not fetch active threads: {e}")

            return None
        except Exception as e:
            logger.warning(f"Error checking for existing thread: {e}")
            return None

    async def _create_thread_from_message(
        self, message: discord.Message, name: str
    ) -> Optional[discord.Thread]:
        """Create a thread from a message with proper error handling."""
        try:
            # CRITICAL: Check if channel is already a thread - cannot create thread from thread
            if isinstance(self.channel, discord.Thread):
                logger.error(
                    f"Cannot create thread '{name}' from message in existing thread '{self.channel.name}'. "
                    f"Message ID: {message.id}. This is a Discord API limitation (Error 50024)."
                )
                return None

            # Check if message has guild info
            if not hasattr(message, "guild") or message.guild is None:
                logger.debug("Message lacks guild info, fetching with proper context")
                try:
                    fetched_message = await self.channel.fetch_message(message.id)
                    return await fetched_message.create_thread(name=name)
                except (discord.HTTPException, discord.NotFound) as e:
                    logger.warning(f"Failed to fetch message {message.id}: {e}")
                    return None

            # Create thread directly
            return await message.create_thread(name=name)

        except ValueError as e:
            if "guild info" in str(e):
                logger.debug("ValueError: guild info missing, fetching message")
                try:
                    fetched_message = await self.channel.fetch_message(message.id)
                    return await fetched_message.create_thread(name=name)
                except (discord.HTTPException, discord.NotFound) as fetch_error:
                    logger.warning(
                        f"Failed to fetch message {message.id}: {fetch_error}"
                    )
                    return None
            logger.error(f"ValueError creating thread: {e}")
            return None

        except discord.Forbidden as e:
            logger.warning(f"Insufficient permissions to create thread '{name}': {e}")
            return None

        except discord.HTTPException as e:
            # Handle race condition where thread was created between checks
            if (
                e.status == 400
                and "thread has already been created" in str(e.text).lower()
            ):
                logger.info(
                    f"Race condition detected for message {message.id}, fetching existing thread"
                )
                existing = await self._get_existing_thread(message)
                if existing:
                    self._cache_thread(message.id, existing)
                return existing

            # Handle error 50024: Cannot execute action on this channel type
            if e.status == 400 and e.code == 50024:
                logger.error(
                    f"Error 50024: Cannot create thread in channel type. "
                    f"Channel: {self.channel.name} (Type: {type(self.channel).__name__}). "
                    f"Message ID: {message.id}. Thread name: '{name}'"
                )
                return None

            logger.warning(
                f"HTTP error creating thread '{name}': {e.status} (code: {e.code}) - {e.text}"
            )
            return None

        except Exception as e:
            logger.error(
                f"Unexpected error creating thread '{name}': {e}", exc_info=True
            )
            return None

    async def _create_standalone_thread(self, name: str) -> Optional[discord.Thread]:
        """Create a standalone thread (not from a message)."""
        try:
            return await self.channel.create_thread(
                name=name, type=discord.ChannelType.public_thread
            )
        except discord.Forbidden as e:
            logger.warning(f"Insufficient permissions to create thread '{name}': {e}")
            return None
        except discord.HTTPException as e:
            logger.warning(
                f"HTTP error creating thread '{name}': {e.status} - {e.text}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error creating thread '{name}': {e}", exc_info=True
            )
            return None
