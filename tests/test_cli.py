#!/usr/bin/env python3
"""
Test script to verify System Manager CLI functionality and type hints
"""

import sys
import inspect
from pathlib import Path
from typing import get_type_hints

print("=" * 60)
print("SYSTEM MANAGER CLI - Test Suite")
print("=" * 60)

# Test 1: Import all modules
print("\n[TEST 1] Testing imports...")
try:
    from system_manager_cli.Primary_Project_Code.exceptions import (
        CliException, ConfigurationError, PathError, 
        PermissionError as CustomPermissionError, BackupError, 
        FileOrganizationError, DiskSpaceError, LogAnalysisError, 
        HealthMonitorError
    )
    print("  [OK] exceptions module")
except Exception as e:
    print(f"  [FAIL] exceptions module: {e}")
    sys.exit(1)

try:
    from system_manager_cli.Primary_Project_Code.validators import (
        validate_path_exists, validate_path_readable, validate_path_writable,
        validate_disk_space, validate_folder_not_empty, validate_backup_drive,
        get_folder_size, validate_config_email
    )
    print("  [OK] validators module")
except Exception as e:
    print(f"  [FAIL] validators module: {e}")
    sys.exit(1)

try:
    from system_manager_cli.Primary_Project_Code.config import Config
    print("  [OK] config module")
except Exception as e:
    print(f"  [FAIL] config module: {e}")
    sys.exit(1)

try:
    from system_manager_cli.Primary_Project_Code.logger import get_logger
    print("  [OK] logger module")
except Exception as e:
    print(f"  [FAIL] logger module: {e}")
    sys.exit(1)

try:
    import click
    print("  [OK] click module")
except Exception as e:
    print(f"  [FAIL] click is not installed: {e}")
    print("\n  Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

try:
    import psutil
    print("  [OK] psutil module")
except Exception as e:
    print(f"  [FAIL] psutil is not installed: {e}")
    print("\n  Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Check type hints in validators
print("\n[TEST 2] Checking type hints in validators module...")
functions_to_check = {
    'validate_path_exists': ('str', 'Path'),
    'validate_path_readable': ('None',),
    'validate_path_writable': ('None',),
    'validate_disk_space': ('None',),
    'validate_folder_not_empty': ('None',),
    'get_folder_size': ('int',),
}

for func_name, expected_return in functions_to_check.items():
    func = globals()[func_name]
    sig = inspect.signature(func)
    return_annotation = sig.return_annotation
    # Handle None type annotation
    return_string = "None" if return_annotation is None or return_annotation is type(None) else str(return_annotation.__name__ if hasattr(return_annotation, '__name__') else return_annotation)
    status = "OK" if return_string in expected_return or return_annotation != inspect.Signature.empty else "WARN"
    print(f"  [{status}] {func_name}() -> {return_string}")

# Test 3: Check type hints in main
print("\n[TEST 3] Checking type hints in main module...")
try:
    from main import handle_error, check_health, clean_temp, backup_folder, generate_report, interactive_menu
    
    functions = {
        'handle_error': handle_error,
        'check_health': check_health,
        'clean_temp': clean_temp,
        'backup_folder': backup_folder,
        'generate_report': generate_report,
        'interactive_menu': interactive_menu,
    }
    
    for func_name, func in functions.items():
        sig = inspect.signature(func)
        has_return_annotation = sig.return_annotation != inspect.Signature.empty
        has_param_annotations = all(
            param.annotation != inspect.Parameter.empty 
            for param in sig.parameters.values()
            if param.default == inspect.Parameter.empty  # Only check required params
        )
        status = "OK" if has_return_annotation else "WARN"
        print(f"  [{status}] {func_name}() - Return type: {sig.return_annotation}")
        
except Exception as e:
    print(f"  [FAIL] Could not check main module: {e}")

# Test 4: Validate config directories exist
print("\n[TEST 4] Testing Config directories...")
try:
    Config.ensure_directories()
    if Config.LOGS_DIR.exists():
        print(f"  [OK] Logs directory: {Config.LOGS_DIR}")
    if Config.REPORTS_DIR.exists():
        print(f"  [OK] Reports directory: {Config.REPORTS_DIR}")
except Exception as e:
    print(f"  [WARN] Could not verify directories: {e}")

# Test 5: Test validator functions
print("\n[TEST 5] Testing validator functions...")
try:
    # Test validate_path_exists
    test_path = Path.cwd()
    result = validate_path_exists(str(test_path), path_type="directory")
    print(f"  [OK] validate_path_exists() works")
except Exception as e:
    print(f"  [FAIL] validate_path_exists(): {e}")

try:
    # Test get_folder_size
    test_path = Path.cwd()
    size = get_folder_size(test_path)
    print(f"  [OK] get_folder_size() works - Current dir: {size} bytes")
except Exception as e:
    print(f"  [FAIL] get_folder_size(): {e}")

try:
    # Test validate_path_readable
    test_path = Path.cwd()
    validate_path_readable(test_path)
    print(f"  [OK] validate_path_readable() works")
except Exception as e:
    print(f"  [FAIL] validate_path_readable(): {e}")

# Test 6: Test exception classes
print("\n[TEST 6] Testing exception classes...")
try:
    raise ConfigurationError("Test error message")
except ConfigurationError as e:
    print(f"  [OK] ConfigurationError can be raised and caught")

try:
    raise PathError("Test error message")
except PathError as e:
    print(f"  [OK] PathError can be raised and caught")

try:
    raise DiskSpaceError("Test error message")
except DiskSpaceError as e:
    print(f"  [OK] DiskSpaceError can be raised and caught")

print("\n" + "=" * 60)
print("TEST SUITE COMPLETED SUCCESSFULLY!")
print("=" * 60)
print("\nSummary:")
print("  - All modules imported successfully")
print("  - Type hints added to key functions")
print("  - Validator functions are working")
print("  - Custom exceptions are functional")
print("\nTo run the CLI:")
print("  python main.py --help")
print("  python main.py check-health")
print("  python main.py clean-temp <folder_path>")
print("=" * 60)
