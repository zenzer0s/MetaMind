import os

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.json')

# Bot settings
DEFAULT_PARSE_MODE = "Markdown"
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'