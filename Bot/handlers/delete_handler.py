import json
import os
import logging
import time
import re  # Added import
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Store states for delete confirmation
delete_states: Dict[int, Any] = {}

def handle_delete_command(bot, message):
    """Handle the /delete command."""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
        
        if not os.path.exists(db_path) or not json.load(open(db_path, 'r')):
            bot.reply_to(message, "❌ No links stored to delete.")
            return

        with open(db_path, 'r') as f:
            data = json.load(f)

        # Cache the data
        delete_states[message.chat.id] = {
            'data': data,
            'awaiting_confirmation': False
        }

        response = (
            "*🗑️ Delete Links:*\n\n"
            "_Send numbers to delete specific links:_\n"
            "• Single number (e.g., `2`)\n"
            "• Multiple numbers (e.g., `1,3,4`)\n"
            "• Type `all` to delete everything\n\n"
            "*Stored Links:*\n\n"
        )

        for index, (url, info) in enumerate(data.items(), 1):
            title = info['metadata']['title'][:47] + "..." if len(info['metadata']['title']) > 50 else info['metadata']['title']
            response += f"{index}. [{title}]({url})\n\n"

        bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error in delete command: {e}")
        bot.reply_to(message, "⚠️ An error occurred while retrieving links.")

def handle_delete_selection(bot, message):
    try:
        chat_id = message.chat.id
        user_input = message.text.strip()
        logger.info(f"[DELETE] New input received: '{user_input}' from chat_id: {chat_id}")

        if chat_id not in delete_states:
            logger.warning(f"[DELETE] State not found for chat_id: {chat_id}")
            bot.reply_to(message, "❌ Please use /del or /delete command first.")
            return

        # Handle numbers with both commas and spaces
        numbers = []
        # Split by both comma and space
        parts = [part.strip() for part in re.split(r'[,\s]+', user_input) if part.strip()]
        
        for part in parts:
            try:
                num = int(part)
                numbers.append(num)
                logger.info(f"[DELETE] Parsed number: {num}")
            except ValueError:
                logger.warning(f"[DELETE] Invalid number: {part}")
                continue

        # Process each number
        deleted_items = []
        state = delete_states[chat_id]
        urls = list(state['data'].keys())
        
        for num in numbers:
            if 1 <= num <= len(urls):
                url = urls[num - 1]
                title = state['data'][url]['metadata']['title']
                deleted_items.append(title)
                state['data'].pop(url)
                logger.info(f"[DELETE] Successfully deleted item {num}: {title}")
            else:
                logger.warning(f"[DELETE] Number out of range: {num}")

        # Save changes
        if deleted_items:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
            with open(db_path, 'w') as f:
                json.dump(state['data'], f, indent=4)
            
            # Format response
            response = "✅ Deleted:\n" + "\n".join(f"{i}. *{title}*" for i, title in enumerate(deleted_items, 1))
            logger.info(f"[DELETE] Sending success response with {len(deleted_items)} items")
            bot.reply_to(message, response, parse_mode="Markdown")
        else:
            logger.warning("[DELETE] No valid items to delete")
            bot.reply_to(message, "❌ No valid items to delete")

        delete_states.pop(chat_id)

    except Exception as e:
        logger.error(f"[DELETE] Error in delete selection: {str(e)}", exc_info=True)
        bot.reply_to(message, "⚠️ An error occurred while deleting.")

def cleanup_delete_states() -> None:
    """Remove old delete states after timeout."""
    current_time = time.time()
    timeout = 300  # 5 minutes
    
    to_remove = [
        chat_id for chat_id, state in delete_states.items()
        if current_time - state.get('timestamp', 0) > timeout
    ]
    
    for chat_id in to_remove:
        delete_states.pop(chat_id, None)