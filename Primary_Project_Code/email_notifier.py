"""
Email Notifier Module
Handles professional email notifications for user actions:
- Registration completion
- Backup completion
- Scheduled task completion
- Password change
- Password reset code
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

from .config import Config
from .logger import get_logger

logger = get_logger(__name__, 'email_notifier.log')


class EmailNotifier:
    """Handles sending professional emails for system events."""

    @staticmethod
    def _normalize_credential(value: str | None) -> str:
        """Trim wrappers and normalize app-password formatting."""
        if not value:
            return ""
        cleaned = value.strip().strip('"').strip("'")
        # Gmail app passwords are often copied with spaces.
        return cleaned.replace(" ", "")

    @staticmethod
    def _is_placeholder(value: str) -> bool:
        placeholders = {
            "your_email@gmail.com",
            "your_app_password",
            "recipient@gmail.com",
            "example@gmail.com",
        }
        return value.lower() in placeholders

    @staticmethod
    def _send_email(recipient_email: str, subject: str, body: str, html_body: str | None = None) -> bool:
        """Send an email using SMTP."""
        try:
            # Always reload .env from project folder so runtime CWD doesn't matter.
            load_dotenv(Config.BASE_DIR / ".env", override=True)

            sender = EmailNotifier._normalize_credential(os.getenv("EMAIL_SENDER", Config.EMAIL_SENDER or ""))
            password = EmailNotifier._normalize_credential(os.getenv("EMAIL_PASSWORD", Config.EMAIL_PASSWORD or ""))
            default_recipient = EmailNotifier._normalize_credential(os.getenv("EMAIL_RECIPIENT", Config.EMAIL_RECIPIENT or ""))

            smtp_host = os.getenv("SMTP_HOST", Config.SMTP_HOST or "smtp.gmail.com").strip()
            smtp_port = int(os.getenv("SMTP_PORT", str(Config.SMTP_PORT or 465)))
            smtp_use_ssl = os.getenv("SMTP_USE_SSL", str(Config.SMTP_USE_SSL).lower()).lower() == "true"
            smtp_use_tls = os.getenv("SMTP_USE_TLS", str(Config.SMTP_USE_TLS).lower()).lower() == "true"

            if not sender or not password:
                logger.error(
                    "Email configuration missing. Set EMAIL_SENDER and EMAIL_PASSWORD in system_manager_cli/.env."
                )
                return False

            if EmailNotifier._is_placeholder(sender) or EmailNotifier._is_placeholder(password):
                logger.error(
                    "Email configuration is still using placeholder values. Replace EMAIL_SENDER/EMAIL_PASSWORD with real credentials."
                )
                return False

            if not recipient_email:
                recipient_email = default_recipient
                if not recipient_email:
                    logger.error("No recipient email provided and EMAIL_RECIPIENT not set in configuration")
                    return False

            recipient_email = recipient_email.strip()

            msg = MIMEMultipart("alternative")
            msg["From"] = sender
            msg["To"] = recipient_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            if smtp_use_ssl:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                    server.login(sender, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                    server.ehlo()
                    if smtp_use_tls:
                        server.starttls()
                        server.ehlo()
                    server.login(sender, password)
                    server.send_message(msg)

            logger.info(f"Email sent successfully to {recipient_email}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"SMTP authentication failed for {recipient_email}: {e}. "
                "If using Gmail, use a 16-digit App Password with 2-Step Verification enabled."
            )
            return False

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False

    @staticmethod
    def send_registration_email(user_email: str, full_name: str = "") -> bool:
        """Send registration confirmation email."""
        subject = "Registration Successful - System Manager CLI"

        name = full_name.split()[0] if full_name else "User"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        body = f"""Dear {name},

Welcome to System Manager CLI. Your registration has been completed successfully.

Your Account Details:
- Email: {user_email}
- Registration Date: {timestamp}

You can now log in and start using these features:
- File and Folder Backup Management
- Scheduled Backup Tasks
- Task Scheduling and Automation
- System Health Monitoring
- Password Management

If you did not register for this service, please contact support immediately.

