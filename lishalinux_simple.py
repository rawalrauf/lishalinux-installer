
#!/usr/bin/env python3
"""
LishaLinux Installer - Simple archinstall configuration generator
"""

import json
import sys
import os
import subprocess
import getpass
import shutil
from pathlib import Path

# -------------------------------------------------
# Utilities
# -------------------------------------------------

def get_disk_size(disk_path):
    """Get disk size in bytes"""
    try:
        result = subprocess.run(
            ['lsblk', '-b', '-d', '-n', '-o', 'SIZE', disk_path],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except Exception:
        # Fallback to 20GB if we can't detect
        return 20 * 1024 * 1024 * 1024


# -------------------------------------------------
# User input
# -------------------------------------------------

def get_user_input():
    """Get required user inputs"""
    print("=== LishaLinux Installer ===")
    print("Arch-based distro with Hyprland and optimized defaults\n")

    # Show available disks
    print("Available disks:")
    try:
        result = subprocess.run(
            ['lsblk', '-d', '-n', '-o', 'NAME,SIZE,TYPE'],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except Exception:
        print("Could not list disks")

    disk = input("Target disk (e.g., sda): ").strip()
    if not disk.startswith('/dev/'):
        disk = f"/dev/{disk}"

    hostname = input("Hostname [lishalinux]: ").strip() or "lishalinux"

    # Root password
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
        "disk": disk,
        "hostname": hostname,
        "username": username,
        "user_password": user_password,
        "root_password": root_password,
        "sudo_access": True,
    }


# -------------------------------------------------
# Archinstall config
# -------------------------------------------------

def create_config(user_data):
    """Create archinstall configuration"""

    disk_size = get_disk_size(user_data["disk"])

    mb = 1024 * 1024
    boot_start = 1 * mb
    boot_size = 1024 * mb
    root_start = boot_start + boot_size

    usable_space = disk_size - (34 * 512 * 2)
    root_size = usable_space - root_start
    root_size = (root_size // mb) * mb

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

        # 🔑 IMPORTANT PART
        "custom_commands": [
            "install -Dm755 /tmp/lishalinux-chroot-stage.sh "
            "/usr/local/bin/lishalinux-chroot-stage",
            f"/usr/local/bin/lishalinux-chroot-stage {user_data['username']}",
        ],

        "disk_config": {
            "btrfs_options": {
                "snapshot_config": {"type": "Snapper"}
            },
            "config_type": "default_layout",
            "device_modifications": [
                {
                    "device": user_data["disk"],
                    "wipe": True,
                    "partitions": [
                        {
                            "fs_type": "fat32",
                            "mountpoint": "/boot",
                            "flags": ["boot", "esp"],
                            "size": {"unit": "GiB", "value": 1},
                            "start": {"unit": "MiB", "value": 1},
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
                            "size": {"unit": "B", "value": root_size},
                            "start": {"unit": "B", "value": root_start},
                            "status": "create",
                            "type": "primary",
                        },
                    ],
                }
            ],
        },
        "hostname": user_data["hostname"],
        "kernels": ["linux"],
        "locale_config": {
            "kb_layout": "us",
            "sys_enc": "UTF-8",
            "sys_lang": "en_US.UTF-8",
        },
        "mirror_config": {
            "mirror_regions": {"Worldwide": []}
        },
        "network_config": {"type": "iso"},
        "ntp": True,
        "packages": ["git", "kitty", "gum"],
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
        "swap": {"enabled": True, "algorithm": "zstd"},
        "timezone": "UTC",
        "version": "3.0.15",
    }


def create_creds(user_data):
    """Create credentials file"""
    return {
        "!root-password": user_data["root_password"],
        "!users": [
            {
                "username": user_data["username"],
                "!password": user_data["user_password"],
                "sudo": user_data["sudo_access"],
            }
        ],
    }


# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    DIRECT_INSTALL = True

    if os.geteuid() != 0:
        print("Run as root")
        sys.exit(1)

    # Validate chroot-stage script from installer wrapper
    chroot_stage_src = os.environ.get("LISHALINUX_CHROOT_STAGE")
    if not chroot_stage_src:
        print("❌ LISHALINUX_CHROOT_STAGE not set")
        sys.exit(1)

    chroot_stage_src = Path(chroot_stage_src)
    if not chroot_stage_src.exists():
        print(f"❌ Chroot stage script not found: {chroot_stage_src}")
        sys.exit(1)

    # Copy into /tmp for archinstall
    chroot_stage_dst = Path("/tmp/lishalinux-chroot-stage.sh")
    shutil.copy(chroot_stage_src, chroot_stage_dst)
    chroot_stage_dst.chmod(0o755)

    # Collect user input
    user_data = get_user_input()

    # Generate config + creds
    config = create_config(user_data)
    creds = create_creds(user_data)

    config_file = Path("/tmp/lishalinux_config.json")
    creds_file = Path("/tmp/lishalinux_creds.json")

    config_file.write_text(json.dumps(config, indent=2))
    creds_file.write_text(json.dumps(creds, indent=2))

    print("\nFiles created:")
    print(f"Config: {config_file}")
    print(f"Creds:  {creds_file}")

    print("\nStarting installation...")

    cmd = ["archinstall", "--config", str(config_file), "--creds", str(creds_file)]
    if DIRECT_INSTALL:
        cmd.append("--silent")

    try:
        subprocess.run(cmd, check=True)
        print("\n=== Installation complete! ===")
        print("Reboot to start LishaLinux")
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

