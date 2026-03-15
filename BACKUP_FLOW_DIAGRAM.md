# Backup Process with Google Drive - Visual Flow

## Complete Backup Workflow

```
┌─────────────────────────────────────────────────┐
│         START APPLICATION                       │
│         python main.py                          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│      LOGIN/REGISTER MENU                        │
│   ┌─ 1. Register (New Users)                   │
│   ├─ 2. Login (Existing Users)                 │
│   └─ 3. Exit                                   │
└────────────────┬────────────────────────────────┘
                 │
            (User logs in)
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│       MAIN MENU (Authenticated)                 │
│   ┌─ 1. Check System Health                    │
│   ├─ 2. Clean Temporary Files                  │
│   ├─ 3. Backup Folder 💾 ◄─── NEW FLOW         │
│   ├─ 4. Generate System Report                 │
│   ├─ 5. Setup Configuration                    │
│   ├─ 6. View Profile                           │
│   ├─ 7. Change Password                        │
│   ├─ 8. Logout                                 │
│   └─ 9. Exit                                   │
└────────────────┬────────────────────────────────┘
                 │
        (User selects: 3)
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│    BACKUP FOLDER SELECTION                      │
│  "Enter folder path to backup"                  │
│  Example: D:\Documents                          │
└────────────────┬────────────────────────────────┘
                 │
      (Validate path & permissions)
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
   Valid                   Invalid
     │                       │
     │                  ❌ Error
     │                  Retry/Return
     │
     ▼
┌─────────────────────────────────────────────────┐
│   COMPRESSION OPTION                            │
│  "Compress backup to ZIP? [Y/n]"               │
│                                                 │
│  Yes ─────────────────────────┐                │
│  No ──────────────┐          │                │
└────────────────┬──┴──────────┬┴────────────────┘
                 │             │
                 ▼             ▼
          Compress          No Compress
                 │             │
                 └─────┬───────┘
                       │
                       ▼
    ┌──────────────────────────────────────┐
    │   CREATE LOCAL BACKUP                │
    │  • Copy folder to backup location    │
    │  • Add timestamp to name             │
    │  • Compress to ZIP (if selected)     │
    │  • Cleanup old backups               │
    │  • Log operation                     │
    └────────────────┬─────────────────────┘
                     │
          ✅ Local Backup Created
                     │
                     ▼
    ┌──────────────────────────────────────┐
    │   SUCCESS MESSAGE                    │
    │  ✅ Backup created successfully!     │
    └────────────────┬─────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────────────────┐
    │  🆕 GOOGLE DRIVE BACKUP PROMPT                  │
    │                                                 │
    │  Do you want to backup data to               │
    │  Google Drive on this email:                 │
    │  john@gmail.com? [y/N]                       │
    │                                                 │
    │  ┌─── YES ───────────────────┐                 │
    │  │                           │                 │
    │  └─── NO ────────────────────┘                 │
    └────────────┬──────────────────┬───────────────┘
                 │                  │
          YES   │                  │  NO
                 ▼                  │
    ┌──────────────────────────────┐│
    │ EMAIL CONFIRMATION PROMPT    ││
    │                              ││
    │ Use the same email for       ││
    │ Google Drive? [Y/n]          ││
    │  john@gmail.com              ││
    │                              ││
    │ ┌─ YES (Same Email)          ││
    │ ├─ NO (Different Email)      ││
    │ └─ Press 'n' to skip         ││
    └────┬─────────────────┬───────┘│
         │                 │        │
    YES  │            NO   │   "Backup saved
         ▼                 ▼     locally only"
    ┌──────────┐     ┌───────────────────┐
    │ Use Email│     │ ENTER ALT EMAIL   │
    │john@... │     │ "Enter alternative│
    │(Default)│     │ email for Drive:"  │
    └────┬────┘     │ work@company.com  │
         │          └────────┬──────────┘
         │                   │
         └─────────┬─────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  🔄 UPLOADING TO GOOGLE DRIVE        │
    │                                      │
    │  • Initialize Google Drive service   │
    │  • Check credentials                 │
    │  • Create folder (if needed)         │
    │  • Upload backup file                │
    │  • Add email metadata                │
    │  • Log upload success/failure        │
    └────────────┬─────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   SUCCESS          FAILURE
        │                 │
        ▼                 ▼
    ┌─────────┐    ┌──────────────┐
    │✅Upload │    │❌Upload     │
    │Success  │    │Failed        │
    │         │    │(Logged)      │
    └────┬────┘    └────┬─────────┘
         │              │
         │    ┌─────────┘
         │    │
         │    ▼
         │  ⚠️  Warning Message
         │  "Failed to upload to
         │   Google Drive"
         │
         ▼
    ┌──────────────────────────────────────┐
    │  Backup Complete                     │
    │  ✅ Local: D:\Backups\...            │
    │  ✅ Cloud: john@gmail.com  [if sent] │
    │  📧 Email: john@gmail.com            │
    │                                      │
    │  Press any key to continue...        │
    └────────────┬─────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────┐
    │     RETURN TO MAIN MENU               │
    └──────────────────────────────────────┘
```

