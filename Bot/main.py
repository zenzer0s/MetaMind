import logging
import telebot
import sys
import os
import time  # Added import
import re  # Add this import at the top
import logging.handlers  # Add after imports
import threading  # Add this import
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from telebot.types import Message
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot import asyncio_filters
from collections import defaultdict
from utils.log_cleanup import cleanup_logs  # Add to imports section at top
from utils.messages import SUCCESS_MESSAGES, ERROR_MESSAGES
from utils.metadata import extract_metadata, store_metadata

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure the project directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.metadata import extract_metadata
from handlers.list_handler import handle_list_command, handle_number_selection
from handlers.delete_handler import (
    handle_delete_command, 
    handle_delete_selection, 
    delete_states,
    cleanup_delete_states  # Add this import
)

# Add this function after imports
def extract_url(text: str) -> str:
    """Extract URL from message text."""
    # Pattern to match URLs
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_pattern, text)
    return urls[0] if urls else None

def ensure_project_structure():
    """Ensure required directories exist."""
    dirs = [
        'Bot/logs',
        'Bot/data',
        'Bot/utils',
        'Bot/handlers'
    ]
    
    for dir_path in dirs:
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            logger.info(f"Created directory: {dir_path}")

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

# Ensure project structure before bot initialization
ensure_project_structure()

# Initialize bot with state storage
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Console handler
        logging.StreamHandler(),
        # File handler
        logging.handlers.RotatingFileHandler(
            'Bot/logs/bot.log',
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

@bot.message_handler(func=lambda message: message.text and ('http://' in message.text.lower() or 'https://' in message.text.lower()))
def handle_link(message: Message) -> None:
    """Handle messages containing URLs."""
    try:
        url = extract_url(message.text)
        if not url:
            bot.reply_to(message, ERROR_MESSAGES['invalid_url'])
            return

        logger.info(f"Extracted URL: {url}")
        metadata = extract_metadata(url)

        if "error" in metadata:
            bot.reply_to(message, ERROR_MESSAGES['metadata_error'])
            return

        # Store the metadata
        store_metadata(url, metadata)
        
        # Format success message
        response = SUCCESS_MESSAGES['link_added'].format(
            title=metadata.get('title', 'No title')
        )
        bot.reply_to(message, response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error processing link: {e}")
        bot.reply_to(message, ERROR_MESSAGES['general_error'])

# Add this after your other handlers
@bot.message_handler(commands=['list'])
def list_command(message):
    handle_list_command(bot, message)

# Update the delete command handler to include 'del' alias
@bot.message_handler(commands=['delete', 'del'])
def delete_command(message):
    handle_delete_command(bot, message)

# Update the delete selection handler to better handle spaces
@bot.message_handler(func=lambda message: message.text and 
                    (message.text.isdigit() or ',' in message.text or 
                     ' ' in message.text.strip() or message.text.lower() in ['all', 'yes']))
def delete_selection(message):
    logger.info(f"[MAIN] Received message: '{message.text}'")
    if message.chat.id in delete_states:
        handle_delete_selection(bot, message)
    else:
        logger.info("[MAIN] Not in delete state, passing to number selection")
        handle_number_selection(message)

@bot.message_handler(func=lambda message: message.text and message.text.isdigit())
def number_selection(message):
    handle_number_selection(message)

@bot.message_handler(commands=['help', 'start'])
def help_command(message: Message) -> None:
    """Display bot usage information."""
    help_text = (
        "*🤖 Welcome to MetaMind Bot!*\n\n"
        "*Available Commands:*\n"
        "📎 Send any URL to extract metadata\n"
        "📋 /list - Browse your saved links\n"
        "🗑️ /del - Delete links\n"
        "❓ /help - Show this message\n\n"
        "*Quick Tips:*\n"
        "• Reply with numbers to select items\n"
        "• Delete multiple links using:\n"
        "  └ Comma format: `1,2,3`\n"
        "  └ Space format: `1 2 3`\n\n"
        "_Made with ❤️ by MetaMind_"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

def cleanup_thread():
    """Thread to clean up logs and states every 5 minutes."""
    while True:
        try:
            # Clean up delete states
            cleanup_delete_states()
            
            # Clean up log file
            log_file = 'Bot/logs/bot.log'
            cleanup_logs(log_file)
            
            # Wait for 5 minutes
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error in cleanup thread: {e}")
            time.sleep(300)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_thread, daemon=True)
cleanup_thread.start()

# Start polling
if __name__ == "__main__":
    logger.info("MetaMind Bot is running...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(15)  # Wait before retrying
