# Email Notification System Documentation

## Overview
The System Manager CLI now includes a professional email notification system that sends automated emails for all critical user actions and system events. This ensures users stay informed about important activities in real-time.

## Features

### 1. **Registration Confirmation Email**
Sent when a user successfully completes the registration process.

**What's Included:**
- Welcome message
- Account details (email and registration timestamp)
- List of available features
- Security notice

**When Triggered:**
- User completes registration via `cli register` command

---

### 2. **Backup Completion Emails**
Sent after any backup operation completes successfully.

#### Manual Backup Email
Sent immediately after a user manually backs up a folder or file.

**What's Included:**
- Backup completion status
- Source path
- Backup location
- Backup size in MB
- Timestamp of completion

**When Triggered:**
- User executes `cli backup` command manually

#### Scheduled Backup Email
Sent after a scheduled backup task automatically executes.

**What's Included:**
- Task name
- Scheduled time
- Actual execution time
- Source and backup paths
- Backup size

**When Triggered:**
- A scheduled backup task runs at its designated time

---

### 3. **Scheduled Task Completion Email**
Sent after any scheduled task completes execution.

**What's Included:**
- Task name and description
- Scheduled execution time
- Actual execution time
- Task status (SUCCESS, WARNING, or FAILED)
- Detailed task information

**When Triggered:**
- Any scheduled task finishes execution (backups, system checks, custom tasks, etc.)

---

### 4. **Password Change Confirmation Email**
Sent when a user successfully changes their password.

**What's Included:**
- Change confirmation
- Timestamp of the change
- Security tips and warnings
- Instructions if unauthorized access is detected

**When Triggered:**
- User executes `cli change-password` command

---

## Setup Instructions

### Prerequisites
- Gmail account (recommended for SMTP support)
- App Password generated from Google Account security settings

### Step-by-Step Configuration

#### 1. **Create a Gmail App Password**

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Sign in with your Gmail account
3. Enable **2-Step Verification** (if not already enabled)
4. Return to Security page and find **App Passwords**
5. Select:
   - **App:** Mail
   - **Device:** Windows Computer (or your device type)
6. Google will generate a 16-character password
7. Copy this password - you'll need it next

#### 2. **Configure Environment Variables**

Create or edit `.env` file in the `system_manager_cli` directory:

```
# Email Configuration (For notifications and alerts)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@gmail.com
```

**Variables Explained:**
- `EMAIL_SENDER`: Your Gmail address (the one that will send emails)
- `EMAIL_PASSWORD`: The 16-character App Password (NOT your regular Gmail password)
- `EMAIL_RECIPIENT`: Optional - backup recipient for system alerts

#### 3. **Test Email Configuration**

Test if your configuration works:

```python
from email_notifier import EmailNotifier

# Test sending a registration email
EmailNotifier.send_registration_email("user@example.com", "John Doe")

# Test sending a backup completion email
EmailNotifier.send_backup_completion_email(
    "user@example.com",
    "D:/Documents",
    "D:/Backups/documents_backup_20260227_120000.zip",
    125.5,
    "Manual"
)
```

---

## Email Types and Their Content

### Registration Email
- **Subject:** ✅ Registration Successful - System Manager CLI
- **Recipient:** New user's email address
- **Format:** Plain text and HTML
- **Contains:**
  - Welcome message
  - Account creation timestamp
  - Available features list
  - Security notices

### Backup Completion Email (Manual)
- **Subject:** ✅ Backup Completed Successfully - Manual Backup
- **Recipient:** Logged-in user's email
- **Format:** Plain text and HTML with table layout
- **Contains:**
  - Completion timestamp
  - Source path
  - Backup location
  - Backup size (MB)
  - Backup type indicator

### Backup Completion Email (Scheduled)
- **Subject:** ✅ Scheduled Backup Completed - [Task Name]
- **Recipient:** Logged-in user's email
- **Format:** Plain text and HTML with detailed table
- **Contains:**
  - Task name
  - Scheduled vs actual execution time
  - Source and backup paths
  - Total backup size
  - Execution status

### Task Completion Email
- **Subject:** ✅ Task Completed - [Task Name]
- **Recipient:** Logged-in user's email
- **Format:** Plain text and HTML
- **Contains:**
  - Task name and status (SUCCESS/WARNING/FAILED)
  - Scheduled time
  - Actual execution time
  - Detailed task description
  - Status-appropriate color coding (green for success, yellow for warning, red for failure)

### Password Change Email
- **Subject:** 🔒 Password Changed Successfully - System Manager CLI
- **Recipient:** User's email
- **Format:** Plain text and HTML
- **Contains:**
  - Change confirmation
  - Email and timestamp
  - Security tips
  - Warning about unauthorized access

---

## How Emails Are Sent

### Email Sending Process

1. **EmailNotifier Module** (`email_notifier.py`)
   - Handles all email generation and sending
   - Uses Gmail SMTP (smtp.gmail.com:465) for securely sending emails
   - Generates both plain text and HTML versions for rich formatting
   - Includes professional templates and styling

2. **Integration Points**

   **In auth.py:**
   ```python
   # Registration email
   EmailNotifier.send_registration_email(email, full_name)
   
   # Password change email
   EmailNotifier.send_password_change_email(email, full_name)
   ```

   **In backup_manager.py:**
   ```python
   # Manual backup email
   backup_manager.send_backup_email(user_email, backup_path, "Manual")
   
   # Scheduled backup email
   backup_manager.send_scheduled_backup_email(
       user_email, 
       task_name, 
       backup_path, 
       schedule_time
   )
   ```

   **In scheduler.py:**
   ```python
   # Task completion email
   scheduler.send_task_completion_email(
       task_id, 
       user_email, 
       task_description, 
       status
   )
   ```

