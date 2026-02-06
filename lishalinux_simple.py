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

def get_disk_size(disk_path):
    """Get disk size in bytes"""
    try:
        result = subprocess.run(['lsblk', '-b', '-d', '-n', '-o', 'SIZE', disk_path], 
                              capture_output=True, text=True)
        return int(result.stdout.strip())
    except:
        # Fallback to 20GB if we can't detect
        return 20 * 1024 * 1024 * 1024

def get_user_input():
    """Get required user inputs"""
    print("=== LishaLinux Installer ===")
    print("Arch-based distro with Hyprland and optimized defaults\n")
    
    # Show available disks
    print("Available disks:")
    try:
        result = subprocess.run(['lsblk', '-d', '-n', '-o', 'NAME,SIZE,TYPE'], 
                              capture_output=True, text=True)
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
        'sudo_access': True
    }

def create_config(user_data):
    """Create archinstall configuration"""
    
    # Calculate aligned partition sizes
    disk_size = get_disk_size(user_data['disk'])
    
    # Align to 1MB boundaries (standard practice)
    mb = 1024 * 1024
    boot_start = 1 * mb  # 1MB
    boot_size = 1024 * mb  # 1GB
    root_start = boot_start + boot_size  # 1025MB
    
    # Calculate root size with proper alignment
    usable_space = disk_size - (34 * 512 * 2)  # Subtract GPT headers
    root_size = usable_space - root_start
    root_size = (root_size // mb) * mb  # Align to MB boundary
    
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
            USERNAME=$(ls /home | head -n1)
HOME_DIR=/home/$USERNAME

echo "=== LishaLinux chroot staging ==="

# -------------------------------------------------
# 1. TEMP passwordless sudo (removed on first boot)
# -------------------------------------------------
echo "Setting temp passwordless sudo..."
echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/temp-lishalinux-setup
chmod 440 /etc/sudoers.d/temp-lishalinux-setup

# -------------------------------------------------
# 2. Autologin via getty (disable SDDM)
# -------------------------------------------------
echo "Configuring getty autologin..."
systemctl disable sddm || true

mkdir -p /etc/systemd/system/getty@tty1.service.d
cat >/etc/systemd/system/getty@tty1.service.d/autologin.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty -a $USERNAME --noclear %I \$TERM
Environment=XDG_SESSION_TYPE=wayland
EOF

# -------------------------------------------------
# 3. Staging directory (NOT ~/.config)
# -------------------------------------------------
echo "Creating staging directory..."
mkdir -p "$HOME_DIR/lishalinux-setup"
chown -R $USERNAME:$USERNAME "$HOME_DIR/lishalinux-setup"

# -------------------------------------------------
# 4. DROP FIRST-BOOT SCRIPT (RUNS AFTER REAL BOOT)
# -------------------------------------------------
cat >"$HOME_DIR/lishalinux-setup/first-boot.sh" <<'EOF'
#!/bin/bash
# LishaLinux First Boot — Hyprland-based (NO systemd user services)

set -e

# Prevent re-run
[ -f "$HOME/.lishalinux-installed" ] && exit 0

# -------------------------------------------------
# Wait for Wayland
# -------------------------------------------------
while [ -z "$WAYLAND_DISPLAY" ]; do
    sleep 1
done

# -------------------------------------------------
# Hyprland config edits (clean screen FIRST)
# -------------------------------------------------
mkdir -p "$HOME/.config/hypr"

cat >>"$HOME/.config/hypr/hyprland.conf" <<'HYPR'

# This is an example Hyprland config file.
# Refer to the wiki for more information.
# https://wiki.hypr.land/Configuring/

# Please note not all available settings / options are set here.
# For a full list, see the wiki

# You can split this configuration into multiple files
# Create your files separately and then link them to this file like this:
# source = ~/.config/hypr/myColors.conf


################
### MONITORS ###
################

# See https://wiki.hypr.land/Configuring/Monitors/
monitor=,preferred,auto,auto


###################
### MY PROGRAMS ###
###################

# See https://wiki.hypr.land/Configuring/Keywords/

# Set programs that you use
$terminal = kitty
$fileManager = dolphin
$menu = hyprlauncher


#################
### AUTOSTART ###
#################

# Autostart necessary processes (like notifications daemons, status bars, etc.)
# Or execute your favorite apps at launch like this:

# exec-once = $terminal
# exec-once = nm-applet &
# exec-once = waybar & hyprpaper & firefox


#############################
### ENVIRONMENT VARIABLES ###
#############################

# See https://wiki.hypr.land/Configuring/Environment-variables/

env = XCURSOR_SIZE,24
env = HYPRCURSOR_SIZE,24


###################
### PERMISSIONS ###
###################

# See https://wiki.hypr.land/Configuring/Permissions/
# Please note permission changes here require a Hyprland restart and are not applied on-the-fly
# for security reasons

# ecosystem {
#   enforce_permissions = 1
# }

# permission = /usr/(bin|local/bin)/grim, screencopy, allow
# permission = /usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland, screencopy, allow
# permission = /usr/(bin|local/bin)/hyprpm, plugin, allow


#####################
### LOOK AND FEEL ###
#####################

# Refer to https://wiki.hypr.land/Configuring/Variables/

# https://wiki.hypr.land/Configuring/Variables/#general
general {
    gaps_in = 5
    gaps_out = 20

    border_size = 2

    # https://wiki.hypr.land/Configuring/Variables/#variable-types for info about colors
    col.active_border = rgba(33ccffee) rgba(00ff99ee) 45deg
    col.inactive_border = rgba(595959aa)

    # Set to true enable resizing windows by clicking and dragging on borders and gaps
    resize_on_border = false

    # Please see https://wiki.hypr.land/Configuring/Tearing/ before you turn this on
    allow_tearing = false

    layout = dwindle
}

# https://wiki.hypr.land/Configuring/Variables/#decoration
decoration {
    rounding = 10
    rounding_power = 2

    # Change transparency of focused and unfocused windows
    active_opacity = 1.0
    inactive_opacity = 1.0

    shadow {
        enabled = true
        range = 4
        render_power = 3
        color = rgba(1a1a1aee)
    }

    # https://wiki.hypr.land/Configuring/Variables/#blur
    blur {
        enabled = true
        size = 3
        passes = 1

        vibrancy = 0.1696
    }
}

# https://wiki.hypr.land/Configuring/Variables/#animations
animations {
    enabled = yes, please :)

    # Default curves, see https://wiki.hypr.land/Configuring/Animations/#curves
    #        NAME,           X0,   Y0,   X1,   Y1
    bezier = easeOutQuint,   0.23, 1,    0.32, 1
    bezier = easeInOutCubic, 0.65, 0.05, 0.36, 1
    bezier = linear,         0,    0,    1,    1
    bezier = almostLinear,   0.5,  0.5,  0.75, 1
    bezier = quick,          0.15, 0,    0.1,  1

    # Default animations, see https://wiki.hypr.land/Configuring/Animations/
    #           NAME,          ONOFF, SPEED, CURVE,        [STYLE]
    animation = global,        1,     10,    default
    animation = border,        1,     5.39,  easeOutQuint
    animation = windows,       1,     4.79,  easeOutQuint
    animation = windowsIn,     1,     4.1,   easeOutQuint, popin 87%
    animation = windowsOut,    1,     1.49,  linear,       popin 87%
    animation = fadeIn,        1,     1.73,  almostLinear
    animation = fadeOut,       1,     1.46,  almostLinear
    animation = fade,          1,     3.03,  quick
    animation = layers,        1,     3.81,  easeOutQuint
    animation = layersIn,      1,     4,     easeOutQuint, fade
    animation = layersOut,     1,     1.5,   linear,       fade
    animation = fadeLayersIn,  1,     1.79,  almostLinear
    animation = fadeLayersOut, 1,     1.39,  almostLinear
    animation = workspaces,    1,     1.94,  almostLinear, fade
    animation = workspacesIn,  1,     1.21,  almostLinear, fade
    animation = workspacesOut, 1,     1.94,  almostLinear, fade
    animation = zoomFactor,    1,     7,     quick
}

