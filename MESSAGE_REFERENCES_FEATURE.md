# Message References Feature

## Overview

The bot now has the ability to see and understand messages that are referenced through replies or Discord message links. When a user mentions the bot and their message references other messages, the bot can access the content of those referenced messages and include them in its response.

## How It Works

### 1. Message Reference Detection

The bot automatically detects two types of message references:

- **Reply References**: When a user replies to a message and then mentions the bot
- **Message Links**: When a user includes Discord message links in their message (e.g., `https://discord.com/channels/guild_id/channel_id/message_id`)

### 2. Context Gathering

When processing a bot command, the system:

1. Checks if the user's message has a reply reference
2. Scans the message content for Discord message links
3. Fetches the content of any referenced/linked messages
4. Compiles this information into a context object

### 3. LLM Integration

The gathered context is formatted and included in the prompt sent to the LLM:

```
**Referenced Message (Reply):**
Author: OriginalUser
Time: 2024-01-01 12:00:00 UTC
Content: This is the original message content

**Linked Message 1:**
Author: AnotherUser
Time: 2024-01-01 11:00:00 UTC
Content: This is a linked message

**User's Question/Request:**
What does this message mean?
```

## Usage Examples

### Example 1: Reply Reference

1. User A posts: "I'm having trouble with my Python code"
2. User B replies to User A's message and mentions the bot: "@bot Can you help explain this error?"
3. The bot can see both User B's question AND User A's original message about Python code
4. The bot responds with context about the Python issue

### Example 2: Message Links

1. User posts: "@bot Please explain this discussion: https://discord.com/channels/123/456/789"
2. The bot fetches the message at that link
3. The bot responds with an explanation of the linked message content

### Example 3: Combined References

1. User replies to a message AND includes a link to another message
2. The bot can see the replied-to message, the linked message, AND the user's question
3. The bot provides a comprehensive response considering all context

## Technical Implementation

### Files Modified

- `command_handler.py`: Added message context gathering to bot command processing
- `llm_handler.py`: Updated to accept and format message context in LLM prompts
- `bot.py`: Updated to pass bot client to command handler
- `message_utils.py`: Already contained the core functionality for fetching references

### Key Functions

- `get_message_context(message, bot_client)`: Main function that gathers all message context
- `fetch_referenced_message(message)`: Fetches replied-to messages
- `fetch_message_from_link(link, bot)`: Fetches messages from Discord links
- `extract_message_links(text)`: Finds Discord message links in text

### Error Handling

The system gracefully handles various error conditions:

- Messages that can't be fetched (deleted, no permissions, etc.)
- Invalid message links
- Cross-channel references
- Network errors

If context gathering fails, the bot continues to work normally without the additional context.

## Benefits

1. **Better Context Understanding**: The bot can provide more relevant and helpful responses
2. **Conversation Continuity**: Users can reference previous discussions easily
3. **Cross-Channel References**: Users can link to messages from other channels
4. **Improved User Experience**: More natural conversation flow

## Privacy and Permissions

- The bot can only access messages in channels where it has read permissions
- The bot respects Discord's permission system
- No additional data is stored; context is gathered on-demand

## Testing

The feature includes comprehensive tests:

- Unit tests for individual functions (`test_message_references.py`)
- Integration tests for the complete flow (`test_integration_message_references.py`)
- Manual testing script (`test_manual_integration.py`)

## Future Enhancements

Potential improvements could include:

- Caching frequently referenced messages
- Supporting thread message references
- Adding visual indicators when context is included
- Limiting context size for very long referenced messages