### Error Handling

- If email configuration is missing, the system logs a warning but doesn't crash
- Failed email sends are logged to `logs/email_notifier.log`
- The application continues normally even if email sending fails
- Users can still complete actions without email configuration

---

## Troubleshooting

### Email Not Sending?

**Problem:** No emails received despite configuration

**Solutions:**
1. **Check .env variables:**
   ```bash
   # Verify EMAIL_SENDER and EMAIL_PASSWORD are set correctly
   # PASSWORD must be an App Password, not your regular Gmail password
   ```

2. **Verify Gmail App Password:**
   - Go to Google Account > Security
   - Check if **Less secure app access** is disabled (it should be)
   - Re-generate App Password if needed

3. **Check recipient address:**
   - Ensure the user's email address is valid
   - Check user account has 'email' field set

4. **Review logs:**
   ```bash
   # Check email notifier logs
   cat logs/email_notifier.log
   
   # Check application logs
   cat logs/system_manager_cli.log
   ```

5. **Test SMTP connection:**
   ```python
   import smtplib
   try:
       with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
           server.login('your_email@gmail.com', 'your_app_password')
           print("✅ Connection successful!")
   except Exception as e:
       print(f"❌ Connection failed: {e}")
   ```

### Emails Going to Spam?

**Solutions:**
1. Add the sender email to your contacts
2. Mark emails as "Not spam" in your email client
3. Ensure the email configuration matches Gmail security requirements
4. Check email headers for SPF/DKIM authentication issues

### "Less secure apps" Error?

- This error means your Gmail security settings blocked the SMTP connection
- Use **App Passwords** instead (recommended method shown above)
- Never enable "Less secure app access" as it's less secure

---

## Email Templates and Customization

### Default Templates
All professional email templates are defined in `email_notifier.py`:

- **send_registration_email()** - Registration welcome
- **send_backup_completion_email()** - Manual backup completion
- **send_scheduled_backup_email()** - Scheduled task backup
- **send_task_completion_email()** - Generic task completion
- **send_password_change_email()** - Password change notification

### How to Customize

To customize email content, edit the corresponding method in `email_notifier.py`:

```python
@staticmethod
def send_registration_email(user_email: str, full_name: str = '') -> bool:
    subject = "Your Custom Subject"
    body = "Your custom plain text content"
    html_body = "<html>Your custom HTML content</html>"
    
    return EmailNotifier._send_email(user_email, subject, body, html_body)
```

---

## Security Best Practices

### Email Security

1. **Never share your App Password**
   - Treat it like your actual password
   - Don't commit `.env` to version control
   - Use `.gitignore` to exclude `.env`

2. **Use App Passwords, Not Regular Passwords**
   - App Passwords are more secure
   - They're specifically for app authentication
   - They can be revoked without affecting your account

3. **Monitor Email Activity**
   - Check your Gmail login activity
   - Review connected apps in Google Account security
   - Revoke access for unused apps

4. **Environment Variable Protection**
   - Store `.env` files securely
   - Restrict file permissions (chmod 600 on Unix)
   - Never share `.env` files with others

---

## Integration Examples

### Example 1: Manual Backup with Email

```python
from backup_manager import BackupManager

# Create backup
backup_manager = BackupManager("D:/Documents")
backup_path = backup_manager.create_backup(compress=True)

# Send completion email
if backup_path:
    backup_manager.send_backup_email(
        "user@example.com",
        backup_path,
        "Manual"
    )
```

### Example 2: Scheduled Backup Task

```python
from backup_manager import BackupManager
from scheduler import TaskScheduler

scheduler = TaskScheduler()
backup_manager = BackupManager("D:/Documents")

def backup_task():
    backup_path = backup_manager.create_backup()
    if backup_path:
        backup_manager.send_scheduled_backup_email(
            "user@example.com",
            "Daily Document Backup",
            backup_path,
            "Every day at 22:00"
        )

# Schedule daily backup
scheduler.add_task("daily_backup", backup_task, interval=1, unit='days', at_time='22:00')
scheduler.start()
```

### Example 3: Custom Task with Completion Email

```python
from scheduler import TaskScheduler

scheduler = TaskScheduler()

def my_task():
    print("Running custom task...")
    # Your task code here
    return True

def task_wrapper():
    status = "SUCCESS" if my_task() else "FAILED"
    scheduler.send_task_completion_email(
        "my_task_id",
        "user@example.com",
        "This task does important work",
        status=status
    )

scheduler.add_task("my_task_id", task_wrapper, interval=1, unit='hours')
scheduler.start()
```

---

## FAQ

**Q: Can I use services other than Gmail?**
A: Currently, the system is configured for Gmail SMTP. To use other services, modify the SMTP server and port in `email_notifier.py`'s `_send_email()` method.

**Q: Will emails be sent if I'm not a registered user?**
A: Only registered users with valid emails will receive emails. Registration email is sent immediately after signup.

**Q: Can I disable email notifications?**
A: Yes. Remove or comment out `EMAIL_SENDER` and `EMAIL_PASSWORD` in `.env`. The system will skip email sending gracefully.

**Q: Are email addresses stored securely?**
A: Only in the user registration data. Always protect your `.env` file containing email credentials.

**Q: What if my email provider doesn't support App Passwords?**
A: Update the SMTP configuration in `email_notifier.py` to use your provider's settings.

---

## Support

For issues or questions about the email system:

1. Check the troubleshooting section above
2. Review logs in `logs/email_notifier.log`
3. Verify `.env` configuration is correct
4. Test SMTP connection separately

---

## Version Information

- **Module:** email_notifier.py v1.0
- **Last Updated:** February 27, 2026
- **Compatible with:** System Manager CLI v2.0+
