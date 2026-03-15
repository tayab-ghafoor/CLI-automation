"""
Authentication Module
Handles user login with email and password verification
"""

import json
import hashlib
import hmac
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .logger import get_logger
from .email_notifier import EmailNotifier
import re

logger = get_logger(__name__)


class AuthManager:
    """Manages user authentication and sessions"""
    RESET_CODE_EXPIRY_MINUTES = 5
    MAX_RESET_ATTEMPTS = 3
    PASSWORD_HASH_ITERATIONS = 200_000
    
    def __init__(self):
        self.users_file = Path(__file__).parent / 'data' / 'users.json'
        self.sessions_file = Path(__file__).parent / 'data' / 'sessions.json'
        self.ensure_data_directory()
        self.loads_users()
        self.load_sessions()
    
    def ensure_data_directory(self) -> None:
        """Create data directory if it doesn't exist"""
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(exist_ok=True)
    
    def loads_users(self) -> None:
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load users: {e}")
                self.users = {}
        else:
            self.users = {}
    
    def load_sessions(self) -> None:
        """Load active sessions from file"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r') as f:
                    sessions = json.load(f)
                    # Clean expired sessions
                    self.sessions = {
                        email: sess for email, sess in sessions.items()
                        if datetime.fromisoformat(sess['expires_at']) > datetime.now()
                    }
                    self.save_sessions()
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
                self.sessions = {}
        else:
            self.sessions = {}
    
    def save_users(self) -> None:
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def save_sessions(self) -> None:
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using PBKDF2-HMAC-SHA256 with a random salt."""
        salt = secrets.token_hex(16)
        derived_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            AuthManager.PASSWORD_HASH_ITERATIONS,
        )
        return (
            f"pbkdf2_sha256${AuthManager.PASSWORD_HASH_ITERATIONS}$"
            f"{salt}${derived_key.hex()}"
        )

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify both current PBKDF2 hashes and legacy SHA256 hashes."""
        if stored_hash.startswith("pbkdf2_sha256$"):
            try:
                _, iterations_str, salt, expected_hash = stored_hash.split("$", 3)
                derived_key = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode(),
                    salt.encode(),
                    int(iterations_str),
                )
                return hmac.compare_digest(derived_key.hex(), expected_hash)
            except (TypeError, ValueError):
                logger.error("Invalid password hash format encountered during verification")
                return False

        legacy_hash = hashlib.sha256(password.encode()).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash)

    @staticmethod
    def _hash_reset_code(reset_code: str) -> str:
        """Hash a password reset code before storing it."""
        return hashlib.sha256(reset_code.encode()).hexdigest()

    @staticmethod
    def _generate_reset_code() -> str:
        """Generate a 6-digit password reset code."""
        return f"{secrets.randbelow(1_000_000):06d}"

    def _clear_password_reset(self, email: str) -> None:
        """Remove reset metadata for a user if present."""
        user = self.users.get(email)
        if not user:
            return
        if 'password_reset' in user:
            del user['password_reset']
            self.save_users()

    def _is_legacy_password_hash(self, stored_hash: str) -> bool:
        """Return True when a stored password hash uses the legacy format."""
        return not stored_hash.startswith("pbkdf2_sha256$")
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_strong_password(password: str) -> bool:
        """Validate password strength (minimum 8 characters, at least 1 uppercase, 1 digit)"""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True
    
    def register_user(self, email: str, password: str, full_name: str = '') -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            email: User email address
            password: User password
            full_name: User's full name (optional)
        
        Returns:
            Dict with success status and message
        """
        if not self.is_valid_email(email):
            return {'success': False, 'message': 'Invalid email format'}
        
        if not self.is_strong_password(password):
            return {'success': False, 'message': 'Password must be at least 8 characters with uppercase and digit'}
        
        if email in self.users:
            return {'success': False, 'message': 'Email already registered'}
        
        try:
            self.users[email] = {
                'email': email,
                'password_hash': self.hash_password(password),
                'full_name': full_name,
                'created_at': datetime.now().isoformat(),
                'last_login': None
            }
            self.save_users()
            
            # Send registration confirmation email (best-effort).
            # User registration should still succeed even when SMTP is not configured.
            email_sent = EmailNotifier.send_registration_email(email, full_name)
            
            logger.info(f"User registered: {email}")
            if email_sent:
                return {'success': True, 'message': 'User registered successfully'}
            return {
                'success': True,
                'message': 'User registered successfully (confirmation email not sent; check EMAIL_SENDER/EMAIL_PASSWORD in .env)'
            }
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {'success': False, 'message': f'Registration failed: {e}'}
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login a user
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dict with success status, message, and session token
        """
        if email not in self.users:
            return {'success': False, 'message': 'Email or password incorrect'}
        
        user = self.users[email]
        if not self.verify_password(password, user['password_hash']):
            return {'success': False, 'message': 'Email or password incorrect'}
        
        try:
            if self._is_legacy_password_hash(user['password_hash']):
                self.users[email]['password_hash'] = self.hash_password(password)

            # Create session
            session_token = self._generate_session_token(email)
            expires_at = datetime.now() + timedelta(hours=8)
            
            self.sessions[email] = {
                'token': session_token,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat()
            }
            
            # Update last login
            self.users[email]['last_login'] = datetime.now().isoformat()
            self.save_users()
            self.save_sessions()
            
            logger.info(f"User logged in: {email}")
            return {
                'success': True,
                'message': 'Login successful',
                'token': session_token,
                'email': email,
                'name': user.get('full_name', email)
            }
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {'success': False, 'message': f'Login failed: {e}'}
    
    def logout(self, email: str) -> Dict[str, Any]:
        """
        Logout a user
        
        Args:
            email: User email
        
        Returns:
            Dict with success status
        """
        if email in self.sessions:
            del self.sessions[email]
            self.save_sessions()
            logger.info(f"User logged out: {email}")
            return {'success': True, 'message': 'Logged out successfully'}
        return {'success': False, 'message': 'User not logged in'}
    
    def verify_session(self, email: str, token: str) -> bool:
        """
        Verify if user session is valid
        
        Args:
            email: User email
            token: Session token
        
        Returns:
            True if session is valid, False otherwise
        """
        if email not in self.sessions:
            return False
        
        session = self.sessions[email]
        
        # Check if session expired
        if datetime.fromisoformat(session['expires_at']) < datetime.now():
            del self.sessions[email]
            self.save_sessions()
            return False
        
        # Verify token
        return session['token'] == token
    
    def is_logged_in(self, email: str) -> bool:
        """
        Check if user is logged in
        
        Args:
            email: User email
        
        Returns:
            True if user has valid session, False otherwise
        """
        if email not in self.sessions:
            return False
        
        session = self.sessions[email]
        if datetime.fromisoformat(session['expires_at']) < datetime.now():
            del self.sessions[email]
            self.save_sessions()
            return False
        
        return True
    
    def change_password(self, email: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password
        
        Args:
            email: User email
            old_password: Current password
            new_password: New password
        
        Returns:
            Dict with success status and message
        """
        if email not in self.users:
            return {'success': False, 'message': 'User not found'}
        
        user = self.users[email]
        if not self.verify_password(old_password, user['password_hash']):
            return {'success': False, 'message': 'Current password is incorrect'}
        
        if not self.is_strong_password(new_password):
            return {'success': False, 'message': 'New password must be at least 8 characters with uppercase and digit'}
        
        user['password_hash'] = self.hash_password(new_password)
        self.save_users()
        
        # Send password change confirmation email
        full_name = user.get('full_name', '')
        EmailNotifier.send_password_change_email(email, full_name)
        
        logger.info(f"Password changed for user: {email}")
        return {'success': True, 'message': 'Password changed successfully'}

    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Generate and email a password reset code.

        The code expires after 5 minutes and allows only limited verification attempts.
        """
        if email not in self.users:
            return {'success': False, 'message': 'Registered email not found'}

        user = self.users[email]
        reset_code = self._generate_reset_code()
        expires_at = datetime.now() + timedelta(minutes=self.RESET_CODE_EXPIRY_MINUTES)

        user['password_reset'] = {
            'code_hash': self._hash_reset_code(reset_code),
            'requested_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'attempts': 0,
            'max_attempts': self.MAX_RESET_ATTEMPTS,
        }
        self.save_users()

        full_name = user.get('full_name', '')
        email_sent = EmailNotifier.send_password_reset_code_email(
            email,
            reset_code,
            full_name,
            self.RESET_CODE_EXPIRY_MINUTES,
        )

        if not email_sent:
            return {
                'success': False,
                'message': 'Could not send reset code email. Check email configuration.',
            }

        logger.info(f"Password reset requested for {email}")
        return {'success': True, 'message': 'A reset code has been sent to your email.'}

    def reset_password_with_code(self, email: str, reset_code: str, new_password: str) -> Dict[str, Any]:
        """Reset a user's password using a valid, unexpired reset code."""
        if email not in self.users:
            return {'success': False, 'message': 'Registered email not found'}

        user = self.users[email]
        reset_data = user.get('password_reset')
        if not reset_data:
            return {'success': False, 'message': 'No active password reset request found'}

        expires_at = datetime.fromisoformat(reset_data['expires_at'])
        if expires_at < datetime.now():
            self._clear_password_reset(email)
            return {'success': False, 'message': 'Reset code has expired. Request a new code.'}

        attempts = int(reset_data.get('attempts', 0))
        max_attempts = int(reset_data.get('max_attempts', self.MAX_RESET_ATTEMPTS))
        if attempts >= max_attempts:
            self._clear_password_reset(email)
            return {'success': False, 'message': 'Reset attempts exceeded. Request a new code.'}

        if not hmac.compare_digest(reset_data['code_hash'], self._hash_reset_code(reset_code)):
            reset_data['attempts'] = attempts + 1
            self.save_users()
            remaining = max(0, max_attempts - reset_data['attempts'])
            if remaining == 0:
                self._clear_password_reset(email)
                return {'success': False, 'message': 'Reset attempts exceeded. Request a new code.'}
            return {
                'success': False,
                'message': f'Invalid reset code. {remaining} attempt(s) remaining.',
            }

        if not self.is_strong_password(new_password):
            return {
                'success': False,
                'message': 'New password must be at least 8 characters with uppercase and digit',
            }

        user['password_hash'] = self.hash_password(new_password)
        if email in self.sessions:
            del self.sessions[email]
        if 'password_reset' in user:
            del user['password_reset']
        self.save_users()
        self.save_sessions()

        full_name = user.get('full_name', '')
        EmailNotifier.send_password_change_email(email, full_name)
        logger.info(f"Password reset completed for user: {email}")
        return {'success': True, 'message': 'Password reset successful!'}
    
    @staticmethod
    def _generate_session_token(email: str) -> str:
        """Generate a unique session token"""
        timestamp = str(datetime.now().timestamp())
        message = f"{email}:{timestamp}"
        token = hmac.new(
            b'secret_key',
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return token
    
    def list_users(self) -> list:
        """Get list of all registered users (without passwords)"""
        return [
            {
                'email': user['email'],
                'full_name': user.get('full_name', ''),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login')
            }
            for user in self.users.values()
        ]
    
    def delete_user(self, email: str, admin_email: str) -> Dict[str, Any]:
        """
        Delete a user (only if requester is admin)
        
        Args:
            email: Email of user to delete
            admin_email: Email of admin requesting deletion
        
        Returns:
            Dict with success status
        """
        # Simple admin check (first registered user is admin)
        if not self.users:
            return {'success': False, 'message': 'No users to delete'}
        
        first_user_email = list(self.users.keys())[0]
        if admin_email != first_user_email:
            return {'success': False, 'message': 'Only admin can delete users'}
        
        if email not in self.users:
            return {'success': False, 'message': 'User not found'}
        
        del self.users[email]
        if email in self.sessions:
            del self.sessions[email]
        
        self.save_users()
        self.save_sessions()
        logger.info(f"User deleted: {email}")
        return {'success': True, 'message': f'User {email} deleted successfully'}


# Global auth manager instance
auth_manager = AuthManager()
