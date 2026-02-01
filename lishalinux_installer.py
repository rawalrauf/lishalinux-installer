#!/usr/bin/env python3
"""
LishaLinux Installer - Arch-based distro installer using archinstall
Enforces fixed defaults while keeping essential options user-configurable
"""

import json
import sys
import subprocess
import os
from pathlib import Path

def create_config():
    """Create archinstall configuration with LishaLinux defaults"""
    
    # Get user inputs for required fields
    print("=== LishaLinux Installer ===")
    print("Setting up your LishaLinux system with optimized defaults...\n")
    
    # User-configurable options
    hostname = input("Hostname [lishalinux]: ").strip() or "lishalinux"
    
    print("\nAvailable disks:")
    try:
        result = subprocess.run(['lsblk', '-d', '-n', '-o', 'NAME,SIZE,TYPE'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except:
        print("Could not list disks. Please check manually with 'lsblk'")
    
    disk = input("Target disk (e.g., /dev/sda): ").strip()
    if not disk.startswith('/dev/'):
        disk = f"/dev/{disk}"
    
    # Timezone
    timezone = input("Timezone [UTC]: ").strip() or "UTC"
    
    # Root password
    import getpass
    root_password = getpass.getpass("Root password: ")
    
    # User creation
    username = input("Username: ").strip()
    user_password = getpass.getpass(f"Password for {username}: ")
    sudo_access = input(f"Give {username} sudo access? [Y/n]: ").strip().lower()
    sudo_access = sudo_access != 'n'
    
    # Create configuration
    config = {
        "archinstall-language": "English",
        "audio_config": {
            "audio": "pipewire"
        },
        "bootloader_config": {
            "bootloader": "Limine",
            "uki": False,
            "removable": True
        },
        "debug": False,
        "disk_config": {
            "config_type": "default_layout",
            "device_modifications": [
                {
                    "device": disk,
                    "partitions": [
                        {
                            "btrfs": [],
                            "flags": ["boot"],
                            "fs_type": "fat32",
                            "size": {"unit": "MiB", "value": 512},
                            "mount_options": [],
                            "mountpoint": "/boot",
                            "start": {"unit": "MiB", "value": 1},
                            "status": "create",
                            "type": "primary"
                        },
                        {
                            "btrfs": [
                                {"name": "@", "mountpoint": "/"},
                                {"name": "@home", "mountpoint": "/home"},
                                {"name": "@var", "mountpoint": "/var"},
                                {"name": "@tmp", "mountpoint": "/tmp"},
                                {"name": "@.snapshots", "mountpoint": "/.snapshots"}
                            ],
                            "flags": [],
                            "fs_type": "btrfs",
                            "size": {"unit": "Percent", "value": 100},
                            "mount_options": ["compress=zstd"],
                            "mountpoint": "/",
                            "start": {"unit": "MiB", "value": 513},
                            "status": "create",
                            "type": "primary"
                        }
                    ],
                    "wipe": True
                }
            ]
        },
        "hostname": hostname,
        "kernels": ["linux"],
        "locale_config": {
            "kb_layout": "us",
            "sys_enc": "UTF-8",
            "sys_lang": "en_US"
        },
        "mirror_config": {
            "mirror_regions": {
                "Worldwide": [],
                "United States": []
            }
        },
        "network_config": {
            "type": "copy_iso"
        },
        "ntp": True,
        "offline": False,
        "packages": ["base-devel", "git", "fzf", "snapper"],
        "profile_config": {
            "gfx_driver": "All open-source (default)",
            "greeter": "sddm",
            "profile": {
                "details": ["Hyprland"],
                "main": "Desktop"
            },
            "seat_access": "polkit"
        },
        "script": "guided",
        "silent": False,
        "swap": {
            "enabled": True
        },
        "timezone": timezone,
        "users": [
            {
                "username": username,
                "password": user_password,
                "sudo": sudo_access
            }
        ],
        "root_password": root_password,
        "version": "2.8.6"
    }
    
    return config

def create_post_install_hook():
    """Create post-installation script for LishaLinux setup"""
    
    post_install = """#!/bin/bash
# LishaLinux Post-Installation Hook
set -e

echo "=== LishaLinux Post-Installation Setup ==="

# Enable services
systemctl enable sddm
systemctl enable bluetooth
systemctl enable NetworkManager
systemctl enable systemd-timesyncd

# Setup Snapper for BTRFS snapshots
if mountpoint -q / && findmnt -n -o FSTYPE / | grep -q btrfs; then
    echo "Setting up Snapper for BTRFS snapshots..."
    snapper -c root create-config /
    systemctl enable snapper-timeline.timer
    systemctl enable snapper-cleanup.timer
fi

# Clone and run LishaLinux configuration
echo "Installing LishaLinux user environment..."
cd /tmp
git clone https://github.com/rawalrauf/lishalinux
cd lishalinux
chmod +x install.sh

# Run the install script
./install.sh

echo "=== LishaLinux installation completed! ==="
"""
    
    return post_install

def main():
    """Main installer function"""
    
    # Check if running as root
    if os.geteuid() != 0:
        print("This installer must be run as root (or with sudo)")
        sys.exit(1)
    
    # Create configuration
    config = create_config()
    
    # Write configuration file
    config_path = Path("/tmp/lishalinux_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create post-install hook
    post_install_script = create_post_install_hook()
    hook_path = Path("/tmp/lishalinux_post_install.sh")
    with open(hook_path, 'w') as f:
        f.write(post_install_script)
    hook_path.chmod(0o755)
    
    print(f"\nConfiguration saved to: {config_path}")
    print(f"Post-install hook saved to: {hook_path}")
    
    # Run archinstall with the configuration
    print("\nStarting archinstall with LishaLinux configuration...")
    try:
        subprocess.run([
            'archinstall',
            '--config', str(config_path),
            '--creds', '/dev/null',  # We handle credentials in config
            '--silent'
        ], check=True)
        
        print("\n=== Installation completed successfully! ===")
        print("Your LishaLinux system is ready. Please reboot.")
        
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
        sys.exit(1)

if __name__ == "__main__":
    import os
    main()
