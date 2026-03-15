# System Manager CLI Tool

A comprehensive command-line tool for system monitoring, file management, backups, and log analysis.

## 🔐 New: User Login System (v1.0)

This tool now requires **email-based authentication** to access features. 

### Quick Start:
```bash
python main.py              # Run the tool
# Select Register for new users, Login for existing users
```

### Features:
- 📧 Email-based user authentication
- 🔐 Secure password hashing (SHA256)
- 🕒 8-hour session management
- 🛡️ Password strength requirements (8+ chars, 1 uppercase, 1 digit)

**See [LOGIN_GUIDE.md](LOGIN_GUIDE.md) and [LOGIN_QUICK_REFERENCE.md](LOGIN_QUICK_REFERENCE.md) for details**

---

## Features

### 1. **Check System Health** 🏥
Monitor your system in real-time:
- CPU usage monitoring
- RAM usage tracking
- Disk space analysis
- Automatic email alerts when thresholds are exceeded

### 2. **Clean Temporary Files** 🧹
Organize and clean your folders:
- Auto-organize files by type (Images, Documents, Videos, Audio, Archives, Code)
- Clean and standardize file names
- Detect and delete duplicate files automatically
- Generate detailed organization reports

### 3. **Backup Folders** 💾
Automated backup management:
- Backup important folders automatically
- Optional compression to ZIP format
- **NEW: Upload to Google Drive with your email** ☁️
- Choose to use login email or different email for Google Drive
- Keeps only the last 7 backups to save space
- Complete logging of all backup operations
- Easy backup listing and management

**See [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) and [GOOGLE_DRIVE_QUICK_REFERENCE.md](GOOGLE_DRIVE_QUICK_REFERENCE.md) for Google Drive backup setup**

### 4. **Generate System Report** 📊
Analyze log files and generate reports:
- Parse system and application log files
- Detect errors and warnings
- Count failed login attempts
- Export analysis to CSV format
- Support for single files or entire folders

## Installation

1. **Clone or download the tool**
```bash
cd system_manager_cli
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure settings**
Edit the `.env` file with your preferences:
```
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@gmail.com
CPU_THRESHOLD=80
RAM_THRESHOLD=85
DISK_THRESHOLD=90
BACKUP_DRIVE=D:\Backups
MAX_BACKUPS=7
```

4. **Run setup (optional)**
```bash
python main.py setup
```

## Usage

### Check System Health
```bash
python main.py check-health
python main.py check-health --email
```

### Clean Temporary Files
```bash
python main.py clean-temp "C:\Users\YourUsername\AppData\Local\Temp"
python main.py clean-temp "C:\Users\YourUsername\AppData\Local\Temp" --rename --delete-duplicates
```

### Backup Folders
```bash
python main.py backup-folder "C:\Important\Folder"
python main.py backup-folder "C:\Important\Folder" --compress
python main.py backup-folder "C:\Important\Folder" --list
```

### Generate System Report
```bash
python main.py generate-report "C:\Logs\event.log"
python main.py generate-report "C:\Logs" --export
```

## Directory Structure

```
system_manager_cli/
├── main.py                 # CLI entry point
├── config.py              # Configuration management
├── logger.py              # Logging setup
├── health_monitor.py      # System health monitoring
├── file_organizer.py      # File organization and cleanup
├── backup_manager.py      # Backup management
├── log_analyzer.py        # Log file analysis
├── requirements.txt       # Python dependencies
├── .env                   # Configuration file
├── README.md             # This file
├── logs/                 # Log files directory
├── reports/              # Generated reports directory
└── syntaxes/             # Language syntax files
```

## Output

All operations generate:
- **Log files** in the `logs/` directory
- **Reports** in the `reports/` directory
- **Console output** with progress and results

## Configuration

Edit `.env` file to customize:
- Email alerts (sender, password, recipient)
- Alert thresholds (CPU, RAM, Disk)
- Backup location and retention
- Temp folder paths

## Requirements

- Python 3.7+
- `click` - For CLI interface
- `psutil` - For system monitoring
- `python-dotenv` - For configuration management

## Examples

### Monitor System Every Hour
```bash
# On Windows, use Task Scheduler to run:
python "C:\path\to\main.py" check-health
```

### Clean Downloads Folder Weekly
```bash
python main.py clean-temp "C:\Users\YourUsername\Downloads"
```

### Backup Documents Daily
```bash
python main.py backup-folder "C:\Users\YourUsername\Documents"
```

### Analyze System Logs
```bash
python main.py generate-report "C:\Windows\System32\winevt\Logs"
```

## Error Handling

The tool includes comprehensive error handling:
- All errors are logged to files
- Console output shows user-friendly messages
- Failed operations don't stop the process
- Detailed error messages for debugging

## Support

For issues or questions:
1. Check the log files in the `logs/` directory
2. Verify your configuration in `.env`
3. Ensure all paths exist and are accessible
4. Make sure email credentials are correct

## License

All rights reserved.

## Changelog

### Version 1.0.0
- Initial release
- System health monitoring
- File organization and deduplication
- Backup management
- Log analysis and reporting
