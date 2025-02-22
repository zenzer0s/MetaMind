import logging
import telebot
import sys
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from telebot.types import Message

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure the project directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.metadata import extract_metadata
from handlers.list_handler import handle_list_command, handle_number_selection
from handlers.delete_handler import handle_delete_command, handle_delete_selection, delete_states  # Added delete_states

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing! Check your .env file.")

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Handle link messages
@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def handle_link(message: Message) -> None:
    logger.info(f"Received link: {message.text}")  # Debug log
    bot.send_message(message.chat.id, "🔍 Extracting metadata...")

    try:
        metadata = extract_metadata(message.text)

        if "error" in metadata:
            bot.send_message(message.chat.id, f"❌ Error: {metadata['error']}")
        else:
            response = (
                f"*Title:* {metadata['title']}\n"
                f"*Description:* {metadata['description']}"
            )
            bot.send_message(message.chat.id, response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error processing link: {e}")
        bot.send_message(message.chat.id, "⚠️ Something went wrong! Please try again.")

# Add this after your other handlers
@bot.message_handler(commands=['list'])
def list_command(message):
    handle_list_command(bot, message)

@bot.message_handler(commands=['delete'])
def delete_command(message):
    handle_delete_command(bot, message)

@bot.message_handler(func=lambda message: message.text and 
                    (message.text.isdigit() or message.text.lower() in ['all', 'yes']))
def delete_selection(message):
    # Check if it's a delete operation
    if message.chat.id in delete_states:
        handle_delete_selection(bot, message)
    else:
        handle_number_selection(message)

@bot.message_handler(func=lambda message: message.text and message.text.isdigit())
def number_selection(message):
    handle_number_selection(message)

# Start polling
if __name__ == "__main__":
    logger.info("MetaMind Bot is running...")
    bot.polling(none_stop=True)
