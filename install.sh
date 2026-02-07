#!/bin/bash
# LishaLinux Installer Wrapper
# This script should be run from the Arch ISO

set -Eeuo pipefail

echo "=== LishaLinux Installer ==="
echo "Arch-based distro with Hyprland and optimized defaults"
echo

# -----------------------------------------
# Sanity checks
# -----------------------------------------

if ! command -v archinstall &>/dev/null; then
  echo "❌ archinstall not found. Run this from an Arch Linux ISO."
  exit 1
fi

if ! ping -c 1 archlinux.org &>/dev/null; then
  echo "❌ No internet connection."
  echo "Use: iwctl (WiFi) or dhcpcd (Ethernet)"
  exit 1
fi

timedatectl set-ntp true

# -----------------------------------------
# Download installer components
# -----------------------------------------

BASE_URL="https://raw.githubusercontent.com/rawalrauf/lishalinux-installer/main"

download() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "Downloading $file..."
    curl -fsSL -o "$file" "$BASE_URL/$file"
    chmod +x "$file"
  fi
}

download lishalinux_simple.py
download lishalinux-chroot-stage.sh

# -----------------------------------------
# Export path to chroot-stage script
# -----------------------------------------
# Python will copy this into the target system

export LISHALINUX_CHROOT_STAGE="$(pwd)/lishalinux-chroot-stage.sh"

# -----------------------------------------
# Run installer (interactive)
# -----------------------------------------

python3 lishalinux_simple.py </dev/tty