# Ref https://wiki.hypr.land/Configuring/Workspace-Rules/
# "Smart gaps" / "No gaps when only"
# uncomment all if you wish to use that.
# workspace = w[tv1], gapsout:0, gapsin:0
# workspace = f[1], gapsout:0, gapsin:0
# windowrule {
#     name = no-gaps-wtv1
#     match:float = false
#     match:workspace = w[tv1]
#
#     border_size = 0
#     rounding = 0
# }
#
# windowrule {
#     name = no-gaps-f1
#     match:float = false
#     match:workspace = f[1]
#
#     border_size = 0
#     rounding = 0
# }

# See https://wiki.hypr.land/Configuring/Dwindle-Layout/ for more
dwindle {
    pseudotile = true # Master switch for pseudotiling. Enabling is bound to mainMod + P in the keybinds section below
    preserve_split = true # You probably want this
}

# See https://wiki.hypr.land/Configuring/Master-Layout/ for more
master {
    new_status = master
}

# https://wiki.hypr.land/Configuring/Variables/#misc
misc {
    force_default_wallpaper = -1 # Set to 0 or 1 to disable the anime mascot wallpapers
    disable_hyprland_logo = false # If true disables the random hyprland logo / anime girl background. :(
}


#############
### INPUT ###
#############

# https://wiki.hypr.land/Configuring/Variables/#input
input {
    kb_layout = us
    kb_variant =
    kb_model =
    kb_options =
    kb_rules =

    follow_mouse = 1

    sensitivity = 0 # -1.0 - 1.0, 0 means no modification.

    touchpad {
        natural_scroll = false
    }
}

