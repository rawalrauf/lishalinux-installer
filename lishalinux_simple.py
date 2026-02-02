#!/usr/bin/env python3
"""
LishaLinux Installer - Simple archinstall configuration generator
"""

import json
import sys
import os
import subprocess
import getpass
from pathlib import Path

def get_disk_size(disk_path):
    """Get disk size in bytes"""
    try:
        result = subprocess.run(['lsblk', '-b', '-d', '-n', '-o', 'SIZE', disk_path], 
                              capture_output=True, text=True)
        return int(result.stdout.strip())
    except:
        # Fallback to 20GB if we can't detect
        return 20 * 1024 * 1024 * 1024

def get_user_input():
    """Get required user inputs"""
    print("=== LishaLinux Installer ===")
    print("Arch-based distro with Hyprland and optimized defaults\n")
    
    # Show available disks
    print("Available disks:")
    try:
        result = subprocess.run(['lsblk', '-d', '-n', '-o', 'NAME,SIZE,TYPE'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except:
        print("Could not list disks")
    
    # Get user inputs
    disk = input("Target disk (e.g., sda): ").strip()
    if not disk.startswith('/dev/'):
        disk = f"/dev/{disk}"
    
    hostname = input("Hostname [lishalinux]: ").strip() or "lishalinux"
    
    # Root password right after hostname
    root_password = getpass.getpass("Root password: ")
    root_confirm = getpass.getpass("Confirm root password: ")
    while root_password != root_confirm:
        print("Passwords don't match!")
        root_password = getpass.getpass("Root password: ")
        root_confirm = getpass.getpass("Confirm root password: ")
    
    timezone = input("Timezone [UTC]: ").strip() or "UTC"
    
    # Direct install option
    direct_install = input("Start installation immediately? [y/N]: ").strip().lower() == 'y'
    
    username = input("Username: ").strip()
    user_password = getpass.getpass(f"Password for {username}: ")
    user_confirm = getpass.getpass(f"Confirm password for {username}: ")
    while user_password != user_confirm:
        print("Passwords don't match!")
        user_password = getpass.getpass(f"Password for {username}: ")
        user_confirm = getpass.getpass(f"Confirm password for {username}: ")
    
    return {
        'disk': disk,
        'hostname': hostname,
        'timezone': timezone,
        'username': username,
        'user_password': user_password,
        'root_password': root_password,
        'sudo_access': True,
        'direct_install': direct_install
    }

def create_config(user_data):
    """Create archinstall configuration"""
    
    # Calculate root partition size (total - boot - GPT overhead)
    disk_size = get_disk_size(user_data['disk'])
    boot_size = 1 * 1024 * 1024 * 1024  # 1 GiB
    gpt_overhead = 34 * 512 * 2  # GPT headers at start and end
    root_size = disk_size - boot_size - gpt_overhead - (1024 * 1024)  # Extra 1MB buffer
    
    return {
        "app_config": {
            "audio_config": {
                "audio": "pipewire"
            },
            "bluetooth_config": {
                "enabled": True
            }
        },
        "archinstall-language": "English",
        "auth_config": {},
        "bootloader_config": {
            "bootloader": "Limine",
            "removable": True,
            "uki": False
        },
        "custom_commands": [],
        "disk_config": {
            "btrfs_options": {
                "snapshot_config": {
                    "type": "Snapper"
                }
            },
            "config_type": "default_layout",
            "device_modifications": [
                {
                    "device": user_data['disk'],
                    "partitions": [
                        {
                            "btrfs": [],
                            "dev_path": None,
                            "flags": [
                                "boot",
                                "esp"
                            ],
                            "fs_type": "fat32",
                            "mount_options": [],
                            "mountpoint": "/boot",
                            "obj_id": "boot-partition-id",
                            "size": {
                                "sector_size": {
                                    "unit": "B",
                                    "value": 512
                                },
                                "unit": "GiB",
                                "value": 1
                            },
                            "start": {
                                "sector_size": {
                                    "unit": "B",
                                    "value": 512
                                },
                                "unit": "MiB",
                                "value": 1
                            },
                            "status": "create",
                            "type": "primary"
                        },
                        {
                            "btrfs": [
                                {
                                    "mountpoint": "/",
                                    "name": "@"
                                },
                                {
                                    "mountpoint": "/home",
                                    "name": "@home"
                                },
                                {
                                    "mountpoint": "/var/log",
                                    "name": "@log"
                                },
                                {
                                    "mountpoint": "/var/cache/pacman/pkg",
                                    "name": "@pkg"
                                }
                            ],
                            "dev_path": None,
                            "flags": [],
                            "fs_type": "btrfs",
                            "mount_options": [
                                "compress=zstd"
                            ],
                            "mountpoint": None,
                            "obj_id": "root-partition-id",
                            "size": {
                                "sector_size": {
                                    "unit": "B",
                                    "value": 512
                                },
                                "unit": "B",
                                "value": root_size
                            },
                            "start": {
                                "sector_size": {
                                    "unit": "B",
                                    "value": 512
                                },
                                "unit": "B",
                                "value": 1074790400
                            },
                            "status": "create",
                            "type": "primary"
                        }
                    ],
                    "wipe": True
                }
            ]
        },
        "hostname": user_data['hostname'],
        "kernels": [
            "linux"
        ],
        "locale_config": {
            "kb_layout": "us",
            "sys_enc": "UTF-8",
            "sys_lang": "en_US.UTF-8"
        },
        "mirror_config": {
            "custom_repositories": [],
            "custom_servers": [],
            "mirror_regions": {
                "Worldwide": [
                    "http://mirror.rackspace.com/archlinux/$repo/os/$arch",
                    "https://mirror.rackspace.com/archlinux/$repo/os/$arch",
                    "https://ftpmirror.infania.net/mirror/archlinux/$repo/os/$arch",
                    "https://geo.mirror.pkgbuild.com/$repo/os/$arch",
                    "https://fastly.mirror.pkgbuild.com/$repo/os/$arch"
                ]
            },
            "optional_repositories": []
        },
        "network_config": {
            "type": "iso"
        },
        "ntp": True,
        "packages": [
            "git",
            "base-devel",
            "fzf"
        ],
        "parallel_downloads": 0,
        "profile_config": {
            "gfx_driver": "All open-source",
            "greeter": "sddm",
            "profile": {
                "custom_settings": {
                    "Hyprland": {
                        "seat_access": "polkit"
                    }
                },
                "details": [
                    "Hyprland"
                ],
                "main": "Desktop"
            }
        },
        "script": None,
        "services": [],
        "swap": {
            "algorithm": "zstd",
            "enabled": True
        },
        "timezone": user_data['timezone'],
        "version": "3.0.15"
    }

def create_creds(user_data):
    """Create credentials file"""
    return {
        "!root-password": user_data['root_password'],
        "!users": [
            {
                "username": user_data['username'],
                "!password": user_data['user_password'],
                "sudo": user_data['sudo_access']
            }
        ]
    }

def create_post_install():
    """Create post-installation script"""
    return '''#!/bin/bash
set -e
echo "=== LishaLinux Post-Installation ==="

# Install LishaLinux configs
cd /tmp
git clone https://github.com/rawalrauf/lishalinux
cd lishalinux
chmod +x install.sh
./install.sh

echo "=== LishaLinux setup complete ==="
'''

def main():
    if os.geteuid() != 0:
        print("Run as root")
        sys.exit(1)
    
    # Get user input
    user_data = get_user_input()
    
    # Create files
    config = create_config(user_data)
    creds = create_creds(user_data)
    post_install = create_post_install()
    
    # Write files
    config_file = Path("/tmp/lishalinux_config.json")
    creds_file = Path("/tmp/lishalinux_creds.json")
    post_file = Path("/tmp/lishalinux_post.sh")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    with open(creds_file, 'w') as f:
        json.dump(creds, f, indent=2)
    
    with open(post_file, 'w') as f:
        f.write(post_install)
    post_file.chmod(0o755)
    
    print(f"\nFiles created:")
    print(f"Config: {config_file}")
    print(f"Creds: {creds_file}")
    print(f"Post-install: {post_file}")
    
    # Run archinstall
    print("\nStarting installation...")
    try:
        cmd = [
            'archinstall',
            '--config', str(config_file),
            '--creds', str(creds_file)
        ]
        
        # Add --silent flag for direct install
        if user_data['direct_install']:
            cmd.append('--silent')
            
        subprocess.run(cmd, check=True)
        
        print("\n=== Installation complete! ===")
        print("Reboot to start LishaLinux")
        
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
