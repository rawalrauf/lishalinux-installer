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

def get_user_input():
    """Get required user inputs"""
    print("=== LishaLinux Installer ===")

    print("Available disks:")
    try:
        result = subprocess.run(['lsblk', '-d', '-n', '-o', 'NAME,SIZE,TYPE'], capture_output=True, text=True)
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
        'username': username,
        'user_password': user_password,
        'root_password': root_password,
    }

def create_config(user_data):
    """Create archinstall configuration"""
    disk_size = int(subprocess.run(['lsblk','-b','-d','-n','-o','SIZE', user_data['disk']], capture_output=True, text=True).stdout.strip())

    mb = 1024 * 1024 # Definig 1MB 
    boot_start = 1 * mb  # 1MB
    boot_size = 1024 * mb  # 1GB
    root_start = boot_start + boot_size  # 1025MB
    gpt_headers = 2 * mb
    root_size = disk_size - root_start - gpt_headers
    root_size = (root_size // mb) * mb  # Align to MB boundary
    
    if root_size < 10 * 1024 * mb:
        raise RuntimeError("Root partition smaller than 10GB, Use another disk")

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

        "custom_commands": [
            "curl -fsSL https://raw.githubusercontent.com/rawalrauf/lishalinux-installer/main/lishalinux-chroot-stage.sh | bash"
        ],
        "disk_config": {
            "btrfs_options": {
                "snapshot_config": {
                    "type": "Snapper"
                }
            },
            "config_type": "manual_partitioning",
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
                                "value": root_start
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
                "India": [],
                    "Singapore": [],
                    "Germany": [],
                    "United States": [],
            },
            "optional_repositories": []
        },
        "network_config": {
            "type": "iso"
        },
        "ntp": True,
        "packages": [
            "git",
            "kitty",
            "gum",
            "ttf-cascadia-mono-nerd"
        ],
        "parallel_downloads": 5,
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
        "timezone": "UTC",
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
                "sudo": True
            }
        ]
    }

def main():
    user_data = get_user_input()
    # Create files
    config = create_config(user_data)
    creds = create_creds(user_data)
    
    # Write files
    config_file = Path("/tmp/lishalinux_config.json")
    creds_file = Path("/tmp/lishalinux_creds.json")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    with open(creds_file, 'w') as f:
        json.dump(creds, f, indent=2)
    
    print("\nStarting installation...")
    try:
        subprocess.run(["archinstall", "--config", str(config_file), "--creds", str(creds_file), "--silent", "--skip-version-check", "--skip-wifi-check"], check=True)
        
        print("You can Reboot Now")
        # subprocess.run(["reboot"], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
