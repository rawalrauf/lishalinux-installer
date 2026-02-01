#!/usr/bin/env python3
"""
Test script to validate LishaLinux installer configuration
"""

import json
import sys
from pathlib import Path

def test_config():
    """Test the configuration generation"""
    
    # Mock user data
    user_data = {
        'disk': '/dev/sda',
        'hostname': 'lishalinux-test',
        'timezone': 'UTC',
        'username': 'testuser',
        'user_password': 'testpass',
        'root_password': 'rootpass',
        'sudo_access': True
    }
    
    # Import the config creation function
    sys.path.append(str(Path(__file__).parent))
    from lishalinux_simple import create_config, create_creds
    
    # Generate config
    config = create_config(user_data)
    creds = create_creds(user_data)
    
    # Validate required fields
    required_fields = [
        'archinstall-language',
        'audio_config',
        'bootloader_config', 
        'disk_config',
        'hostname',
        'kernels',
        'locale_config',
        'mirror_config',
        'network_config',
        'packages',
        'profile_config',
        'swap',
        'timezone'
    ]
    
    print("=== Configuration Validation ===")
    
    for field in required_fields:
        if field in config:
            print(f"✓ {field}")
        else:
            print(f"✗ {field} - MISSING")
    
    # Check specific values
    print("\n=== Value Validation ===")
    
    checks = [
        (config['audio_config']['audio'] == 'pipewire', 'PipeWire audio'),
        (config['bootloader_config']['bootloader'] == 'Limine', 'Limine bootloader'),
        (config['bootloader_config']['removable'] == True, 'Removable bootloader'),
        ('btrfs' in str(config['disk_config']), 'BTRFS filesystem'),
        ('compress=zstd' in str(config['disk_config']), 'BTRFS compression'),
        ('base-devel' in config['packages'], 'base-devel package'),
        ('git' in config['packages'], 'git package'),
        ('fzf' in config['packages'], 'fzf package'),
        ('snapper' in config['packages'], 'snapper package'),
        (config['swap']['enabled'] == True, 'Swap enabled'),
        (config['ntp'] == True, 'NTP enabled'),
        (config['profile_config']['greeter'] == 'sddm', 'SDDM greeter'),
        ('Hyprland' in str(config['profile_config']), 'Hyprland profile')
    ]
    
    for check, description in checks:
        if check:
            print(f"✓ {description}")
        else:
            print(f"✗ {description} - FAILED")
    
    print("\n=== Generated Files ===")
    
    # Write test files
    config_file = Path("/tmp/test_config.json")
    creds_file = Path("/tmp/test_creds.json")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    with open(creds_file, 'w') as f:
        json.dump(creds, f, indent=2)
    
    print(f"Config: {config_file}")
    print(f"Creds: {creds_file}")
    
    print("\n=== Test Complete ===")
    print("Configuration appears valid for archinstall")

if __name__ == "__main__":
    test_config()