# See https://wiki.hypr.land/Configuring/Gestures
gesture = 3, horizontal, workspace

# Example per-device config
# See https://wiki.hypr.land/Configuring/Keywords/#per-device-input-configs for more
device {
    name = epic-mouse-v1
    sensitivity = -0.5
}


###################
### KEYBINDINGS ###
###################

# See https://wiki.hypr.land/Configuring/Keywords/
$mainMod = SUPER # Sets "Windows" key as main modifier

# Example binds, see https://wiki.hypr.land/Configuring/Binds/ for more
bind = $mainMod, Q, exec, $terminal
bind = $mainMod, C, killactive,
bind = $mainMod, M, exec, command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch exit
bind = $mainMod, E, exec, $fileManager
bind = $mainMod, V, togglefloating,
bind = $mainMod, R, exec, $menu
bind = $mainMod, P, pseudo, # dwindle
bind = $mainMod, J, togglesplit, # dwindle

# Move focus with mainMod + arrow keys
bind = $mainMod, left, movefocus, l
bind = $mainMod, right, movefocus, r
bind = $mainMod, up, movefocus, u
bind = $mainMod, down, movefocus, d

# Switch workspaces with mainMod + [0-9]
bind = $mainMod, 1, workspace, 1
bind = $mainMod, 2, workspace, 2
bind = $mainMod, 3, workspace, 3
bind = $mainMod, 4, workspace, 4
bind = $mainMod, 5, workspace, 5
bind = $mainMod, 6, workspace, 6
bind = $mainMod, 7, workspace, 7
bind = $mainMod, 8, workspace, 8
bind = $mainMod, 9, workspace, 9
bind = $mainMod, 0, workspace, 10

# Move active window to a workspace with mainMod + SHIFT + [0-9]
bind = $mainMod SHIFT, 1, movetoworkspace, 1
bind = $mainMod SHIFT, 2, movetoworkspace, 2
bind = $mainMod SHIFT, 3, movetoworkspace, 3
bind = $mainMod SHIFT, 4, movetoworkspace, 4
bind = $mainMod SHIFT, 5, movetoworkspace, 5
bind = $mainMod SHIFT, 6, movetoworkspace, 6
bind = $mainMod SHIFT, 7, movetoworkspace, 7
bind = $mainMod SHIFT, 8, movetoworkspace, 8
bind = $mainMod SHIFT, 9, movetoworkspace, 9
bind = $mainMod SHIFT, 0, movetoworkspace, 10

# Example special workspace (scratchpad)
bind = $mainMod, S, togglespecialworkspace, magic
bind = $mainMod SHIFT, S, movetoworkspace, special:magic

