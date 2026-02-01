# LishaLinux Installer

Arch-based distro installer using official Arch ISO + archinstall. Provides a fast, reproducible installation with Hyprland desktop environment and optimized defaults.

## Features

### Fixed Defaults (No User Prompts)
- **Language**: English
- **Locale/Keyboard**: archinstall defaults (US)
- **Mirrors**: Worldwide + United States
- **Filesystem**: BTRFS with compression (zstd)
- **Subvolumes**: @, @home, @var, @tmp, @.snapshots
- **Snapshots**: Snapper (not Timeshift)
- **Swap**: Enabled (default size)
- **Bootloader**: Limine (removable location enabled)
- **Kernel**: linux
- **Desktop**: Hyprland
- **Display Manager**: SDDM
- **Graphics**: Auto-detected open-source drivers
- **Audio**: PipeWire
- **Bluetooth**: Enabled
- **Network**: Copy ISO configuration
- **Packages**: base-devel, git, fzf, snapper, hyprland, sddm, pipewire, bluez
- **NTP**: Enabled

### User-Configurable Options
- Disk selection
- Hostname
- Root password
- User creation (username, password, sudo access)
- Timezone

### Post-Installation
- Automatically clones https://github.com/rawalrauf/lishalinux
- Executes ./install.sh for Hyprland configs, AUR packages, theming
- Enables all required services
- Sets up Snapper snapshots

## Usage

### From Arch ISO

1. Boot Arch ISO and connect to internet
2. Download and run installer:

```bash
curl -L https://raw.githubusercontent.com/rawalrauf/lishalinux-installer/main/install.sh | bash
```

### Manual Installation

1. Download the installer:
```bash
git clone https://github.com/rawalrauf/lishalinux-installer
cd lishalinux-installer
```

2. Run as root:
```bash
sudo python3 lishalinux_simple.py
```

## Files

- `lishalinux_simple.py` - Main installer (recommended)
- `lishalinux_installer.py` - Alternative implementation
- `install.sh` - Wrapper script for easy ISO usage

## Requirements

- Arch Linux ISO (2024.01.01 or newer)
- Internet connection
- UEFI system (recommended)
- At least 20GB disk space

## Architecture

The installer generates archinstall configuration files with LishaLinux defaults, then runs the standard archinstall process. After base installation, it automatically applies LishaLinux customizations.

This approach avoids maintaining custom ISOs or offline packages while providing a distro-like experience.