---

## Detailed Email Selection Flow

```
┌─────────────────────────────────────────────────┐
│  USER LOGGED IN WITH EMAIL:                    │
│       john@gmail.com                           │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  GOOGLE DRIVE EMAIL SELECTION                   │
│                                                 │
│  "Do you want to backup to Google Drive       │
│   on this email: john@gmail.com?"              │
│   [y/N]                                         │
└────┬────────────────────────────────┬──────────┘
     │                                │
    YES                              NO
     │                                │
     ▼                                ▼
┌──────────────────────────┐   ┌─────────────────┐
│ NEXT PROMPT:             │   │ Skip Google     │
│ "Use the same email for  │   │ Drive backup    │
│  Google Drive? [Y/n]"    │   │                 │
│  john@gmail.com          │   │ Backup saved    │
│                          │   │ locally only    │
└──┬──────────────────┬────┘   └─────────────────┘
   │                  │
  YES                NO
   │                  │
   ▼                  ▼
┌─────────────┐  ┌──────────────────────────┐
│ Use Email:  │  │ ENTER ALTERNATIVE EMAIL  │
│ john@...    │  │                          │
│             │  │ "Enter alternative email │
│ (Default)   │  │  for Google Drive:"      │
│             │  │                          │
│ Upload to:  │  │ [User types:]            │
│ john@gmail  │  │ work@company.com         │
│ .com Drive  │  │                          │
└──────┬──────┘  └──────────┬────────────────┘
       │                    │
       │ Upload to:         │
       │ work@company.com   │
       │ Drive              │
       │                    │
       └──────────┬─────────┘
                  │
                  ▼
         🔄 Upload Process
                  │
                  ▼
         Upload with email
         metadata
                  │
           ┌──────┴──────┐
           │             │
        SUCCESS       FAILURE
           │             │
           ▼             ▼
      ✅ Success    ❌ Error
```

---

## File Organization Timeline

```
TIMELINE OF OPERATIONS:

1️⃣  PRE-BACKUP
    │
    ├─ Validate folder path
    ├─ Check permissions
    ├─ Check disk space
    └─ Prepare backup location
    Time: < 1 second

2️⃣  LOCAL BACKUP CREATION
    │
    ├─ Create backup folder
    ├─ Copy files
    ├─ Compress to ZIP (optional)
    └─ Cleanup old backups
    Time: Depends on folder size

3️⃣  GOOGLE DRIVE PROMPT
    │
    ├─ Display current email
    ├─ Ask about Google Drive
    ├─ Ask about email choice
    └─ Collect user input
    Time: User interaction

4️⃣  GOOGLE DRIVE UPLOAD
    │
    ├─ Authenticate with Google Drive
    ├─ Create/find folder
    ├─ Upload backup file
    └─ Log operation
    Time: Depends on file size

5️⃣  SUCCESS/COMPLETION
    │
    ├─ Display success message
    ├─ Show backup location(s)
    ├─ Show email(s) used
    └─ Return to menu
    Time: < 1 second
```

---

## Data Flow Diagram

