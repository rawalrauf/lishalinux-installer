#!/bin/bash
set -e

echo "=== LishaLinux Installer ==="
echo

curl -fsSL -o lishalinux_simple.py \
  https://raw.githubusercontent.com/rawalrauf/lishalinux-installer/main/lishalinux_simple.py

chmod +x lishalinux_simple.py

python3 lishalinux_simple.py </dev/tty
