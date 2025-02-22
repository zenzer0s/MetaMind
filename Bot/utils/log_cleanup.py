import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def cleanup_logs(log_file: str) -> None:
    """Clean up log file every 5 minutes."""
    try:
        if not os.path.exists(log_file):
            return

        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{log_file}.{timestamp}"
        
        # Rename current log to backup
        os.rename(log_file, backup_file)
        
        # Create new empty log file
        with open(log_file, 'w') as f:
            f.write(f"Log file rotated at {datetime.now().isoformat()}\n")
        
        logger.info(f"Log file rotated. Backup created: {backup_file}")

        # Keep only last 3 backups
        backup_files = [f for f in os.listdir(os.path.dirname(log_file)) 
                       if f.startswith('bot.log.')]
        backup_files.sort(reverse=True)
        
        for old_backup in backup_files[3:]:
            try:
                os.remove(os.path.join(os.path.dirname(log_file), old_backup))
                logger.info(f"Deleted old backup: {old_backup}")
            except Exception as e:
                logger.error(f"Error deleting old backup {old_backup}: {e}")

    except Exception as e:
        logger.error(f"Error in log cleanup: {str(e)}")