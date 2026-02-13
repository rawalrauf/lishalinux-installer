#!/bin/bash
set -e

echo "=== LishaLinux Installer ==="
echo

curl -fsSL -o lishalinux.py \
  https://raw.githubusercontent.com/rawalrauf/lishalinux-installer/main/lishalinux.py

chmod +x lishalinux.py

python3 lishalinux.py </dev/tty
