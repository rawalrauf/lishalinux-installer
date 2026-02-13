# LishaLinux Installer

Arch-based distro installer using official Arch ISO + archinstall. Provides a fast, reproducible installation with Hyprland desktop environment and optimized defaults.

## Usage

### From Arch ISO

1. Boot Arch ISO and connect to internet
2. Download and run installer using given below command:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/rawalrauf/lishalinux-installer/main/install.sh)
```

### Manual Installation

1. Download the installer:
```bash
git clone https://github.com/rawalrauf/lishalinux-installer
cd lishalinux-installer
```

2. Run as root:
```bash
python3 lishalinux.py
```

## Files

- `lishalinux.py` - Main install script
- `lishalinux-chroot.sh` - lishalinux chroot setup script
- `install.sh` - Main installer that uses install script

## Requirements

- Internet connection
- UEFI system (recommended)
- At least 10GB disk space

