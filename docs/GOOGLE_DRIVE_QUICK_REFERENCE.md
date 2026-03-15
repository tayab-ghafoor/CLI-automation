# Google Drive Backup - Quick Reference

## Setup (One-Time)

1. **Install libraries:**
   ```bash
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

2. **Create Google Cloud credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create project → Enable Google Drive API → Create Service Account
   - Download JSON key

3. **Place credentials file:**
   - Rename: `google_drive_credentials.json`
   - Location: `system_manager_cli/` folder

4. **Share Google Drive folder:**
   - Create/select folder on Google Drive
   - Share with service account email (from JSON)
   - Set permission to "Editor"

## Backup Flow

```
python main.py
   ↓
Login with email
   ↓
Select: 3. Backup Folder 💾
   ↓
Enter folder path
   ↓
Compress? [Y/n]: y
   ↓
✅ Backup created locally
   ↓
Google Drive prompt:
"Do you want to backup to Google Drive?" 
   ↓
[Option 1] Use same email
[Option 2] Enter different email
   ↓
✅ Upload to Google Drive
```

## Command Examples

### Backup with Google Drive

```bash
python main.py
# Select: 3. Backup Folder 💾
# Enter folder path: D:\Documents
# Compress: y
# Google Drive: y
# Same email: y/n
# Done! ✅
```

### Local Backup Only

```bash
python main.py
# Select: 3. Backup Folder 💾
# Enter folder path: D:\Documents
# Compress: y
# Google Drive: n
# Done! ✅
```

## Features

| Feature | Status |
|---------|--------|
| Local backup | ✅ Always created |
| Compress to ZIP | ✅ Optional |
| Google Drive upload | ✅ Optional |
| Choose email | ✅ Same or different |
| Folder organization | ✅ Automatic |
| Multiple backups | ✅ Supported |

## Email Options

### Option 1: Same Email
```
Login email: john@gmail.com
Google Drive email: john@gmail.com (default)
```

### Option 2: Different Email
```
Login email: john@gmail.com
Google Drive email: backup@company.com (custom)
```

## File Organization

```
Google Drive / System Backups /
├── 📄 folder_20260221_100530.zip     (2.5 GB)
├── 📄 folder_20260221_111245.zip     (3.1 GB)
└── 📄 project_20260221_120000.zip    (1.8 GB)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Libraries not installed | `pip install google-auth-*` |
| Credentials file missing | Place `google_drive_credentials.json` in system_manager_cli/ |
| Upload fails | Share Google Drive folder with service account |
| Permission denied | Set folder permission to "Editor" |

## File Size Limits

- **Per file:** 5TB (Google Drive limit)
- **Storage:** Your Google Drive quota
- **Compression:** Reduces size by 40-70%

## Data Location

```
Local: D:\Backups\system_backups\     (or configured backup drive)
Cloud: Google Drive / System Backups /
```

## Restore

1. Go to Google Drive
2. Download backup ZIP file
3. Extract to desired location
4. Restore files

## Log Location

```
system_manager_cli/logs/
  └── backup_manager.log
  └── google_drive_manager.log
```

## Examples

### Example 1: First-Time Backup
```
Email: john@example.com
Folder: D:\MyProjects
Compress: Yes
Google Drive: Yes
Same Email: Yes
Result: Backup saved locally + uploaded to john@example.com's Drive
```

### Example 2: Work Backup
```
Email: john@gmail.com
Folder: D:\WorkData
Compress: Yes
Google Drive: Yes
Same Email: No
Alternative Email: john.work@company.com
Result: Backup saved locally + uploaded to company Google Drive
```

### Example 3: Local Only
```
Email: john@gmail.com
Folder: D:\Desktop
Compress: Yes
Google Drive: No
Result: Backup saved locally only
```

## Important Notes

⚠️ **Security:**
- Keep `google_drive_credentials.json` private
- Don't commit to version control
- Add to `.gitignore`

💡 **Tips:**
- Compress backups to save storage space
- Use different email for work vs personal
- Check Google Drive folder regularly
- Verify upload success in logs

✅ **Best Practices:**
- Regular backups scheduled daily/weekly
- Monitor Google Drive storage
- Test restore process occasionally
- Keep credentials file backed up (securely)

## Status Check

- Local backup: ✅ Created successfully
- Google Drive: ❓ (depends on credentials setup)
- Compression: ✅ Optional
- Email options: ✅ Same or different

## Quick Checklist

```
☐ Install Google libraries
☐ Create Google Cloud project
☐ Create Service Account
☐ Download credentials JSON
☐ Place credentials in correct folder
☐ Create Google Drive folder
☐ Share folder with service account
☐ Test backup with Google Drive upload
☐ Verify upload in Google Drive
☐ Done! 🎉
```

---

**For detailed setup:** See `GOOGLE_DRIVE_SETUP.md`

**Version:** System Manager CLI v1.0
**Date:** February 21, 2026