Best regards,
System Manager CLI Team
"""

        html_body = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 5px; padding: 20px;">
            <h2 style="color: #27ae60;">Registration Successful</h2>
            <p>Dear <strong>{name}</strong>,</p>
            <p>Welcome to <strong>System Manager CLI</strong>. Your registration has been completed successfully.</p>

            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4>Your Account Details:</h4>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Registration Date:</strong> {timestamp}</p>
            </div>

            <p>You can now log in and start using all available features:</p>
            <ul style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #27ae60;">
                <li>File and Folder Backup Management</li>
                <li>Scheduled Backup Tasks</li>
                <li>Task Scheduling and Automation</li>
                <li>System Health Monitoring</li>
                <li>Password Management</li>
            </ul>

            <p style="color: #e74c3c;"><strong>Security Note:</strong> If you did not register for this service, please contact support immediately.</p>

            <p>Best regards,<br><strong>System Manager CLI Team</strong></p>
        </div>
    </body>
</html>
"""

        return EmailNotifier._send_email(user_email, subject, body, html_body)

    @staticmethod
    def send_backup_completion_email(
        user_email: str,
        source_path: str,
        backup_path: str,
        backup_size_mb: float,
        backup_type: str = "Manual",
    ) -> bool:
        """Send backup completion notification email."""
        subject = f"Backup Completed Successfully - {backup_type} Backup"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        body = f"""Backup Completion Report

Type: {backup_type} Backup
Completion Time: {timestamp}

Source Details:
Source Path: {source_path}

Backup Details:
Backup Location: {backup_path}
Backup Size: {backup_size_mb:.2f} MB
Backup Type: {backup_type}

Status: COMPLETED SUCCESSFULLY

Your data has been successfully backed up. You can restore from this backup anytime.

Best regards,
System Manager CLI Team
"""

        html_body = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 5px; padding: 20px; background-color: #f0f8f5;">
            <h2 style="color: #27ae60;">Backup Completed Successfully</h2>

            <div style="background-color: #d5f4e6; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                <p style="margin: 0;"><strong>Status:</strong> <span style="color: #27ae60;">Completed Successfully</span></p>
                <p style="margin: 5px 0 0 0;"><strong>Completion Time:</strong> {timestamp}</p>
            </div>

            <h4 style="color: #2c3e50;">Backup Details:</h4>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Source Path:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{source_path}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Backup Location:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{backup_path}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Backup Size:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{backup_size_mb:.2f} MB</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Backup Type:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{backup_type}</td>
                </tr>
            </table>

            <p style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <strong>Note:</strong> Your data has been successfully backed up. Keep this backup safe for future restoration needs.
            </p>

            <p>Best regards,<br><strong>System Manager CLI Team</strong></p>
        </div>
    </body>
</html>
"""

        return EmailNotifier._send_email(user_email, subject, body, html_body)

    @staticmethod
    def send_scheduled_backup_email(
        user_email: str,
        task_name: str,
        source_path: str,
        backup_path: str,
        backup_size_mb: float,
        schedule_time: str,
    ) -> bool:
        """Send scheduled backup completion notification email."""
        subject = f"Scheduled Backup Completed - {task_name}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        body = f"""Scheduled Backup Completion Report

Task Name: {task_name}
Scheduled Time: {schedule_time}
Completion Time: {timestamp}

Source Details:
Source Path: {source_path}

Backup Details:
Backup Location: {backup_path}
Backup Size: {backup_size_mb:.2f} MB

Status: EXECUTED SUCCESSFULLY

Your scheduled backup has been executed and completed successfully.

Best regards,
System Manager CLI Team
"""

        html_body = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 5px; padding: 20px; background-color: #f0f8f5;">
            <h2 style="color: #27ae60;">Scheduled Backup Executed</h2>

            <div style="background-color: #d5f4e6; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                <p style="margin: 0;"><strong>Task:</strong> {task_name}</p>
                <p style="margin: 5px 0 0 0;"><strong>Status:</strong> <span style="color: #27ae60;">Completed Successfully</span></p>
            </div>

            <h4 style="color: #2c3e50;">Execution Details:</h4>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Scheduled Time:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{schedule_time}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Completion Time:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{timestamp}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Source Path:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{source_path}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Backup Location:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{backup_path}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Backup Size:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{backup_size_mb:.2f} MB</td>
                </tr>
            </table>

            <p>Best regards,<br><strong>System Manager CLI Team</strong></p>
        </div>
    </body>
</html>
"""

        return EmailNotifier._send_email(user_email, subject, body, html_body)

    @staticmethod
    def send_task_completion_email(
        user_email: str,
        task_name: str,
        task_description: str,
        scheduled_time: str,
        execution_time: str,
        status: str = "SUCCESS",
    ) -> bool:
        """Send task completion notification email."""
        status_label = "SUCCESS" if status == "SUCCESS" else "WARNING" if status == "WARNING" else "FAILED"
        status_color = "#27ae60" if status == "SUCCESS" else "#f39c12" if status == "WARNING" else "#e74c3c"

        subject = f"[{status_label}] Task Completed - {task_name}"

        body = f"""Task Execution Report

Task Name: {task_name}
Status: {status}
Scheduled Time: {scheduled_time}
Execution Time: {execution_time}

Task Details:
{task_description}

The scheduled task has been executed as planned.

Best regards,
System Manager CLI Team
"""

        html_body = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 5px; padding: 20px;">
            <h2 style="color: {status_color};">{status_label} Task Completed</h2>

            <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid {status_color};">
                <p style="margin: 0;"><strong>Task Name:</strong> {task_name}</p>
                <p style="margin: 5px 0 0 0;"><strong>Status:</strong> <span style="color: {status_color};">{status}</span></p>
            </div>

            <h4 style="color: #2c3e50;">Task Information:</h4>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Scheduled Time:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{scheduled_time}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Execution Time:</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{execution_time}</td>
                </tr>
            </table>

            <h4 style="color: #2c3e50;">Task Description:</h4>
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db;">
                <p>{task_description}</p>
            </div>

            <p>Best regards,<br><strong>System Manager CLI Team</strong></p>
        </div>
    </body>
