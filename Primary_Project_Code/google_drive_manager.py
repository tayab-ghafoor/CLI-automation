"""
Google Drive Manager
Handles uploading backups to Google Drive
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .logger import get_logger

logger = get_logger(__name__)


class GoogleDriveManager:
    """Manages Google Drive uploads and authentication"""
    
    def __init__(self):
        self.service = None
        self.is_authenticated = False
        self.credentials_path = Path(__file__).parent / 'google_drive_credentials.json'
        self.token_path = Path(__file__).parent / 'google_drive_token.json'
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            # Check if credentials file exists
            if not self.credentials_path.exists():
                logger.error(f"Google Drive credentials file not found: {self.credentials_path}")
                return False

            # Read the credentials JSON to determine type
            try:
                with open(self.credentials_path, 'r', encoding='utf-8') as f:
                    cred_json = json.load(f)
            except Exception as e:
                logger.error(f"Failed to read credentials file: {e}")
                return False

            scopes = ['https://www.googleapis.com/auth/drive']

            # Try service account credentials first
            try:
                if isinstance(cred_json, dict) and (
                    cred_json.get('type') == 'service_account' or 'private_key' in cred_json
                ):
                    from google.oauth2 import service_account

                    credentials = service_account.Credentials.from_service_account_file(
                        self.credentials_path,
                        scopes=scopes
                    )

                    self.service = build('drive', 'v3', credentials=credentials)
                    self.is_authenticated = True
                    logger.info('Google Drive authentication successful (service account)')
                    return True
            except Exception as e:
                logger.warning(f"Service account auth failed, will try OAuth flow: {e}")

            # Fallback to OAuth installed application flow (client_secrets JSON)
            try:
                # Imports local to this block so package absence is handled above
                from google.oauth2.credentials import Credentials as OAuthCredentials
                from google_auth_oauthlib.flow import InstalledAppFlow

                creds = None
                # Load token if it exists
                if self.token_path.exists():
                    try:
                        creds = OAuthCredentials.from_authorized_user_file(str(self.token_path), scopes)
                    except Exception as e:
                        logger.warning(f"Failed to load existing token, will re-run OAuth flow: {e}")

                # If no valid creds, run the installed app flow
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        try:
                            creds.refresh(Request())
                        except Exception as e:
                            logger.warning(f"Failed to refresh token, running full OAuth flow: {e}")
                            creds = None

                    if not creds:
                        flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), scopes)
                        creds = flow.run_local_server(port=0)

                    # Save the credentials for the next run
                    try:
                        with open(self.token_path, 'w', encoding='utf-8') as token_file:
                            token_file.write(creds.to_json())
                    except Exception as e:
                        logger.warning(f"Failed to save token file: {e}")

                # Build service
                self.service = build('drive', 'v3', credentials=creds)
                self.is_authenticated = True
                logger.info('Google Drive authentication successful (OAuth installed flow)')
                return True

            except ImportError:
                logger.error('Google API libraries not installed. Install with: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client')
                return False
            except Exception as e:
                logger.error(f"OAuth authentication error: {e}")
                return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def upload_backup(self, file_path: str, user_email: str, folder_name: str = "Backups") -> Optional[str]:
        """
        Upload backup file to Google Drive
        
        Args:
            file_path: Path to the backup file
            user_email: Email address for organization
            folder_name: Name of folder on Google Drive
        
        Returns:
            File ID if successful, None otherwise
        """
        try:
            if not self.is_authenticated:
                if not self.authenticate():
                    return None
            
            if self.service is None:
                logger.error("Google Drive service not initialized")
                return None
            
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                logger.error(f"Backup file not found: {file_path_obj}")
                return None
            
            # Find or create folder on Google Drive
            folder_id = self._get_or_create_folder(folder_name, user_email)
            
            if not folder_id:
                logger.error("Failed to create/find Google Drive folder")
                return None
            
            # Upload file
            from googleapiclient.http import MediaFileUpload
            
            file_metadata = {
                'name': file_path_obj.name,
                'parents': [folder_id],
                'description': f'Backup created for {user_email}'
            }
            
            media = MediaFileUpload(
                str(file_path_obj),
                mimetype='application/zip' if str(file_path_obj).endswith('.zip') else 'application/octet-stream',
                resumable=True
            )
            
            if self.service is None:
                logger.error("Google Drive service is not initialized")
                return None
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Backup uploaded to Google Drive: {file_id}")
            
            return file_id
        
        except Exception as e:
            logger.error(f"Failed to upload backup to Google Drive: {e}")
            return None
    
    def _get_or_create_folder(self, folder_name: str, user_email: str) -> Optional[str]:
        """
        Get or create a folder on Google Drive
        
        Args:
            folder_name: Name of the folder
            user_email: Email for organization
        
        Returns:
            Folder ID if successful, None otherwise
        """
        try:
            if not self.service:
                logger.error("Google Drive service is not initialized")
                return None
            
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                logger.info(f"Found existing folder: {files[0]['id']}")
                return files[0]['id']
            
            # Create new folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'description': f'Backups for {user_email}'
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created new folder: {folder_id}")
            
            return folder_id
        
        except Exception as e:
            logger.error(f"Failed to get/create folder: {e}")
            return None
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file on Google Drive
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            File info dict if successful, None otherwise
        """
        try:
            if not self.service:
                return None
            
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, size, createdTime, webViewLink'
            ).execute()
            
            return file
        
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
    
    def list_backups(self, folder_name: str = "Backups") -> list:
        """
        List all backup files in a specific folder
        
        Args:
            folder_name: Name of the folder on Google Drive
        
        Returns:
            List of file info dicts
        """
        try:
            if not self.is_authenticated:
                if not self.authenticate():
                    return []
            
            if self.service is None:
                logger.error("Google Drive service is not initialized")
                return []
            
            # Find folder
            folder_id = self._get_or_create_folder(folder_name, "backup")
            
            if not folder_id:
                return []
            
            # List files in folder
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, size, createdTime, webViewLink)',
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} backups on Google Drive")
            
            return files
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_backup(self, file_id: str) -> bool:
        """
        Delete a backup file from Google Drive
        
        Args:
            file_id: Google Drive file ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.service:
                return False
            
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted backup from Google Drive: {file_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False


# Global instance
google_drive_manager = GoogleDriveManager()
