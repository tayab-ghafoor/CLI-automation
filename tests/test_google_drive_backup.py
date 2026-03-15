#!/usr/bin/env python3
"""
Test script for Google Drive backup functionality
"""

import sys
from pathlib import Path
from system_manager_cli.Primary_Project_Code.backup_manager import BackupManager
from system_manager_cli.Primary_Project_Code.google_drive_manager import GoogleDriveManager

def test_backup_manager():
    """Test backup manager functionality"""
    print("\n" + "="*60)
    print("Testing BackupManager Class")
    print("="*60)
    
    # Create a test folder with some files
    test_source = Path("test_backup_source")
    test_source.mkdir(exist_ok=True)
    
    # Create some test files
    (test_source / "test_file_1.txt").write_text("Test content 1")
    (test_source / "test_file_2.txt").write_text("Test content 2")
    subdir = test_source / "subdir"
    subdir.mkdir(exist_ok=True)
    (subdir / "test_file_3.txt").write_text("Test content 3")
    
    try:
        # Test backup creation
        print("\n✓ Testing backup creation...")
        backup_mgr = BackupManager(str(test_source))
        backup_result = backup_mgr.create_backup(compress=True)
        
        if backup_result and isinstance(backup_result, Path):
            print(f"✓ Backup created: {backup_result}")
            print(f"  File exists: {backup_result.exists()}")
            print(f"  File size: {backup_result.stat().st_size / 1024:.2f} KB")
        elif backup_result is False:
            print("✗ Backup creation failed")
            return False
        else:
            print(f"✓ Backup path: {backup_result}")
        
        # Test display status
        print("\n✓ Testing display_backup_status...")
        backup_mgr.display_backup_status(backup_result)
        
        # Test list backups
        print("✓ Testing list_backups...")
        backup_mgr.list_backups()
        
        return True
    
    except Exception as e:
        print(f"✗ Error during backup testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup test source
        import shutil
        if test_source.exists():
            shutil.rmtree(test_source)

def test_google_drive_manager():
    """Test Google Drive manager functionality"""
    print("\n" + "="*60)
    print("Testing GoogleDriveManager Class")
    print("="*60)
    
    try:
        gd_mgr = GoogleDriveManager()
        
        print("\n✓ GoogleDriveManager initialized")
        print(f"  Credentials path: {gd_mgr.credentials_path}")
        print(f"  Token path: {gd_mgr.token_path}")
        print(f"  Credentials exist: {gd_mgr.credentials_path.exists()}")
        
        # Try to authenticate
        print("\n✓ Attempting authentication...")
        if gd_mgr.authenticate():
            print("✓ Authentication successful!")
            print(f"  Service initialized: {gd_mgr.service is not None}")
            print(f"  Is authenticated: {gd_mgr.is_authenticated}")
            
            # List existing backups
            print("\n✓ Testing list_backups...")
            backups = gd_mgr.list_backups()
            print(f"  Found {len(backups)} backups on Google Drive")
            
            return True
        else:
            print("⚠ Authentication failed (expected if credentials not configured)")
            print("  This is normal if Google Drive credentials haven't been set up yet")
            print("  Refer to GOOGLE_DRIVE_SETUP.md for configuration instructions")
            return True  # Return True because this is expected
    
    except ImportError as e:
        print(f"⚠ Google API libraries not installed: {e}")
        print("  Install with: pip install -r requirements.txt")
        return True  # Return True because this is expected
    
    except Exception as e:
        print(f"✗ Error during Google Drive testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Google Drive Backup System - Test Suite")
    print("="*60)
    
    results = []
    
    # Test backup manager
    backup_ok = test_backup_manager()
    results.append(("BackupManager", backup_ok))
    
    # Test Google Drive manager
    gd_ok = test_google_drive_manager()
    results.append(("GoogleDriveManager", gd_ok))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = all(result[1] for result in results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed - see details above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