```
USER LOGIN
    │
    ├─ Email: john@gmail.com
    ├─ Session: Active (8 hrs)
    └─ Token: Generated
         │
         ▼
SELECT BACKUP (Choice 3)
    │
    └─ Path: D:\Documents
         │
         ▼
LOCAL BACKUP SYSTEM
    │
    ├─ Source: D:\Documents
    ├─ Destination: D:\Backups\system_backups\
    │              documents_backup_20260221_100530.zip
    └─ Stored in: Local disk
         │
         ▼
GOOGLE DRIVE UPLOAD (Optional)
    │
    ├─ Service Account Auth
    │  └─ Credentials: google_drive_credentials.json
    │
    ├─ Create Folder: System Backups
    │  └─ Shared with: service@account.iam.gserviceaccount.com
    │
    ├─ Upload File
    │  ├─ Source: documents_backup_20260221_100530.zip
    │  ├─ Destination: Google Drive / System Backups /
    │  ├─ Metadata: Created by john@gmail.com
    │  └─ Size: Compressed
    │
    └─ Storage
       ├─ Local: D:\Backups\...
       └─ Cloud: Google Drive / System Backups /
            └─ documents_backup_20260221_100530.zip
```

---

## Email Handling Examples

```
SCENARIO 1: Same Email (Default)
┌─────────────────────────────┐
│ Login Email: john@gmail.com │
└────────────────┬────────────┘
                 │
         Google Drive Prompt
                 │
    "Use john@gmail.com? [Y/n]"
                 │
              YES (Default)
                 │
    Upload to Google Drive
      with email: john@gmail.com
                 │
         Stored in folder named
         for john@gmail.com backups
         ✅ Done


SCENARIO 2: Different Email
┌──────────────────────────────┐
│ Login Email: john@gmail.com  │
└────────────────┬─────────────┘
                 │
         Google Drive Prompt
                 │
    "Use john@gmail.com? [Y/n]"
                 │
              NO
                 │
    "Enter alternative email:"
                 │
    work@company.com
                 │
    Upload to Google Drive
    with email: work@company.com
                 │
    Stored in company Google Drive
    or shared account
    ✅ Done


SCENARIO 3: Skip Google Drive
┌──────────────────────────────┐
│ Login Email: john@gmail.com  │
└────────────────┬─────────────┘
                 │
         Google Drive Prompt
                 │
"Do you want to backup to Drive? [y/N]"
                 │
              NO / Skip
                 │
    Local backup only
    ✅ Done (no cloud backup)
```

---

## Success Scenarios

```
✅ SUCCESSFUL FLOW:
   • User logs in
   • Creates backup
   • Selects Google Drive
   • Chooses email
   • Upload succeeds
   • Confirmation shown

⚠️  PARTIAL SUCCESS:
   • Local backup succeeds
   • Google Drive upload fails
   • User notified
   • Can retry later

⚠️  LOCAL ONLY:
   • Local backup succeeds
   • User skips Google Drive
   • Backup saved locally
   • Can move to Drive later

❌ ERROR HANDLING:
   • Invalid path → Error message + retry
   • Disk space low → Error message + exit
   • Google credentials missing → Warning + skip
   • Upload fails → Log error + warning message
```

---

## Complete Backup File Organization

```
LOCAL STORAGE:
D:\Backups\system_backups\
├── 2026-02-21/
│   ├── documents_backup_20260221_100530.zip
│   ├── documents_backup_20260221_111245.zip
│   └── photos_backup_20260221_120000.zip
│
├── 2026-02-22/
│   ├── projects_backup_20260222_090530.zip
│   └── music_backup_20260222_101530.zip
│
└── logs/
    └── backup_manager.log

GOOGLE DRIVE STORAGE:
Google Drive /
├── System Backups/
│   ├── documents_backup_20260221_100530.zip
│   │   (Created by: john@gmail.com)
│   │
│   ├── documents_backup_20260221_111245.zip
│   │   (Created by: john@gmail.com)
│   │
│   ├── photos_backup_20260221_120000.zip
│   │   (Created by: work@company.com)
│   │
│   ├── projects_backup_20260222_090530.zip
│   │   (Created by: john@gmail.com)
│   │
│   └── music_backup_20260222_101530.zip
│       (Created by: john@gmail.com)
└── logs/
    └── google_drive_manager.log
```

---

**Visualization Complete!**

This flow chart shows the complete backup process with Google Drive integration,
including all decision points and email handling options.

For more details, see:
- GOOGLE_DRIVE_SETUP.md
- GOOGLE_DRIVE_QUICK_REFERENCE.md
- main.py (backup section)
