import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project-local .env first.
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / '.env')
# Also allow environment variables from current shell to override.
load_dotenv(override=False)

class Config:
    """Configuration management for the CLI tool"""
    
    # Email settings
    EMAIL_SENDER = os.getenv('EMAIL_SENDER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 465))
    SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'true').lower() == 'true'
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'false').lower() == 'true'
    
    # Thresholds for alerts
    CPU_THRESHOLD = int(os.getenv('CPU_THRESHOLD', 80))
    RAM_THRESHOLD = int(os.getenv('RAM_THRESHOLD', 85))
    DISK_THRESHOLD = int(os.getenv('DISK_THRESHOLD', 90))
    
    # Backup settings (Local)
    BACKUP_DRIVE = os.getenv('BACKUP_DRIVE', 'D:\\Backups')
    MAX_BACKUPS = int(os.getenv('MAX_BACKUPS', 7))
    
    # Rclone settings (Cloud backup)
    RCLONE_REMOTE = os.getenv('RCLONE_REMOTE', 'gdrive')  # Default: gdrive, onedrive, dropbox, etc.
    RCLONE_BACKUP_PATH = os.getenv('RCLONE_BACKUP_PATH', '/backups')
    USE_RCLONE = os.getenv('USE_RCLONE', 'true').lower() == 'true'  # Enable cloud backup by default
    
    # Paths
    BASE_DIR = BASE_DIR
    LOGS_DIR = BASE_DIR / 'logs'
    REPORTS_DIR = BASE_DIR / 'reports'
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.REPORTS_DIR.mkdir(exist_ok=True)
