#!/usr/bin/env python3
"""
Test script for new backup features:
- Single file backup
- ZIP vs Folder format choice
"""

from pathlib import Path
from system_manager_cli.Primary_Project_Code.backup_manager import BackupManager
from system_manager_cli.Primary_Project_Code.rclone_manager import rclone_manager

print("="*70)
print("TEST: Single File Backup with Format Selection")
print("="*70)

# Create test file
test_file = Path('d:\\python\\test_single_file.txt')
if not test_file.exists():
    test_file.write_text("This is a test file for backup\n" * 5)
    print(f"✅ Created test file: {test_file}")
else:
    print(f"✅ Test file exists: {test_file}")

test_file_size = test_file.stat().st_size
print(f"   Size: {test_file_size} bytes\n")

# Test 1: Backup as ZIP
print("Test 1: Backup Single File as ZIP")
print("-" * 70)
backup_mgr_zip = BackupManager(str(test_file), 'd:\\python\\test_backup_dir')
backup_path_zip = backup_mgr_zip.create_backup(compress=True)
if backup_path_zip:
    print(f"✅ ZIP Backup created: {backup_path_zip}")
    print(f"   Type: {type(backup_path_zip).__name__}")
    print(f"   Is file: {Path(backup_path_zip).is_file()}")
    print(f"   Size: {Path(backup_path_zip).stat().st_size} bytes\n")
else:
    print("❌ ZIP Backup failed\n")

# Test 2: Backup as Folder (copy only, no compression)
print("Test 2: Backup Single File as Folder (uncompressed)")
print("-" * 70)
backup_mgr_folder = BackupManager(str(test_file), 'd:\\python\\test_backup_dir')
backup_path_folder = backup_mgr_folder.create_backup(compress=False)
if backup_path_folder:
    print(f"✅ Folder Backup created: {backup_path_folder}")
    print(f"   Type: {type(backup_path_folder).__name__}")
    print(f"   Is file: {Path(backup_path_folder).is_file()}")
    print(f"   Size: {Path(backup_path_folder).stat().st_size} bytes\n")
else:
    print("❌ Folder Backup failed\n")

# Test 3: Backup a folder with ZIP format
print("Test 3: Backup Folder as ZIP")
print("-" * 70)
test_folder = Path('d:\\python\\test_to_backup')
if test_folder.exists():
    backup_mgr_folder_zip = BackupManager(str(test_folder), 'd:\\python\\test_backup_dir')
    backup_path_folder_zip = backup_mgr_folder_zip.create_backup(compress=True)
    if backup_path_folder_zip:
        print(f"✅ Folder ZIP Backup created: {backup_path_folder_zip}")
        print(f"   Size: {Path(backup_path_folder_zip).stat().st_size} bytes\n")
    else:
        print("❌ Folder ZIP Backup failed\n")
else:
    print(f"⚠️ Test folder not found: {test_folder}\n")

# Test 4: Backup folder as uncompressed folder structure
print("Test 4: Backup Folder as Folder Structure (uncompressed)")
print("-" * 70)
if test_folder.exists():
    backup_mgr_folder_unzip = BackupManager(str(test_folder), 'd:\\python\\test_backup_dir')
    backup_path_folder_unzip = backup_mgr_folder_unzip.create_backup(compress=False)
    if backup_path_folder_unzip:
        print(f"✅ Folder Structure Backup created: {backup_path_folder_unzip}")
        print(f"   Is directory: {Path(backup_path_folder_unzip).is_dir()}")
        if Path(backup_path_folder_unzip).is_dir():
            total_size = sum(f.stat().st_size for f in Path(backup_path_folder_unzip).rglob('*') if f.is_file())
            print(f"   Total size: {total_size} bytes\n")
    else:
        print("❌ Folder Structure Backup failed\n")

# Test 5: Check rclone availability
print("Test 5: Rclone Upload Capability Check")
print("-" * 70)
print(f"Rclone available: {rclone_manager.is_available}")
print(f"Rclone path: {rclone_manager.rclone_path}")
remotes = rclone_manager.list_remotes()
print(f"Available remotes: {remotes}\n")

print("="*70)
print("✅ All tests completed!")
print("="*70)
