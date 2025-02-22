import logging
import telebot
import sys
import os
import time  # Added import
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from telebot.types import Message
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot import asyncio_filters
from collections import defaultdict

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

# Rate limiting
RATE_LIMIT = 2  # seconds between messages
last_message_time: Dict[int, float] = defaultdict(float)

def rate_limit_check(message: Message) -> bool:
    """Check if user is sending messages too quickly."""
    user_id = message.from_user.id
    current_time = time.time()
    
    if current_time - last_message_time[user_id] < RATE_LIMIT:
        return False
    
    last_message_time[user_id] = current_time
    return True

# Initialize bot with state storage
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

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

@bot.message_handler(commands=['help', 'start'])
def help_command(message: Message) -> None:
    """Display bot usage information."""
    help_text = (
        "*📚 MetaMind Bot Commands:*\n\n"
        "• Send any URL to extract metadata\n"
        "• /list - Show all stored links\n"
        "• /delete - Delete specific or all links\n"
        "• /help - Show this message\n\n"
        "_Reply with numbers when prompted to select items._"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# Start polling
if __name__ == "__main__":
    logger.info("MetaMind Bot is running...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(15)  # Wait before retrying