</html>
"""

        return EmailNotifier._send_email(user_email, subject, body, html_body)

    @staticmethod
    def send_password_change_email(user_email: str, full_name: str = "") -> bool:
        """Send password change confirmation email."""
        subject = "Password Changed Successfully - System Manager CLI"

        name = full_name.split()[0] if full_name else "User"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        body = f"""Password Change Confirmation

Dear {name},

Your password has been changed successfully.

Change Details:
- Email: {user_email}
- Change Time: {timestamp}

If you did not request this change or if you notice any suspicious activity on your account,
please reset your password immediately and contact support.

Security Tips:
- Never share your password with anyone
- Use a strong, unique password
- Change your password regularly
- Enable two-factor authentication if available

Best regards,
System Manager CLI Team
"""

        html_body = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 5px; padding: 20px; background-color: #f0f5fb;">
            <h2 style="color: #2980b9;">Password Changed Successfully</h2>

            <p>Dear <strong>{name}</strong>,</p>
            <p>Your password has been changed successfully.</p>

            <div style="background-color: #d6eaf8; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #2980b9;">
                <h4>Change Details:</h4>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Change Time:</strong> {timestamp}</p>
            </div>

            <h4 style="color: #e74c3c;">Important Security Notice:</h4>
            <p style="background-color: #fadbd8; padding: 15px; border-radius: 5px; border-left: 4px solid #e74c3c;">
                If you did not request this change or if you notice any suspicious activity on your account,
                please <strong>reset your password immediately</strong> and contact support.
            </p>

            <h4>Security Tips:</h4>
            <ul style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #27ae60;">
                <li>Never share your password with anyone</li>
                <li>Use a strong, unique password (8+ characters with uppercase and numbers)</li>
                <li>Change your password regularly</li>
                <li>Be cautious of phishing emails</li>
            </ul>

            <p>Best regards,<br><strong>System Manager CLI Team</strong></p>
        </div>
    </body>
</html>
"""

        return EmailNotifier._send_email(user_email, subject, body, html_body)

    @staticmethod
    def send_password_reset_code_email(
        user_email: str,
        reset_code: str,
        full_name: str = "",
        expires_in_minutes: int = 5,
    ) -> bool:
        """Send a password reset code email."""
        subject = "Password Reset Code - System Manager CLI"

        name = full_name.split()[0] if full_name else "User"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        body = f"""Password Reset Request

Dear {name},

We received a request to reset your System Manager CLI password.

Your password reset code is: {reset_code}

This code will expire in {expires_in_minutes} minutes.
Request Time: {timestamp}

If you did not request this password reset, you can ignore this email.

Best regards,
System Manager CLI Team
"""

        html_body = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 5px; padding: 20px; background-color: #fdfaf2;">
            <h2 style="color: #d35400;">Password Reset Code</h2>
            <p>Dear <strong>{name}</strong>,</p>
            <p>We received a request to reset your <strong>System Manager CLI</strong> password.</p>

            <div style="background-color: #fff3cd; padding: 20px; border-radius: 6px; text-align: center; margin: 20px 0; border: 1px solid #ffe08a;">
                <p style="margin: 0 0 8px 0;"><strong>Your reset code</strong></p>
                <p style="font-size: 32px; letter-spacing: 4px; margin: 0; color: #c0392b;"><strong>{reset_code}</strong></p>
            </div>

            <p><strong>Expires in:</strong> {expires_in_minutes} minutes</p>
            <p><strong>Request Time:</strong> {timestamp}</p>

            <p style="background-color: #f8f9fa; padding: 12px; border-radius: 5px;">
                If you did not request this password reset, you can safely ignore this email.
            </p>

            <p>Best regards,<br><strong>System Manager CLI Team</strong></p>
        </div>
    </body>
</html>
"""

        return EmailNotifier._send_email(user_email, subject, body, html_body)
