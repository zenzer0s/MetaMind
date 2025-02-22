import logging
import telebot
import sys
import os
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure the project directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.metadata import extract_metadata
  # Import after fixing sys.path

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
def handle_link(message):
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

# Start polling
if __name__ == "__main__":
    logger.info("MetaMind Bot is running...")
    bot.polling(none_stop=True)
