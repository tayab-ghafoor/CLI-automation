import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from .config import Config
from .logger import get_logger
from .email_notifier import EmailNotifier

logger = get_logger(__name__, 'backup_manager.log')

class BackupManager:
    """Manage file and folder backups"""
    
    def __init__(self, source_folder, backup_drive=None):
        self.source_folder = Path(source_folder)
        self.backup_drive = Path(backup_drive or Config.BACKUP_DRIVE)
        self.max_backups = Config.MAX_BACKUPS
        self.backup_base = self.backup_drive / 'system_backups'
        self.source_name = self.source_folder.name
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        try:
            self.backup_base.mkdir(parents=True, exist_ok=True)
            logger.info(f"Backup directory ensured: {self.backup_base}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            return False
    
    def get_existing_backups(self):
        """Get list of existing backups sorted by date"""
        try:
            backup_items = []
            for f in self.backup_base.glob(f"{self.source_name}_backup_*"):
                if f.is_dir() or f.is_file():
                    backup_items.append(f)
            
            # Sort by modification time, newest first
            backup_folders = sorted(
                backup_items,
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            return backup_folders
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self):
        """Keep only the last N backups"""
        try:
            backups = self.get_existing_backups()
            
            if len(backups) > self.max_backups:
                to_delete = backups[self.max_backups:]
                
                for backup_folder in to_delete:
                    try:
                        if backup_folder.is_dir():
                            shutil.rmtree(backup_folder)
                        else:
                            backup_folder.unlink()
                        logger.info(f"Deleted old backup: {backup_folder}")
                    except Exception as e:
                        logger.error(f"Failed to delete backup {backup_folder}: {e}")
            
            return len(backups)
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0
    
    def create_backup(self, compress=True):
        """Create a backup of the source file or folder"""
        try:
            if not self.ensure_backup_directory():
                return False
            
            if not self.source_folder.exists():
                logger.error(f"Source not found: {self.source_folder}")
                return False
            
            # Create backup folder with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{self.source_name}_backup_{timestamp}"
            
            # Handle single file backup
            if self.source_folder.is_file():
                logger.info(f"Starting backup of file: {self.source_folder}")
                
                if compress:
                    # For a single file, create ZIP
                    zip_path = self.backup_base / f"{backup_name}.zip"
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        zipf.write(self.source_folder, arcname=self.source_folder.name)
                    logger.info(f"File backed up as ZIP: {zip_path}")
                    return zip_path
                else:
                    # Copy file directly to backup location
                    backup_file = self.backup_base / f"{backup_name}_{self.source_folder.name}"
                    shutil.copy2(self.source_folder, backup_file)
                    logger.info(f"File backed up: {backup_file}")
                    self.cleanup_old_backups()
                    return backup_file
            
            # Handle folder backup
            else:
                logger.info(f"Starting backup of folder: {self.source_folder}")
                backup_folder = self.backup_base / backup_name
                
                # Copy folder, ignoring problematic directories
                if not self._copytree_ignore_errors(str(self.source_folder), str(backup_folder)):
                    logger.error("Failed to copy directory tree")
                    return False
                
                logger.info(f"Backup created: {backup_folder}")
                
                # Compress if requested
                if compress:
                    zip_path = f"{backup_folder}.zip"
                    if not self._compress_backup(backup_folder, zip_path):
                        logger.error("Compression failed")
                        return False
                    backup_folder = Path(zip_path)
                
                # Cleanup old backups
                self.cleanup_old_backups()
                
                logger.info("Backup completed successfully")
                return backup_folder
        
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def _copytree_ignore_errors(self, src, dst):
        """Copy directory tree, ignoring common problematic directories and files"""
        import os
        ignore_dirs = {'__pycache__', 'node_modules', '.git', '.svn', '.hg', 'logs', 'reports', 'data'}
        ignore_files = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
        
        try:
            os.makedirs(dst, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create destination directory {dst}: {e}")
            return False
        
        try:
            for root, dirs, files in os.walk(src):
                # Remove ignored directories from dirs to prevent walking into them
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                
                # Calculate relative path
                rel_path = os.path.relpath(root, src)
                if rel_path == '.':
                    dest_root = dst
                else:
                    dest_root = os.path.join(dst, rel_path)
                
                # Create destination directory
                try:
                    os.makedirs(dest_root, exist_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to create directory {dest_root}: {e}")
                    continue
                
                # Copy files
                for file in files:
                    if file in ignore_files:
                        continue
                    
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dest_root, file)
                    
                    try:
                        shutil.copy2(src_file, dst_file)
                    except Exception as e:
                        logger.warning(f"Failed to copy {src_file} to {dst_file}: {e}")
                        continue
            
            return True
        except Exception as e:
            logger.error(f"Error during directory copy: {e}")
            return False
        """
        Compress backup folder into a zip file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Compressing backup to {zip_path}")
            
            ignore_dirs = {'__pycache__', 'node_modules', '.git', '.svn', '.hg', 'logs', 'reports', 'data'}
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    # Remove ignored directories from dirs to prevent walking into them
                    dirs[:] = [d for d in dirs if d not in ignore_dirs]
                    
                    for file in files:
                        file_path = Path(root) / file
                        try:
                            arcname = file_path.relative_to(self.backup_base)
                            zipf.write(file_path, arcname)
                        except Exception as e:
                            logger.warning(f"Failed to add {file_path} to zip: {e}")
                            continue
            
            # Delete original folder after compression
            shutil.rmtree(folder_path)
            logger.info(f"Backup compressed successfully: {zip_path}")
            return True
        
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return False
    
    def send_backup_email(self, user_email: str, backup_path, backup_type: str = "Manual") -> bool:
        """
        Send backup completion email notification
        
        Args:
            user_email: User's email address
            backup_path: Path to the backup file/folder
            backup_type: Type of backup (Manual, Scheduled, etc.)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            if not isinstance(backup_path, Path):
                backup_path = Path(str(backup_path))
            
            # Calculate backup size
            backup_size = 0
            if backup_path.is_file():
                backup_size = backup_path.stat().st_size
            elif backup_path.is_dir():
                for item in backup_path.rglob('*'):
                    if item.is_file():
                        backup_size += item.stat().st_size
            
            backup_size_mb = backup_size / (1024 * 1024)
            
            return EmailNotifier.send_backup_completion_email(
                user_email,
                str(self.source_folder),
                str(backup_path),
                backup_size_mb,
                backup_type
            )
        
        except Exception as e:
            logger.error(f"Failed to send backup email: {e}")
            return False
    
    def send_scheduled_backup_email(self, user_email: str, task_name: str, backup_path, 
                                   schedule_time: str) -> bool:
        """
        Send scheduled backup completion email notification
        
        Args:
            user_email: User's email address
            task_name: Name of the scheduled task
            backup_path: Path to the backup file/folder
            schedule_time: When the task is scheduled
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            if not isinstance(backup_path, Path):
                backup_path = Path(str(backup_path))
            
            # Calculate backup size
            backup_size = 0
            if backup_path.is_file():
                backup_size = backup_path.stat().st_size
            elif backup_path.is_dir():
                for item in backup_path.rglob('*'):
                    if item.is_file():
                        backup_size += item.stat().st_size
            
            backup_size_mb = backup_size / (1024 * 1024)
            
            return EmailNotifier.send_scheduled_backup_email(
                user_email,
                task_name,
                str(self.source_folder),
                str(backup_path),
                backup_size_mb,
                schedule_time
            )
        
        except Exception as e:
            logger.error(f"Failed to send scheduled backup email: {e}")
            return False
    
    def display_backup_status(self, backup_path):
        """Display backup status"""
        try:
            if isinstance(backup_path, bool):
                if not backup_path:
                    print("\n❌ Backup failed!")
                return
            
            if not isinstance(backup_path, Path):
                backup_path = Path(str(backup_path))
            
            backup_size = 0
            if backup_path.is_file():
                backup_size = backup_path.stat().st_size
            elif backup_path.is_dir():
                for item in backup_path.rglob('*'):
                    if item.is_file():
                        backup_size += item.stat().st_size
            
            size_mb = backup_size / (1024 * 1024)
            
            print("\n" + "="*50)
            print("    BACKUP COMPLETED SUCCESSFULLY")
            print("="*50)
            print(f"Source: {self.source_folder}")
            print(f"Backup Location: {backup_path}")
            print(f"Size: {size_mb:.2f} MB")
            print(f"Kept Backups: {len(self.get_existing_backups())}/{self.max_backups}")
            print("="*50 + "\n")
        
        except Exception as e:
            logger.error(f"Error displaying backup status: {e}")
    
    def list_backups(self):
        """List all existing backups"""
        try:
            backups = self.get_existing_backups()
            
            print("\n" + "="*50)
            print(f"    EXISTING BACKUPS FOR '{self.source_name}'")
            print("="*50)
            
            if not backups:
                print("No backups found.")
            else:
                for idx, backup in enumerate(backups, 1):
                    size = 0
                    if backup.is_file() and backup.suffix == '.zip':
                        # For zip files, get file size directly
                        size = backup.stat().st_size
                    elif backup.is_dir():
                        # For directories, sum all file sizes
                        for item in backup.rglob('*'):
                            if item.is_file():
                                size += item.stat().st_size
                    
                    mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
                    size_mb = size / (1024 * 1024)
                    
                    backup_type = "ZIP" if backup.is_file() else "DIR"
                    print(f"{idx}. {backup.name} [{backup_type}]")
                    print(f"   Size: {size_mb:.2f} MB | Date: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("="*50 + "\n")
        
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
    
    def upload_to_rclone(
        self,
        backup_path,
        remote_name: str,
        remote_path: str = '/backups',
        progress_callback=None,
    ) -> bool:
        """
        Upload backup to cloud storage using Rclone
        Supports both ZIP files and folder uploads
        
        Args:
            backup_path: Path to the backup file or folder
            remote_name: Configured Rclone remote name (e.g., 'gdrive', 'onedrive', 'dropbox')
            remote_path: Path on the remote to upload to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from .rclone_manager import rclone_manager
            
            # Handle invalid backup paths
            if backup_path is None:
                logger.error("Invalid backup path for Rclone upload")
                return False
            
            if isinstance(backup_path, bool):
                if not backup_path:
                    logger.error("Invalid backup path for Rclone upload")
                    return False
                logger.error("Invalid backup path type for Rclone upload")
                return False
            
            # Convert to Path object
            if isinstance(backup_path, str):
                backup_file: Path = Path(backup_path)
            else:
                backup_file = Path(str(backup_path))
            
            # Verify the backup exists
            if not backup_file.exists():
                logger.error(f"Backup path not found: {backup_file}")
                return False
            
            # Handle different backup types
            if backup_file.is_file():
                # Upload as single file
                logger.info(f"Uploading file backup to Rclone remote '{remote_name}': {backup_file}")
                success = rclone_manager.upload_backup(
                    str(backup_file),
                    remote_name,
                    remote_path,
                    progress_callback=progress_callback
                )
            elif backup_file.is_dir():
                # Try to upload as folder first
                logger.info(f"Uploading folder backup to Rclone remote '{remote_name}': {backup_file}")
                success = rclone_manager.upload_backup(
                    str(backup_file),
                    remote_name,
                    remote_path,
                    progress_callback=progress_callback
                )
            
            if success:
                logger.info(f"Successfully uploaded backup to {remote_name}")
            else:
                logger.error(f"Failed to upload backup to {remote_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error uploading to Rclone: {e}")
            return False
            remote_path
            
            
            if success:
                logger.info(f"Successfully uploaded backup to {remote_name}")
                return True
            else:
                logger.error(f"Failed to upload backup to {remote_name}")
                return False
        
        except ImportError as e:
            logger.error(f"Rclone manager not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Error uploading to Rclone: {e}")
            return False
    
    def upload_to_google_drive_rclone(self, backup_path, remote_name: str = 'gdrive') -> bool:
        """
        Upload backup to Google Drive using Rclone
        
        This uses the configured 'gdrive' remote in Rclone for Google Drive uploads.
        Ensure you have configured rclone with 'rclone config' first.
        
        Args:
            backup_path: Path to the backup file or folder
            remote_name: Rclone remote name for Google Drive (default: 'gdrive')
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Uploading backup to Google Drive via Rclone using remote '{remote_name}'")
            return self.upload_to_rclone(backup_path, remote_name, '/System Backups')
        except Exception as e:
            logger.error(f"Error uploading to Google Drive via Rclone: {e}")
            return False
    
    def upload_to_google_drive(self, backup_path, user_email: str) -> bool:
        """
        DEPRECATED: Upload backup to Google Drive
        
        This method is deprecated. Use upload_to_rclone() instead for better compatibility.
        
        Args:
            backup_path: Path to the backup file or folder
            user_email: Email to associate with the backup
        
        Returns:
            True if successful, False otherwise
        """
        try:
            from .google_drive_manager import google_drive_manager
            
            # Handle invalid backup paths
            if backup_path is None:
                logger.error("Invalid backup path for Google Drive upload")
                return False
            
            if isinstance(backup_path, bool):
                if not backup_path:
                    logger.error("Invalid backup path for Google Drive upload")
                    return False
                logger.error("Invalid backup path type for Google Drive upload")
                return False
            
            # Convert to Path object
            if isinstance(backup_path, str):
                backup_file: Path = Path(backup_path)
            else:
                backup_file = Path(str(backup_path))
            
            # If backup_path is a directory, use the .zip if it exists
            if backup_file.is_dir():
                zip_path = Path(str(backup_file) + '.zip')
                if zip_path.exists():
                    backup_file = zip_path
                else:
                    logger.warning(f"No zip file found for backup directory: {backup_file}")
                    return False
            
            # Verify the backup file exists
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            logger.info(f"Uploading backup to Google Drive: {backup_file}")
            
            # Perform the upload
            file_id = google_drive_manager.upload_backup(
                str(backup_file),
                user_email,
                folder_name="System Backups"
            )
            
            if file_id:
                logger.info(f"Successfully uploaded to Google Drive with ID: {file_id}")
                return True
            else:
                logger.error("Failed to upload backup to Google Drive")
                return False
        
        except ImportError as e:
            logger.error(f"Google Drive manager not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return False
