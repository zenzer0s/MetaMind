import json
import os
import logging
from telebot.handler_backends import State

logger = logging.getLogger(__name__)

def handle_list_command(bot, message):
    """Handle the /list command by displaying stored links with shortened titles."""
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

        response = "*Stored Links:*\n\n"
        for url, info in data.items():
            metadata = info['metadata']
            
            # Shorten title if longer than 50 characters
            title = metadata['title']
            if len(title) > 50:
                title = title[:47] + "..."
            
            # Format as clickable link with shortened title
            response += f"• [{title}]({url})\n"
            
            # Add description if available
            description = metadata.get('description', '').strip()
            if description:
                if len(description) > 100:
                    description = description[:97] + "..."
                response += f"  _{description}_\n"
            response += "\n"

        # Handle Telegram's message length limit
        if len(response) > 4000:
            response = response[:3900] + "\n\n_(More links available but not shown due to length limit)_"

        bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Error in list command: {e}")
        bot.reply_to(message, "⚠️ An error occurred while retrieving the links.")