# Email Notifications - Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Get Gmail App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Ensure **2-Step Verification** is enabled
3. Find **App Passwords** → Select Mail & Windows
4. Copy the 16-character password

### Step 2: Configure .env File
```
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=backup_alerts@example.com
```

### Step 3: Done! ✅
Emails will automatically send when:
- ✅ User registers
- ✅ File/folder backup completes
- ✅ Scheduled tasks execute
- ✅ Password is changed

---

## 📧 What Emails You'll Get

| Event | Email Sent | Contains |
|-------|-----------|----------|
| **Registration** | Yes | Welcome + account details |
| **Manual Backup** | Yes | Backup location + size |
| **Scheduled Backup** | Yes | Task name + execution time |
| **Scheduled Task** | Yes | Task status + timestamp |
| **Password Change** | Yes | Confirmation + security tips |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Email not sending | Check `.env` file for EMAIL_SENDER & EMAIL_PASSWORD |
| App Password error | Ensure you used **App Password**, not regular Gmail password |
| Emails in spam | Mark sender as trusted in your email client |
| Connection failed | Verify internet connection & Gmail security settings |

---

## 📝 Configuration Reference

```
# 📧 Email Configuration
EMAIL_SENDER=your_gmail@gmail.com      # Required: Your Gmail address
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx     # Required: 16-char App Password (spaces ok)
EMAIL_RECIPIENT=alerts@example.com     # Optional: Default alert recipient
```

### Getting App Password:
1. Enable 2-Step Verification in Security Settings
2. Go to App Passwords section
3. Select: Mail + Windows Computer
4. Use the generated 16-character password

---

## ✨ Features

### Professional HTML Emails
- ✅ Rich formatting with colors and tables
- ✅ Mobile-friendly design
- ✅ Plain text fallback version
- ✅ Brand-consistent styling

### Smart Error Handling
- ✅ Graceful fallback if email fails
- ✅ Automatic logging of errors
- ✅ No impact on main operations

### User-Specific
- ✅ Emails sent to each user's registered email
- ✅ Personalized content with user names
- ✅ Timestamp information included

---

## 🎯 Usage Examples

### Check Email Configuration
```python
from config import Config
print(f"Sender: {Config.EMAIL_SENDER}")
print(f"Password configured: {bool(Config.EMAIL_PASSWORD)}")
```

### Send Test Email
```python
from email_notifier import EmailNotifier
EmailNotifier.send_registration_email("test@example.com", "Test User")
```

### Manual Backup with Email
```bash
cli backup --path="/path/to/backup" --email
```

---

## ❓ FAQ

**Q: Why do I need an App Password?**
A: It's more secure than your main Gmail password and can be revoked independently.

**Q: Can I use non-Gmail accounts?**
A: Yes, modify SMTP settings in `email_notifier.py` for your provider.

**Q: What if email sending fails?**
A: The system logs errors but continues normally. Check `logs/email_notifier.log`.

**Q: Is my password safe?**
A: Yes, store `.env` in `.gitignore` and never share it.

**Q: Can I customize email templates?**
A: Yes, edit the methods in `email_notifier.py`.

---

## 🚀 Next Steps

1. ✅ Configure `.env` with your Gmail credentials
2. ✅ Test by registering a new user account
3. ✅ Check your inbox for welcome email
4. ✅ Create a backup to test backup email
5. ✅ Schedule a task to test task completion email

---

## 📞 Support

- **Logs:** `logs/email_notifier.log`
- **Config:** Check `.env` file exists and is valid
- **Testing:** See EMAIL_NOTIFICATIONS.md for detailed testing guide

---

**Last Updated:** February 27, 2026
**Version:** 1.0
