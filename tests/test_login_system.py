#!/usr/bin/env python3
"""
Simple test/demo script for the System Manager CLI login system
Run this to verify the login functionality works
"""

import json
from pathlib import Path
from system_manager_cli.Primary_Project_Code.auth import auth_manager

def demo_login_system():
    """Demonstrate the login system functionality"""
    print("="*60)
    print("System Manager CLI - Login System Demo")
    print("="*60 + "\n")
    
    # Test 1: Register a user
    print("Test 1: Registering a new user...")
    result = auth_manager.register_user(
        email="demo@example.com",
        password="DemoPass123",
        full_name="Demo User"
    )
    print(f"Result: {result['message']}\n")
    
    # Test 2: Try registering with invalid email
    print("Test 2: Registering with invalid email...")
    result = auth_manager.register_user(
        email="invalid-email",
        password="DemoPass123",
        full_name="Test User"
    )
    print(f"Result: {result['message']}\n")
    
    # Test 3: Try registering with weak password
    print("Test 3: Registering with weak password...")
    result = auth_manager.register_user(
        email="test@example.com",
        password="weak",
        full_name="Test User"
    )
    print(f"Result: {result['message']}\n")
    
    # Test 4: Register another valid user
    print("Test 4: Registering another new user...")
    result = auth_manager.register_user(
        email="test@example.com",
        password="TestPass123",
        full_name="Test User"
    )
    print(f"Result: {result['message']}\n")
    
    # Test 5: Try registering duplicate email
    print("Test 5: Trying to register duplicate email...")
    result = auth_manager.register_user(
        email="demo@example.com",
        password="AnotherPass123",
        full_name="Another User"
    )
    print(f"Result: {result['message']}\n")
    
    # Test 6: Login with correct credentials
    print("Test 6: Login with correct credentials...")
    result = auth_manager.login("demo@example.com", "DemoPass123")
    print(f"Result: {result['message']}\n")
    
    # Test 7: Login with incorrect password
    print("Test 7: Login with incorrect password...")
    result = auth_manager.login("demo@example.com", "WrongPassword")
    print(f"Result: {result['message']}\n")
    
    # Test 8: Check if user is logged in
    print("Test 8: Checking session status...")
    is_logged_in = auth_manager.is_logged_in("demo@example.com")
    print(f"User 'demo@example.com' is logged in: {is_logged_in}\n")
    
    # Test 9: List all users
    print("Test 9: Listing all registered users...")
    users = auth_manager.list_users()
    for user in users:
        print(f"  - {user['email']} ({user['full_name']})")
    print()
    
    # Test 10: Change password
    print("Test 10: Changing password...")
    result = auth_manager.change_password(
        "test@example.com",
        "TestPass123",
        "NewPass456"
    )
    print(f"Result: {result['message']}\n")
    
    # Test 11: Login with new password
    print("Test 11: Login with new password...")
    result = auth_manager.login("test@example.com", "NewPass456")
    print(f"Result: {result['message']}\n")
    
    # Test 12: Logout
    print("Test 12: Logging out...")
    result = auth_manager.logout("demo@example.com")
    print(f"Result: {result['message']}\n")
    
    # Test 13: Request a password reset
    print("Test 13: Requesting password reset...")
    original_generate_reset_code = auth_manager._generate_reset_code
    auth_manager._generate_reset_code = staticmethod(lambda: "482193")
    result = auth_manager.request_password_reset("test@example.com")
    print(f"Result: {result['message']}\n")

    # Test 14: Reset password with the emailed code
    print("Test 14: Resetting password with code...")
    result = auth_manager.reset_password_with_code(
        "test@example.com",
        "482193",
        "ResetPass789"
    )
    print(f"Result: {result['message']}\n")
    auth_manager._generate_reset_code = original_generate_reset_code

    # Test 15: Check if user is logged in after logout
    print("Test 15: Checking session after logout...")
    is_logged_in = auth_manager.is_logged_in("demo@example.com")
    print(f"User 'demo@example.com' is logged in: {is_logged_in}\n")
    
    print("="*60)
    print("Demo completed successfully!")
    print("="*60)
    
    # Demonstrate Drive email prompt (simulated)
    print("\nTest 16: Simulating Drive email selection prompt")
    from main import current_user, upload_backup_cloud
    # ensure user is logged in in context
    current_user['email'] = 'demo@example.com'
    current_user['name'] = 'Demo User'
    # patch click.confirm to avoid interactive input
    import click
    orig_confirm = click.confirm
    click.confirm = lambda message, default=True: True
    try:
        upload_backup_cloud.callback('..\\test_backup_dir\\system_backups\\test_to_backup_backup_20260226_055603.zip', remote='gdrive', remote_path='/Test Backups', list_remotes=False)
    except Exception as e:
        print(f"(expected prompt simulation) {e}")
    finally:
        click.confirm = orig_confirm

    # Show data files
    print("\nData files created:")
    data_dir = Path(__file__).parent / 'data'
    if data_dir.exists():
        for file in data_dir.glob('*.json'):
            print(f"  - {file.name}")

if __name__ == '__main__':
    demo_login_system()
