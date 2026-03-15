#!/usr/bin/env python3
"""Test backup and rclone upload"""

from system_manager_cli.Primary_Project_Code.backup_manager import BackupManager
from system_manager_cli.Primary_Project_Code.rclone_manager import rclone_manager

# Test with a small folder
test_source = 'd:\\python\\test_to_backup'
backup_mgr = BackupManager(test_source, 'd:\\python\\test_backup_dir')

# Create backup
print("Creating backup...")
backup_result = backup_mgr.create_backup(compress=True)
if backup_result:
        print(f'✅ Backup created: {backup_result}')
        
        # optionally send email (requires EMAIL_SENDER / PASSWORD configuration)
        try:
            print("\nAttempting to send notification email...")
            from system_manager_cli.Primary_Project_Code.email_notifier import EmailNotifier
            ok = EmailNotifier.send_backup_completion_email(
                'user@example.com',
                test_source,
                str(backup_result),
                0.0,
                'Manual'
            )
            print(f'Email sent: {ok}')
        except Exception as e:
            print(f'Email test skipped: {e}')
        
        # Test rclone connection first
        print("\nTesting rclone connection...")
        success, msg = rclone_manager.check_remote_connection('gdrive')
        print(f'Connection test: {msg}')
    # Test rclone upload
    print("\nUploading to Google Drive...")
    success = rclone_manager.upload_backup(backup_result, 'gdrive', '/Test Backups')
    print(f'Upload success: {success}')
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Upload failed")
else:
    print('❌ Backup creation failed')
