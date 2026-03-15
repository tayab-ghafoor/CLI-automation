# System Manager CLI - Login System Guide

## Overview
The System Manager CLI now includes a secure login system that requires users to authenticate via email before accessing any features.

## Features

### 1. User Registration
- Users can create new accounts with their email and password
- **Password Requirements:**
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 digit

### 2. User Login
- Users must login with their email and password before accessing any system management features
- Sessions last for 8 hours
- After logging in, users are presented with the main interactive menu

### 3. Account Management
- **View Profile:** Check your email, name, creation date, and last login time
- **Change Password:** Update your password securely
- **Logout:** Logout from your current session

## How to Use

### Starting the Application

```bash
python main.py
```

### First Time Users

1. Select **Register** from the welcome menu
2. Enter your email address
3. Enter your full name (optional)
4. Create a strong password (8+ chars, 1 uppercase, 1 digit)
5. Confirm your password
6. You can now login with your credentials

### Logging In

1. Run the application
2. Select **Login** from the welcome menu
3. Enter your email and password
4. After successful login, choose from the available options:
   - Check System Health 🏥
   - Clean Temporary Files 🧹
   - Backup Folder 💾
   - Generate System Report 📊
   - Setup Configuration ⚙️
   - View Profile 👤
   - Change Password 🔐
   - Logout
   - Exit

### Using CLI Commands

You can also use specific commands directly:

```bash
# Register a new user
python main.py register

# Login to your account
python main.py login

# Logout from your account
python main.py logout

# Change your password
python main.py change-password

# View your profile
python main.py show-profile

# Check system health (requires login)
python main.py check-health-cli
```

## Data Storage

### User Data
- User information is stored in: `system_manager_cli/data/users.json`
- Passwords are hashed using SHA256
- User data includes:
  - Email
  - Password hash
  - Full name
  - Creation date
  - Last login date

### Session Data
- Active sessions are stored in: `system_manager_cli/data/sessions.json`
- Session tokens are generated using HMAC-SHA256
- Sessions expire after 8 hours of inactivity

## Security Features

1. **Password Hashing:** All passwords are hashed using SHA256 before storage
2. **Session Tokens:** Unique tokens are generated for each session
3. **Session Expiration:** Sessions automatically expire after 8 hours
4. **Email Validation:** Email addresses are validated before registration
5. **Password Strength:** Passwords must meet minimum security requirements

## Troubleshooting

### Forgot Password
Currently, there's no password reset feature. To reset your password:
1. Contact your administrator
2. Have them delete your user account from `system_manager_cli/data/users.json`
3. Register a new account with the same or different email

### Cannot Login
- Ensure your email is correctly spelled
- Check that your password is correct
- Verify the email exists in the system (case-sensitive)

### Session Expired
- If your session expires, simply login again
- Sessions last 8 hours from the last activity

## Admin Features

The first registered user is considered the admin and has the ability to:
- Delete user accounts (via future admin panel)
- Manage system-wide settings

## Future Enhancements

Potential features to be added:
- Email-based password reset
- Two-factor authentication (2FA)
- User role management (Admin, User, Guest)
- Login history and audit logs
- Account lockout after failed attempts
- Refresh token mechanism
