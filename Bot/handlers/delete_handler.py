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
            'awaiting_confirmation': False,
            'timestamp': time.time()  # Add timestamp
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
        user_input = message.text.strip().lower()
        logger.info(f"[DELETE] New input received: '{user_input}' from chat_id: {chat_id}")

        if chat_id not in delete_states:
            logger.warning(f"[DELETE] State not found for chat_id: {chat_id}")
            bot.reply_to(message, "❌ Please use /del or /delete command first.")
            return

        state = delete_states[chat_id]

        # Handle confirmation for multiple deletions
        if state.get('awaiting_confirmation'):
            if user_input == 'yes':
                numbers = state.get('pending_numbers', [])
                urls = list(state['data'].keys())
                deleted_items = []

                for num in numbers:
                    if 1 <= num <= len(urls):
                        url = urls[num - 1]
                        title = state['data'][url]['metadata']['title']
                        deleted_items.append(title)
                        state['data'].pop(url)
                        logger.info(f"[DELETE] Successfully deleted item {num}: {title}")

                # Save changes
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
                with open(db_path, 'w') as f:
                    json.dump(state['data'], f, indent=4)

                response = "✅ Deleted:\n" + "\n".join(f"{i}. *{title}*" for i, title in enumerate(deleted_items, 1))
                bot.reply_to(message, response, parse_mode="Markdown")
            else:
                bot.reply_to(message, "❌ Deletion cancelled.")
            
            delete_states.pop(chat_id)
            return

        # Handle new number input
        numbers = []
        parts = [part.strip() for part in re.split(r'[,\s]+', user_input) if part.strip()]
        
        for part in parts:
            try:
                num = int(part)
                numbers.append(num)
                logger.info(f"[DELETE] Parsed number: {num}")
            except ValueError:
                logger.warning(f"[DELETE] Invalid number: {part}")
                continue

        if not numbers:
            logger.warning("[DELETE] No valid numbers found")
            bot.reply_to(message, "❌ Please enter valid numbers.")
            return

        # Validate numbers
        if any(num < 1 or num > len(state['data']) for num in numbers):
            logger.warning("[DELETE] Numbers out of range")
            bot.reply_to(message, "❌ Invalid number(s). Please choose from the list.")
            return

        # Request confirmation for multiple deletions
        if len(numbers) > 1:
            state['pending_numbers'] = numbers
            state['awaiting_confirmation'] = True
            titles = [state['data'][list(state['data'].keys())[n-1]]['metadata']['title'] for n in numbers]
            confirm_text = "*❓ Confirm deletion of these items:*\n\n"
            for i, title in enumerate(titles, 1):
                confirm_text += f"{i}. *{title}*\n"
            confirm_text += "\n_Reply 'yes' to confirm or anything else to cancel_"
            
            bot.reply_to(message, confirm_text, parse_mode="Markdown")
            return

        # Handle single deletion
        url = list(state['data'].keys())[numbers[0] - 1]
        title = state['data'][url]['metadata']['title']
        state['data'].pop(url)

        # Save changes
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
        with open(db_path, 'w') as f:
            json.dump(state['data'], f, indent=4)

        bot.reply_to(message, f"✅ Deleted: *{title}*", parse_mode="Markdown")
        delete_states.pop(chat_id)

    except Exception as e:
        logger.error(f"[DELETE] Error in delete selection: {str(e)}", exc_info=True)
        bot.reply_to(message, "⚠️ An error occurred while deleting.")

def cleanup_delete_states() -> None:
    """Remove old delete states after timeout."""
    try:
        current_time = time.time()
        timeout = 300  # 5 minutes timeout

        # Find expired states
        expired_chats = [
            chat_id for chat_id, state in delete_states.items()
            if current_time - state.get('timestamp', 0) > timeout
        ]

        # Remove expired states
        for chat_id in expired_chats:
            delete_states.pop(chat_id, None)
            logger.info(f"[DELETE] Cleaned up expired state for chat_id: {chat_id}")

    except Exception as e:
        logger.error(f"[DELETE] Error in cleanup: {str(e)}")