# Scroll through existing workspaces with mainMod + scroll
bind = $mainMod, mouse_down, workspace, e+1
bind = $mainMod, mouse_up, workspace, e-1

# Move/resize windows with mainMod + LMB/RMB and dragging
bindm = $mainMod, mouse:272, movewindow
bindm = $mainMod, mouse:273, resizewindow

# Laptop multimedia keys for volume and LCD brightness
bindel = ,XF86AudioRaiseVolume, exec, wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+
bindel = ,XF86AudioLowerVolume, exec, wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
bindel = ,XF86AudioMute, exec, wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
bindel = ,XF86AudioMicMute, exec, wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle
bindel = ,XF86MonBrightnessUp, exec, brightnessctl -e4 -n2 set 5%+
bindel = ,XF86MonBrightnessDown, exec, brightnessctl -e4 -n2 set 5%-

# Requires playerctl
bindl = , XF86AudioNext, exec, playerctl next
bindl = , XF86AudioPause, exec, playerctl play-pause
bindl = , XF86AudioPlay, exec, playerctl play-pause
bindl = , XF86AudioPrev, exec, playerctl previous

##############################
### WINDOWS AND WORKSPACES ###
##############################

# See https://wiki.hypr.land/Configuring/Window-Rules/ for more
# See https://wiki.hypr.land/Configuring/Workspace-Rules/ for workspace rules

# Example windowrules that are useful

windowrule {
    # Ignore maximize requests from all apps. You'll probably like this.
    name = suppress-maximize-events
    match:class = .*

    suppress_event = maximize
}

windowrule {
    # Fix some dragging issues with XWayland
    name = fix-xwayland-drags
    match:class = ^$
    match:title = ^$
    match:xwayland = true
    match:float = true
    match:fullscreen = false
    match:pin = false

    no_focus = true
}

# Hyprland-run windowrule
windowrule {
    name = move-hyprland-run

    match:class = hyprland-run

    move = 20 monitor_h-120
    float = yes
}

# ---- LishaLinux First Boot ----
autogenerated = 0
misc {
    force_default_wallpaper = 0
    disable_hyprland_logo = true
    disable_watchdog_warning = true
}

windowrule = float on, match:tag floating-window
windowrule = center on, match:tag floating-window
windowrule = size 875 600, match:tag floating-window
windowrule = tag +floating-window, match:class org.lishalinux.terminal
# --------------------------------
HYPR

# -------------------------------------------------
# Launch installer terminal
# -------------------------------------------------
kitty \
  --config NONE \
  --override font_family="CaskaydiaMono Nerd Font" \
  --override font_size=10.0 \
  --override foreground=#cdd6f4 \
  --override background=#1e1e2e \
  --override color2=#a6e3a1 \
  --override color10=#a6e3a1 \
  --override selection_foreground=#1e1e2e \
  --override selection_background=#89b4fa \
  --override window_padding_width=15 \
  --app-id=org.lishalinux.terminal \
  --title="Lishalinux" \
  -e bash -c '
clear

printf "\033[32m%s\033[0m\n\n" "
 ▄█             ▄█          ▄████████         ▄█    █▄            ▄████████ 
███            ███         ███    ███        ███    ███          ███    ███ 
███            ███▌        ███    █▀         ███    ███          ███    ███ 
███            ███▌        ███              ▄███▄▄▄▄███▄▄        ███    ███ 
███            ███▌      ▀███████████      ▀▀███▀▀▀▀███▀       ▀███████████ 
███            ███                ███        ███    ███          ███    ███ 
███▌    ▄      ███          ▄█    ███        ███    ███          ███    ███ 
█████▄▄██      █▀         ▄████████▀         ███    █▀           ███    █▀  
"

rows=$(tput lines)
printf "\e[11;${rows}r"
printf "\e[11;1H"

rm -rf "$HOME/lishalinux"
git clone https://github.com/rawalrauf/lishalinux
chmod +x lishalinux/install.sh
./lishalinux/install.sh

printf "\e[r"
printf "\e[999;1H"
echo ""

