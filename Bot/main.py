import os
import logging
import telebot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start Command Handler
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.reply_to(message, "🚀 Welcome to MetaMind Bot! Send a link, and I'll categorize it for you.")

# Run the bot
if __name__ == "__main__":
    logger.info("MetaMind Bot is running...")
    bot.polling(none_stop=True)
