# Google Drive Backup Integration Guide

## Overview

The System Manager CLI now supports backing up your data directly to Google Drive. After creating a local backup, the software will ask if you want to upload it to Google Drive using your email address.

## Features

✅ **Automatic Google Drive Integration**
- Creates backups locally first
- Optionally uploads to Google Drive
- Choose same email or different email for Google Drive
- Organized backup folder on Google Drive

## Setup Instructions

### Step 1: Install Required Libraries

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or add to requirements.txt:
```
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
```

### Step 2: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project:
   - Click "Select a Project" → "New Project"
   - Enter project name (e.g., "System Manager Backups")
   - Click "Create"

### Step 3: Enable Google Drive API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

### Step 4: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in the details:
   - Service account name: "System Manager CLI"
   - Service account ID: (auto-filled)
   - Description: "For backing up system data to Google Drive"
   - Click "Create and Continue"

4. Grant permissions:
   - Click "Continue" (you can skip optional steps)
   - Click "Done"

### Step 5: Create and Download JSON Key

1. Go to "APIs & Services" → "Credentials"
2. Under "Service Accounts", click on the account you created
3. Go to "Keys" tab
4. Click "Add Key" → "Create new key"
5. Select "JSON" and click "Create"
6. The JSON file will download automatically

### Step 6: Place Credentials File

1. Rename the downloaded JSON file to: `google_drive_credentials.json`
2. Place it in the `system_manager_cli` folder (same location as `main.py`)

**Location:** `d:\python\system_manager_cli\google_drive_credentials.json`

### Step 7: Share Folder with Service Account

1. Open your Google Drive
2. Create a folder (or use existing): "Backups" or "System Backups"
3. Get the service account email from the JSON file (looks like: `xxx@xxx.iam.gserviceaccount.com`)
4. Share the folder with this email address with "Editor" permissions

## Usage

### During Backup

1. Run: `python main.py`
2. Login with your credentials
3. Select: "3. Backup Folder 💾"
4. Enter folder path to backup
5. Choose to compress (optional)
6. **New Step:** Choose email for Google Drive backup:
   ```
   Do you want to backup data to Google Drive on this email: your@email.com? [y/N]:
   ```
   - Type `y` to enable Google Drive backup
   - Type `n` to skip Google Drive backup

7. If you choose `y`, you'll be asked:
   ```
   Use the same email for Google Drive? [Y/n]:
   ```
   - Type `y` to use your login email
   - Type `n` to enter a different email

### Example Flow

```
✅ Backup created successfully!

==================================================
☁️  Google Drive Backup
==================================================

Do you want to backup data to Google Drive on this email: john@example.com? [y/N]: y
Use the same email for Google Drive? [Y/n]: y

🔄 Uploading backup to Google Drive...
✅ Backup uploaded to Google Drive successfully!
📧 Email: john@example.com
```

### Alternative Email

```
Do you want to backup data to Google Drive on this email: john@example.com? [y/N]: y
Use the same email for Google Drive? [Y/n]: n
Enter alternative email for Google Drive: work@company.com

🔄 Uploading backup to Google Drive...
✅ Backup uploaded to Google Drive successfully!
📧 Email: work@company.com
```

## File Organization on Google Drive

Your backups will be organized as follows:

```
Google Drive /
├── System Backups/
│   ├── folder_backup_20260221_100000.zip
│   ├── folder_backup_20260221_110530.zip
│   └── another_folder_backup_20260221_120000.zip
```

Each backup file includes:
- Original folder name
- Timestamp (YYYYMMDD_HHMMSS)
- .zip extension (compressed)

## Troubleshooting

### "Google API libraries not installed"

**Solution:**
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "Credentials file not found"

**Solution:**
1. Ensure `google_drive_credentials.json` is in the correct location
2. File should be in: `system_manager_cli/google_drive_credentials.json`
3. Follow "Step 6: Place Credentials File" above

### "Permission denied" or "Forbidden"

**Solution:**
1. Check that you shared the Google Drive folder with the service account email
2. Ensure permissions are set to "Editor" (not "Viewer")
3. Service account email format: `xxx@xxx.iam.gserviceaccount.com`

### "Failed to authenticate with Google"

**Solution:**
1. Delete `google_drive_token.json` if it exists
2. Verify the credentials JSON file is valid
3. Check that Google Drive API is enabled in Cloud Console
4. Verify service account has the correct permissions

### Upload fails silently

**Check the logs:**
```
system_manager_cli/logs/
```
Look for error messages related to Google Drive.

## Security Notes

⚠️ **Important:**
- Keep `google_drive_credentials.json` secure and private
- Do not share this file
- Do not commit to version control
- Add to `.gitignore` if using Git:
  ```
  google_drive_credentials.json
  google_drive_token.json
  ```

## Advanced: Using Multiple Google Accounts

You can backup to different Google Drive accounts by specifying different emails:

**Example:**
- Login with: `user1@gmail.com`
- Backup to Google Drive with: `user2@gmail.com` (if it's shared with service account)

## Limits and Considerations

- **File Size:** Google Drive has a 5TB per file limit
- **Storage Quota:** Your Google Drive storage limit applies
- **API Quota:** Free tier has rate limits (but high for personal use)
- **Security:** Backups are stored on Google's secure servers

## Backing Up Multiple Folders

```bash
# First backup
python main.py
# Backup folder1 → Upload to john@gmail.com

# Second backup (same session or new session)
# Backup folder2 → Upload to john@gmail.com

# Both backups will be stored in the same "System Backups" folder on Google Drive
```

## Disable Google Drive Backup

If you don't want to use Google Drive backup:
1. Simply answer "No" when asked to backup to Google Drive
2. Your local backup will still be created
3. No credentials file needed if not using this feature

## View Backups on Google Drive

1. Open Google Drive
2. Navigate to "System Backups" folder
3. You'll see all your backups with timestamps
4. Right-click to download, delete, or share

## Restore from Google Drive Backup

1. Go to "System Backups" folder on Google Drive
2. Download the backup file you need
3. Extract the ZIP file
4. Restore to desired location

## Migration to New Computer

1. Download all backups from Google Drive
2. Set up Google Drive credentials on new computer
3. Place credentials file in system_manager_cli folder
4. Restore from downloaded backups

## Support

For issues:
1. Check this guide in troubleshooting section
2. Review logs in `system_manager_cli/logs/`
3. Verify Google Cloud Console setup
4. Ensure all required libraries are installed

## Example Setup Summary

```
✓ Installed Google libraries
✓ Created Google Cloud Project
✓ Enabled Google Drive API
✓ Created Service Account
✓ Downloaded JSON key
✓ Placed credentials.json in correct folder
✓ Shared Google Drive folder with service account
✓ Tested backup with Google Drive upload

Ready to use! 🚀
```

---

**Version:** System Manager CLI v1.0 with Google Drive Backup
**Last Updated:** February 21, 2026
