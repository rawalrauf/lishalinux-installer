
#!/usr/bin/env python3
"""
LishaLinux Installer
Archinstall-based automatic installer with Hyprland defaults
"""

import json
import sys
import os
import subprocess
import getpass
from pathlib import Path


def get_user_input():
    print("=== LishaLinux Installer ===")
    print("Arch-based distro with Hyprland and optimized defaults\n")

    # Show available disks
    print("Available disks:\n")
    try:
        result = subprocess.run(
            ["lsblk", "-d", "-n", "-o", "NAME,SIZE,TYPE"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
    except Exception:
        print("⚠️  Could not list disks\n")

    disk = input("Target disk (e.g., sda): ").strip()
    if not disk.startswith("/dev/"):
        disk = f"/dev/{disk}"

    hostname = input("Hostname [lishalinux]: ").strip() or "lishalinux"

    # Root password
    root_password = getpass.getpass("Root password: ")
    root_confirm = getpass.getpass("Confirm root password: ")
    while root_password != root_confirm:
        print("Passwords do not match!")
        root_password = getpass.getpass("Root password: ")
        root_confirm = getpass.getpass("Confirm root password: ")

    username = input("Username: ").strip()
    user_password = getpass.getpass(f"Password for {username}: ")
    user_confirm = getpass.getpass(f"Confirm password for {username}: ")
    while user_password != user_confirm:
        print("Passwords do not match!")
        user_password = getpass.getpass(f"Password for {username}: ")
        user_confirm = getpass.getpass(f"Confirm password for {username}: ")

    return {
        "disk": disk,
        "hostname": hostname,
        "username": username,
        "user_password": user_password,
        "root_password": root_password,
        "sudo_access": True,
    }


def create_config(user):
    return {
        "app_config": {
            "audio_config": {"audio": "pipewire"},
            "bluetooth_config": {"enabled": True},
        },
        "archinstall-language": "English",
        "auth_config": {},
        "bootloader_config": {
            "bootloader": "Limine",
            "removable": True,
            "uki": False,
        },
        "custom_commands": [],
        
"disk_config": {
    "config_type": "default_layout",
    "btrfs_options": {
        "snapshot_config": {"type": "Snapper"}
    },
    "device_modifications": [
        {
            "device": user["disk"],
            "wipe": True,
            "partitions": [
                {
                    "fs_type": "fat32",
                    "mountpoint": "/boot",
                    "flags": ["boot", "esp"],
                    "status": "create",
                    "type": "primary",
                },
                {
                    "fs_type": "btrfs",
                    "mount_options": ["compress=zstd"],
                    "btrfs": [
                        {"name": "@", "mountpoint": "/"},
                        {"name": "@home", "mountpoint": "/home"},
                        {"name": "@log", "mountpoint": "/var/log"},
                        {"name": "@pkg", "mountpoint": "/var/cache/pacman/pkg"},
                    ],
                    "status": "create",
                    "type": "primary",
                },
            ],
        }
    ],
},
        "hostname": user["hostname"],
        "kernels": ["linux"],
        "locale_config": {
            "kb_layout": "us",
            "sys_enc": "UTF-8",
            "sys_lang": "en_US.UTF-8",
        },
        "mirror_config": {
            "mirror_regions": {
                "Worldwide": []
            },
            "custom_servers": [],
            "custom_repositories": [],
            "optional_repositories": [],
        },
        "network_config": {"type": "iso"},
        "ntp": True,
        "packages": [
            "git",
            "kitty",
            "gum",
        ],
        "parallel_downloads": 0,
        "profile_config": {
            "gfx_driver": "All open-source",
            "greeter": "sddm",
            "profile": {
                "main": "Desktop",
                "details": ["Hyprland"],
                "custom_settings": {
                    "Hyprland": {"seat_access": "polkit"}
                },
            },
        },
        "services": [],
        "swap": {
            "enabled": True,
            "algorithm": "zstd",
        },
        "timezone": "UTC",
        "version": "3.0.15",
    }


def create_creds(user):
    return {
        "!root-password": user["root_password"],
        "!users": [
            {
                "username": user["username"],
                "!password": user["user_password"],
                "sudo": user["sudo_access"],
            }
        ],
    }


def main():
    if os.geteuid() != 0:
        print("Run this installer as root.")
        sys.exit(1)

    user_data = get_user_input()

    config = create_config(user_data)
    creds = create_creds(user_data)

    config_path = Path("/tmp/lishalinux_config.json")
    creds_path = Path("/tmp/lishalinux_creds.json")

    config_path.write_text(json.dumps(config, indent=2))
    creds_path.write_text(json.dumps(creds, indent=2))

    print("\nStarting installation...\n")

    cmd = [
        "archinstall",
        "--config", str(config_path),
        "--creds", str(creds_path),
        "--silent",
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Installation complete! Reboot to start LishaLinux.")
    except subprocess.CalledProcessError as e:
        print("\n❌ Installation failed.")
        print("Check /var/log/archinstall/install.log")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()

