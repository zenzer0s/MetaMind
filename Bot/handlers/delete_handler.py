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
    """Handle delete selection including multiple numbers."""
    try:
        chat_id = message.chat.id
        if chat_id not in delete_states:
            bot.reply_to(message, "❌ Please use /delete command first.")
            return

        state = delete_states[chat_id]
        
        # Handle "all" deletion confirmation
        if state.get('awaiting_confirmation'):
            if message.text.lower() == 'yes':
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
                with open(db_path, 'w') as f:
                    json.dump({}, f, indent=4)
                bot.reply_to(message, "✅ All links have been deleted.")
            else:
                bot.reply_to(message, "❌ Deletion cancelled.")
            delete_states.pop(chat_id)
            return

        # Handle "all" request
        if message.text.lower() == 'all':
            state['awaiting_confirmation'] = True
            bot.reply_to(message, "⚠️ Are you sure you want to delete ALL links? Reply 'yes' to confirm.")
            return

        # Handle multiple number deletion
        try:
            # Parse numbers from input (e.g., "1,3,4" or "1 3 4")
            numbers = [int(n.strip()) for n in re.split(r'[,\s]+', message.text)]
            
            if not numbers:
                bot.reply_to(message, "❌ Please enter valid numbers.")
                return

            # Validate numbers
            if any(n < 1 or n > len(state['data']) for n in numbers):
                bot.reply_to(message, "❌ Invalid number(s). Please choose from the list.")
                return

            # Get URLs to delete
            urls_to_delete = [list(state['data'].keys())[n - 1] for n in numbers]
            
            # Delete entries
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
            deleted_titles = []
            
            for url in urls_to_delete:
                title = state['data'][url]['metadata']['title']
                deleted_titles.append(title)
                state['data'].pop(url)

            # Save updated data
            with open(db_path, 'w') as f:
                json.dump(state['data'], f, indent=4)

            # Format response
            response = "✅ Deleted:\n"
            for i, title in enumerate(deleted_titles, 1):
                response += f"{i}. *{title}*\n"
            
            bot.reply_to(message, response, parse_mode="Markdown")
            delete_states.pop(chat_id)

        except ValueError:
            bot.reply_to(message, "❌ Please enter valid numbers separated by commas or spaces.")

    except Exception as e:
        logger.error(f"Error handling delete selection: {e}")
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