gum spin --spinner globe --title "Done! Press any key to close..." -- bash -c "read -n 1 -s"
'

# -------------------------------------------------
# CLEANUP (runs AFTER installer finishes)
# -------------------------------------------------

touch "$HOME/.lishalinux-installed"

rm -f "$HOME/.lishalinux-autostart"

sudo systemctl enable sddm
sudo rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
sudo rmdir /etc/systemd/system/getty@tty1.service.d 2>/dev/null || true

sudo rm -f /etc/sudoers.d/temp-lishalinux-setup

sleep 3
reboot
EOF

chmod +x "$HOME_DIR/lishalinux-setup/first-boot.sh"
chown $USERNAME:$USERNAME "$HOME_DIR/lishalinux-setup/first-boot.sh"

# -------------------------------------------------
# 5. Hyprland autostart hook (TTY → Hyprland)
# -------------------------------------------------
cat >"$HOME_DIR/.lishalinux-autostart" <<'EOF'
if [ -z "$WAYLAND_DISPLAY" ] && [ "$XDG_VTNR" -eq 1 ]; then
    exec Hyprland
fi
EOF

chown $USERNAME:$USERNAME "$HOME_DIR/.lishalinux-autostart"

# -------------------------------------------------
# 6. Ensure hook is sourced
# -------------------------------------------------
grep -q lishalinux-autostart "$HOME_DIR/.bash_profile" 2>/dev/null ||
  echo '[ -f ~/.lishalinux-autostart ] && source ~/.lishalinux-autostart' \
    >>"$HOME_DIR/.bash_profile"

# -------------------------------------------------
# 7. Hook first boot into Hyprland exec-once
# -------------------------------------------------
mkdir -p "$HOME_DIR/.config/hypr"
touch "$HOME_DIR/.config/hypr/hyprland.conf"

grep -q first-boot.sh "$HOME_DIR/.config/hypr/hyprland.conf" ||
  echo "exec-once = $HOME_DIR/lishalinux-setup/first-boot.sh" \
    >>"$HOME_DIR/.config/hypr/hyprland.conf"

chown -R $USERNAME:$USERNAME "$HOME_DIR/.config"

echo "=== chroot staging complete ==="
echo "Exit chroot and reboot"
        ],
        "disk_config": {
            "btrfs_options": {
                "snapshot_config": {
                    "type": "Snapper"
                }
            },
            "config_type": "default_layout",
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
                "Worldwide": []
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
            "gum"
        ],
        "parallel_downloads": 0,
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
                "sudo": user_data['sudo_access']
            }
        ]
    }

def create_post_install():
    """Create post-installation script"""
    return '''#!/bin/bash
# This script is no longer used - custom_commands handles LishaLinux setup
echo "LishaLinux setup handled by custom_commands"
'''

def main():
    # Backend configuration - set to True for direct install, False for TUI
    DIRECT_INSTALL = True  # Back to silent mode
    
    if os.geteuid() != 0:
        print("Run as root")
        sys.exit(1)
    
    # Get user input
    user_data = get_user_input()
    
    # Create files
    config = create_config(user_data)
    creds = create_creds(user_data)
    post_install = create_post_install()
    
    # Write files
    config_file = Path("/tmp/lishalinux_config.json")
    creds_file = Path("/tmp/lishalinux_creds.json")
    post_file = Path("/tmp/lishalinux_post.sh")
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    with open(creds_file, 'w') as f:
        json.dump(creds, f, indent=2)
    
    with open(post_file, 'w') as f:
        f.write(post_install)
    post_file.chmod(0o755)
    
    print(f"\nFiles created:")
    print(f"Config: {config_file}")
    print(f"Creds: {creds_file}")
    print(f"Post-install: {post_file}")
    
    # Run archinstall
    print("\nStarting installation...")
    try:
        cmd = [
            'archinstall',
            '--config', str(config_file),
            '--creds', str(creds_file)
        ]
        
        # Add --silent flag based on backend configuration
        if DIRECT_INSTALL:
            cmd.append('--silent')
            
        subprocess.run(cmd, check=True)
        
        print("\n=== Installation complete! ===")
        print("Reboot to start LishaLinux")
        
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
