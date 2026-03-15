"""
Rclone Manager
Handles backup uploads to cloud storage using Rclone
Supports: Google Drive, OneDrive, AWS S3, Dropbox, and many more
"""

import subprocess
import json
import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable
from .logger import get_logger
from .config import Config

logger = get_logger(__name__)


class RcloneManager:
    """Manages Rclone operations for cloud backups"""
    
    def __init__(self):
        self.rclone_path = self._find_rclone()
        self.is_available = self.rclone_path is not None
        self.config_path = Path.home() / '.config' / 'rclone' / 'rclone.conf'
        
        if not self.is_available:
            logger.warning("Rclone not found. Please install it from https://rclone.org/downloads/")
    
    def _find_rclone(self) -> Optional[str]:
        """Find rclone executable in system PATH or common locations"""
        try:
            # First try system PATH
            result = subprocess.run(
                ['where', 'rclone'] if os.name == 'nt' else ['which', 'rclone'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0].strip()  # Take first line if multiple
                if path and Path(path).exists():
                    logger.info(f"Found rclone at: {path}")
                    return path
            
            # Try common Windows installation paths
            if os.name == 'nt':
                common_paths = [
                    Path.home() / 'bin' / 'rclone.exe',
                    Path.home() / 'AppData' / 'Local' / 'Programs' / 'rclone' / 'rclone.exe',
                    Path('C:\\Program Files\\rclone\\rclone.exe'),
                    Path('C:\\Program Files (x86)\\rclone\\rclone.exe'),
                ]
                
                for rclone_path in common_paths:
                    if rclone_path.exists():
                        logger.info(f"Found rclone at: {rclone_path}")
                        return str(rclone_path)
            
            return None
        except Exception as e:
            logger.warning(f"Could not find rclone: {e}")
            return None
    
    def list_remotes(self) -> List[str]:
        """List all configured Rclone remotes"""
        try:
            if not self.is_available or self.rclone_path is None:
                logger.error("Rclone not available")
                return []
            
            result = subprocess.run(
                [self.rclone_path, 'listremotes'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                remotes = [r.strip(':') for r in result.stdout.strip().split('\n') if r.strip()]
                logger.info(f"Available remotes: {remotes}")
                return remotes
            
            logger.warning("Could not list remotes")
            return []
        
        except Exception as e:
            logger.error(f"Error listing remotes: {e}")
            return []
    
    def check_rclone_installed(self) -> bool:
        """Check if Rclone is properly installed"""
        if not self.is_available or self.rclone_path is None:
            return False
        
        try:
            result = subprocess.run(
                [self.rclone_path, 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"Rclone version: {result.stdout.strip()}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking rclone: {e}")
            return False
    
    def check_remote_connection(self, remote_name: str) -> Tuple[bool, str]:
        """
        Test connection to a remote destination
        
        Args:
            remote_name: Name of the configured remote
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not self.is_available or self.rclone_path is None:
                return False, "Rclone not installed"
            
            result = subprocess.run(
                [self.rclone_path, 'lsd', f'{remote_name}:/'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully connected to remote: {remote_name}")
                return True, f"Connected to {remote_name}"
            else:
                error_msg = result.stderr.strip()
                logger.warning(f"Failed to connect to {remote_name}: {error_msg}")
                return False, error_msg
        
        except subprocess.TimeoutExpired:
            msg = f"Connection timeout for {remote_name}"
            logger.error(msg)
            return False, msg
        except Exception as e:
            logger.error(f"Error checking remote connection: {e}")
            return False, str(e)

    @staticmethod
    def _extract_progress_percent(line: str) -> Optional[float]:
        """Extract transfer percentage from an rclone output line."""
        matches = re.findall(r'(\d{1,3}(?:\.\d+)?)%', line)
        if not matches:
            return None
        try:
            value = float(matches[-1])
            if 0 <= value <= 100:
                return value
        except ValueError:
            return None
        return None
    
    def upload_backup(
        self,
        backup_path: str,
        remote_name: str,
        remote_path: str = '/backups',
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> bool:
        """
        Upload backup to cloud using Rclone
        Supports both files and folder uploads
        
        Args:
            backup_path: Local path to the backup file or folder
            remote_name: Configured Rclone remote name
            remote_path: Path on the remote to upload to
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_available or self.rclone_path is None:
                logger.error("Rclone not available")
                return False
            
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                logger.error(f"Backup path not found: {backup_path}")
                return False
            
            # Determine if uploading file or folder
            if backup_file.is_file():
                # Upload as single file
                source = str(backup_file)
                filename = backup_file.name
                destination = f"{remote_name}:{remote_path}/{filename}"
                
                logger.info(f"Starting Rclone file upload: {source} -> {destination}")
                
                # Build rclone copy command for file
                cmd = [
                    self.rclone_path,
                    'copy',
                    source,
                    destination,
                    '--progress',
                    '--stats',
                    '1s',
                    '--stats-one-line',
                    '--use-json-log',
                    '--verbose'
                ]
            else:
                # Upload as folder structure
                source = str(backup_file)
                folder_name = backup_file.name
                destination = f"{remote_name}:{remote_path}/{folder_name}"
                
                logger.info(f"Starting Rclone folder upload: {source} -> {destination}")
                
                # Build rclone sync command for folder (preserves structure)
                cmd = [
                    self.rclone_path,
                    'copy',
                    source,
                    destination,
                    '--progress',
                    '--stats',
                    '1s',
                    '--stats-one-line',
                    '--use-json-log',
                    '--verbose',
                    '--create-empty-src-dirs'  # Preserve folder structure
                ]
            
            # Run upload and stream progress output.
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            last_percent = -1.0
            output_tail: List[str] = []
            if process.stdout is not None:
                for raw_line in process.stdout:
                    line = raw_line.strip()
                    if not line:
                        continue

                    output_tail.append(line)
                    if len(output_tail) > 20:
                        output_tail.pop(0)

                    msg = line
                    if line.startswith('{') and '"msg"' in line:
                        try:
                            parsed = json.loads(line)
                            msg = str(parsed.get('msg', line))
                        except json.JSONDecodeError:
                            msg = line

                    percent = self._extract_progress_percent(msg)
                    if percent is not None and percent > last_percent:
                        last_percent = percent
                        if progress_callback:
                            progress_callback(percent, msg)

            process.wait()

            if process.returncode == 0:
                if progress_callback and last_percent < 100:
                    progress_callback(100.0, "Completed")
                logger.info(f"Successfully uploaded backup: {backup_file.name}")
                return True
            else:
                error_msg = '\n'.join(output_tail[-5:])
                logger.error(f"Rclone upload failed: {error_msg}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error("Upload timeout - file/folder may be too large")
            return False
        except Exception as e:
            logger.error(f"Error uploading backup with Rclone: {e}")
            return False
    
    def sync_backup(self, backup_path: str, remote_name: str, remote_path: str = '/backups') -> bool:
        """
        Sync backup to cloud using bidirectional sync
        
        Args:
            backup_path: Local path to the backup file or folder
            remote_name: Configured Rclone remote name
            remote_path: Path on the remote to sync with
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_available or self.rclone_path is None:
                logger.error("Rclone not available")
                return False
            
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                logger.error(f"Backup path not found: {backup_path}")
                return False
            
            # Prepare source and destination
            source = str(backup_file)
            destination = f"{remote_name}:{remote_path}"
            
            logger.info(f"Starting Rclone sync: {source} -> {destination}")
            
            # Build rclone sync command
            cmd = [
                self.rclone_path,
                'sync',
                source,
                destination,
                '--progress',
                '--verbose',
                '--create-empty-src-dirs'
            ]
            
            # Run sync
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=None
            )
            
            if result.returncode == 0:
                logger.info("Successfully synced backup")
                return True
            else:
                error_msg = result.stderr.strip()
                logger.error(f"Rclone sync failed: {error_msg}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error("Sync timeout")
            return False
        except Exception as e:
            logger.error(f"Error syncing backup with Rclone: {e}")
            return False
    
    def list_remote_backups(self, remote_name: str, remote_path: str = '/backups') -> List[Dict]:
        """
        List backups on remote storage
        
        Args:
            remote_name: Configured Rclone remote name
            remote_path: Path on the remote to list
        
        Returns:
            List of backup info dictionaries
        """
        try:
            if not self.is_available or self.rclone_path is None:
                logger.error("Rclone not available")
                return []
            
            cmd = [
                self.rclone_path,
                'lsf',
                f'{remote_name}:{remote_path}',
                '--format', 'ps'  # Size and path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                backups = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.rsplit(';', 1)
                        if len(parts) == 2:
                            size_str = parts[1]
                            filename = parts[0]
                            try:
                                size = int(size_str)
                                backups.append({
                                    'name': filename,
                                    'size': size,
                                    'size_mb': size / (1024 * 1024)
                                })
                            except ValueError:
                                pass
                
                logger.info(f"Found {len(backups)} backups on remote")
                return sorted(backups, key=lambda x: x['name'], reverse=True)
            
            logger.warning(f"Could not list remote backups: {result.stderr}")
            return []
        
        except subprocess.TimeoutExpired:
            logger.error("List timeout")
            return []
        except Exception as e:
            logger.error(f"Error listing remote backups: {e}")
            return []
    
    def get_status_message(self) -> str:
        """Get current Rclone status message"""
        if not self.is_available:
            return "❌ Rclone not installed. Install from https://rclone.org/downloads/"
        
        if not self.check_rclone_installed():
            return "❌ Rclone installation issue detected"
        
        remotes = self.list_remotes()
        if not remotes:
            return "⚠️  No Rclone remotes configured. Run 'rclone config' to set up"
        
        return f"✅ Rclone ready. Configured remotes: {', '.join(remotes)}"


# Global instance
rclone_manager = RcloneManager()
