# Quick Start - Google Drive Backup System

## Installation (5 minutes)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test Local Backups (Works Immediately)
```bash
python test_google_drive_backup.py
```

You should see:
```
✓ PASS: BackupManager
✓ PASS: GoogleDriveManager
```

---

## Using the System

### Local Backups Only (No Google Drive)
```bash
python main.py
# Select option 3 (Create Backup)
# Answer "No" when asked about Google Drive
```

✓ Works immediately - no configuration needed

### With Google Drive (Optional)

#### Step 1: Create Google Service Account
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable Google Drive API
4. Create service account → Create JSON key
5. Download the JSON file

#### Step 2: Save Credentials
```bash
# Copy the JSON file to:
system_manager_cli/google_drive_credentials.json
```

#### Step 3: Share Google Drive Folder
1. Get the service account email from the JSON
2. Create a folder in your Google Drive
3. Share it with that email address

#### Step 4: Use the System
```bash
python main.py
# Select option 3 (Create Backup)
# Answer "Yes" when asked about Google Drive
```

---

## Error Messages & Solutions

### "Google Drive credentials file not found"
**Solution**: Make sure `google_drive_credentials.json` is in the system_manager_cli folder

### "Google API libraries not installed"
**Solution**: 
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "Failed to authenticate with Google Drive"
**Solution**: 
- Check service account has access to the shared folder
- Verify JSON file format is correct
- Check Google Drive API is enabled in console

### "Backup file not found"
**Solution**: Make sure the source folder exists and is readable

---

## Features

✓ Local backup creation  
✓ Automatic compression (zip)  
✓ Backup history management  
✓ Google Drive cloud storage  
✓ Automatic old backup cleanup  
✓ Full error logging  

---

## File Structure After Setup

```
system_manager_cli/
├── main.py                      # Main CLI tool
├── backup_manager.py            # Backup functionality
├── google_drive_manager.py      # Google Drive integration
├── google_drive_credentials.json # (Optional) Put your credentials here
├── requirements.txt             # Python dependencies
├── logs/                        # Backup logs
│   └── backup_manager.log
└── test_google_drive_backup.py  # Testing script
```

---

## Troubleshooting

### Check Backup Logs
```bash
tail -f logs/backup_manager.log
```

### Run Diagnostic Test
```bash
python test_google_drive_backup.py
```

### Manual Backup Creation
```python
from backup_manager import BackupManager

mgr = BackupManager("path/to/folder")
result = mgr.create_backup(compress=True)
print(f"Backup created: {result}")
```

---

## Support Files

- **[BUG_FIXES.md](BUG_FIXES.md)** - What was fixed
- **[FIXES_COMPLETE.md](FIXES_COMPLETE.md)** - Complete fix report
- **[GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md)** - Detailed setup guide
- **[GOOGLE_DRIVE_QUICK_REFERENCE.md](GOOGLE_DRIVE_QUICK_REFERENCE.md)** - Quick reference

---

## Next Steps

1. ✓ Install dependencies: `pip install -r requirements.txt`
2. ✓ Test the system: `python test_google_drive_backup.py`
3. ? (Optional) Configure Google Drive for cloud backups
4. ✓ Use: `python main.py` → Select option 3

---

**System Status**: ✅ Ready to Use

All bugs have been fixed. Local backups work immediately. Google Drive integration is optional.
