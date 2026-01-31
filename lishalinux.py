from archinstall import Profile, Installer
import subprocess
import os

class LishaLinux(Profile):
    name = "LishaLinux (Hyprland)"

    def install(self, installer: Installer):
        # ---- Desktop / WM ----
        installer.add_additional_packages([
            "hyprland",
            "sddm",
            "polkit",
            "pipewire",
            "pipewire-pulse",
            "wireplumber",
            "bluez",
            "bluez-utils",
            "git",
            "base-devel",
            "fzf"
        ])

        # ---- Services ----
        installer.enable_service("sddm")
        installer.enable_service("bluetooth")
        installer.enable_service("systemd-timesyncd")

        # ---- Post-install hook ----
        self._run_lishalinux_installer(installer)

    def _run_lishalinux_installer(self, installer: Installer):
        """
        This runs inside the installed system (chroot)
        """
        script = r"""
set -e

echo ">>> Installing LishaLinux user environment"

# Ensure network is up
systemctl enable NetworkManager

# Clone LishaLinux repo
git clone https://github.com/rawalrauf/lishalinux

cd lishalinux
chmod +x install.sh

# Run install script
./install.sh

"""

        installer.run_command(f"bash -c '{script}'")
