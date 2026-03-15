# System Manager CLI - Login System - Quick Reference

## 🚀 Getting Started

### First Time Setup
```bash
python main.py
# Select: Register
# Enter email, name, password
# Select: Login with your credentials
```

## 📋 Login Commands (CLI)

| Command | Description |
|---------|-------------|
| `python main.py register` | Create a new account |
| `python main.py login` | Login to your account |
| `python main.py logout` | Logout from current session |
| `python main.py change-password` | Change your password |
| `python main.py show-profile` | View your profile |
| `python main.py check-health-cli` | Check system health (login required) |

## 🎯 Interactive Menu Options (after login)

```
1. Check System Health 🏥         - Monitor CPU, RAM, Disk usage
2. Clean Temporary Files 🧹       - Organize and clean files
3. Backup Folder 💾               - Create backups
4. Generate System Report 📊      - Analyze logs
5. Setup Configuration ⚙️         - Configure settings
6. View Profile 👤                - See account details
7. Change Password 🔐             - Update password
8. Logout ❌                       - End session
9. Exit 🚪                        - Close application
```

## 🔐 Password Requirements

- ✅ Minimum 8 characters
- ✅ At least 1 UPPERCASE letter
- ✅ At least 1 digit (0-9)

**Example:** `MyPassword123`

## 📧 Email Validation

Valid formats:
- ✅ user@example.com
- ✅ john.doe@company.co.uk
- ✅ test123@email.org

Invalid formats:
- ❌ user@
- ❌ @example.com
- ❌ user@.com

## ⏱️ Session Information

- **Duration:** 8 hours
- **Automatic:** Sessions expire after 8 hours of inactivity
- **Token:** Unique security token generated per session
- **Location:** `system_manager_cli/data/sessions.json`

## 💾 Data Storage

```
system_manager_cli/
├── data/
│   ├── users.json          (User accounts)
│   └── sessions.json       (Active sessions)
├── auth.py                 (Authentication module)
├── main.py                 (Updated with login)
└── LOGIN_GUIDE.md         (Full documentation)
```

## 🛡️ Security Features

1. **Password Hashing:** SHA256 encryption
2. **Session Tokens:** HMAC-SHA256 generated tokens
3. **Email Validation:** Format checking before registration
4. **Password Strength:** Enforced requirements
5. **Session Expiration:** Automatic 8-hour timeout

## ⚠️ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Email already registered" | Use a different email or login |
| "Email or password incorrect" | Check spelling and case sensitivity |
| "Password must be at least 8 characters" | Use longer password with uppercase & digit |
| "Invalid email format" | Use proper email format (user@domain.com) |
| "Session expired" | Login again with your credentials |

## example registration flow:

```
$ python main.py
Select: Register
📧 Enter your email: john@example.com
👤 Enter your full name (optional): John Doe
🔐 Enter password: MyPass123
🔐 Confirm password: MyPass123
✅ User registered successfully

Select: Login
📧 Enter your email: john@example.com
🔐 Enter your password: MyPass123
✅ Welcome John Doe!
```

## Example CLI Usage:

```bash
# Register
python main.py register

# Login
python main.py login

# After login, use system features
python main.py check-health-cli --email

# View profile
python main.py show-profile

# Change password
python main.py change-password

# Logout
python main.py logout
```

## 🔄 File Organization & Backup (after login)

Once logged in, you can:
1. **Organize files:** Rename, deduplicate, organize by type
2. **Create backups:** Compress and backup important folders
3. **Analyze logs:** Generate reports on system logs
4. **Monitor health:** Track CPU, RAM, and disk usage

## 🆘 Troubleshooting

### Can't remember password?
- Contact administrator
- Admin can delete and re-register account

### Lost session?
- Simply login again
- Your account is safe

### Can't register?
- Check email format
- Ensure password meets requirements
- Check if email already registered

## 📈 Admin Features

First registered user becomes admin with ability to:
- Delete user accounts
- Manage system settings
- View user statistics

---

**Last Updated:** February 21, 2026
**System Manager CLI v1.0 with Login**
