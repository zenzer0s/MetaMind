import json
import os
import logging
from telebot.handler_backends import State

logger = logging.getLogger(__name__)

# Store global reference to data
cached_data = {}

def handle_list_command(bot, message):
    """Handle the /list command by displaying numbered links."""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.json')
        
        if not os.path.exists(db_path):
            bot.reply_to(message, "❌ No links have been stored yet.")
            return

        with open(db_path, 'r') as f:
            data = json.load(f)

        if not data:
            bot.reply_to(message, "📝 No links have been stored yet.")
            return

        # Cache the data for number selection
        global cached_data
        cached_data = data

        response = "*📚 Stored Links:*\n\n"
        for index, (url, info) in enumerate(data.items(), 1):
            metadata = info['metadata']
            title = metadata['title']
            if len(title) > 50:
                title = title[:47] + "..."
            response += f"{index}. [{title}]({url})\n\n"

        response += "\n_Reply with a number to see full details._"

        if len(response) > 4000:
            response = response[:3900] + "\n\n_(Some links not shown due to length limit)_"

        bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error in list command: {e}")
        bot.reply_to(message, "⚠️ An error occurred while retrieving the links.")

def handle_number_selection(message):
    """Handle numeric selection to show full details of a specific link."""
    try:
        from telebot import TeleBot
        bot = TeleBot(os.getenv("BOT_TOKEN"))
        
        number = int(message.text)
        if not cached_data:
            bot.reply_to(message, "❌ Please use /list command first.")
            return

        if number < 1 or number > len(cached_data):
            bot.reply_to(message, "❌ Invalid number. Please choose from the list.")
            return

        # Get the selected item
        url = list(cached_data.keys())[number - 1]
        info = cached_data[url]
        metadata = info['metadata']

        # Format detailed response
        response = (
            f"*🔗 Link Details #{number}*\n\n"
            f"*Title:* {metadata['title']}\n\n"
            f"*Description:* _{metadata['description']}_\n\n"
            f"*URL:* [{url}]({url})"
        )

        bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error handling number selection: {e}")
        bot.reply_to(message, "⚠️ An error occurred while retrieving the details.")