#!/bin/bash
# LishaLinux Installer Wrapper
# This script should be run from the Arch ISO

set -e

echo "=== LishaLinux Installer ==="
echo "Arch-based distro with Hyprland and optimized defaults"
echo

# Check if we're on Arch ISO
if ! command -v archinstall &> /dev/null; then
    echo "Error: archinstall not found. Please run this from an Arch Linux ISO."
    exit 1
fi

# Check internet connection
if ! ping -c 1 archlinux.org &> /dev/null; then
    echo "Error: No internet connection. Please configure network first."
    echo "You can use: iwctl (for WiFi) or dhcpcd (for Ethernet)"
    exit 1
fi

# Update system clock
timedatectl set-ntp true

# Download the installer if not present
if [ ! -f "lishalinux_simple.py" ]; then
    echo "Downloading LishaLinux installer..."
    curl -L -o lishalinux_simple.py https://raw.githubusercontent.com/rawalrauf/lishalinux-installer/main/lishalinux_simple.py
    chmod +x lishalinux_simple.py
fi

# Run the Python installer
python3 lishalinux_simple.py
