import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Store states for delete confirmation
delete_states: Dict[int, Any] = {}

def handle_delete_command(bot, message):
    """Handle the /delete command by displaying numbered links."""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
        
        if not os.path.exists(db_path):
            bot.reply_to(message, "❌ No links stored to delete.")
            return

        with open(db_path, 'r') as f:
            data = json.load(f)

        if not data:
            bot.reply_to(message, "❌ No links stored to delete.")
            return

        # Cache the data for number selection
        delete_states[message.chat.id] = {
            'data': data,
            'awaiting_confirmation': False
        }

        response = "*🗑️ Select a link to delete:*\n\n"
        for index, (url, info) in enumerate(data.items(), 1):
            metadata = info['metadata']
            title = metadata['title']
            if len(title) > 50:
                title = title[:47] + "..."
            response += f"{index}. [{title}]({url})\n\n"

        response += "\n_Reply with a number to delete that link, or 'all' to clear everything._"

        bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error in delete command: {e}")
        bot.reply_to(message, "⚠️ An error occurred while retrieving the links.")

def handle_delete_selection(bot, message):
    """Handle delete selection and confirmation."""
    try:
        chat_id = message.chat.id
        if chat_id not in delete_states:
            bot.reply_to(message, "❌ Please use /delete command first.")
            return

        state = delete_states[chat_id]
        
        # Handle "delete all" confirmation
        if state.get('awaiting_confirmation'):
            if message.text.lower() == 'yes':
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
                with open(db_path, 'w') as f:
                    json.dump({}, f)
                bot.reply_to(message, "✅ All links have been deleted.")
            else:
                bot.reply_to(message, "❌ Deletion cancelled.")
            delete_states.pop(chat_id)
            return

        # Handle "delete all" request
        if message.text.lower() == 'all':
            state['awaiting_confirmation'] = True
            bot.reply_to(message, "⚠️ Are you sure you want to delete ALL links? Reply 'yes' to confirm.")
            return

        # Handle single deletion
        try:
            number = int(message.text)
            if number < 1 or number > len(state['data']):
                bot.reply_to(message, "❌ Invalid number. Please choose from the list.")
                return

            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
            url = list(state['data'].keys())[number - 1]
            title = state['data'][url]['metadata']['title']

            # Remove the entry
            state['data'].pop(url)
            with open(db_path, 'w') as f:
                json.dump(state['data'], f, indent=4)

            bot.reply_to(message, f"✅ Deleted: *{title}*", parse_mode="Markdown")
            delete_states.pop(chat_id)

        except ValueError:
            bot.reply_to(message, "❌ Please enter a valid number or 'all'.")

    except Exception as e:
        logger.error(f"Error handling delete selection: {e}")
        bot.reply_to(message, "⚠️ An error occurred while deleting.")