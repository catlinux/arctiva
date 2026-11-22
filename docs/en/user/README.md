# Arctiva user guide

> Versión en castellano: [../../es/usuario/README.md](../../es/usuario/README.md)

Arctiva is a Linux distribution based on Arch Linux, with a Windows-style KDE Plasma desktop. This guide is for people who have never installed Linux.

**Status:** test version. There is no public ISO yet; when there is, it will be on the repository's *Releases* page, with its checksum and signature (see [releasing](../releasing.md)).

## 1. What you need

- A computer with **UEFI** (almost every one from the last 10 years; Arctiva does not boot in legacy BIOS mode).
- At least **4 GiB of RAM** and **25 GiB of free disk**.
- A USB stick of 4 GB or more (it is erased completely).
- An internet connection during installation (for what does not fit on the ISO, such as the LTS kernel or the Gaming and Office profiles). Without it, what the ISO carries is still installed.

## 2. Prepare the USB

Download the ISO and check it is authentic (see [releasing](../releasing.md)). Then use one of these:

- **Rufus** (Windows): pick the ISO, partition scheme **GPT** and target system **UEFI**.
- **balenaEtcher** (Windows, macOS, Linux): pick the ISO and the USB.
- **Ventoy** (Windows, Linux): copy the ISO to a USB already prepared with Ventoy. At its menu choose **"Boot in grub2 mode"**: the normal mode drops to an emergency shell and does not start Arctiva yet. If in doubt, use Rufus or Etcher.
- **dd** (Linux): `sudo dd if=arctiva-X.Y.Z-x86_64.iso of=/dev/sdX bs=4M status=progress oflag=sync` (careful: `/dev/sdX` is the USB, not your disk).

## 3. Before booting: Secure Boot and BitLocker

- **Secure Boot** (D-05): Arctiva does **not** boot with Secure Boot on. Enter the firmware settings (UEFI/BIOS; usually Del, F2 or F12 at power-on) and turn it off.
- **BitLocker (Windows):** if you will install **next to Windows** and Windows uses BitLocker (or "device encryption"), **have your recovery key at hand** (from your Microsoft account): Windows will ask for it after the boot settings change. Shrink the Windows partition from Windows' *Disk Management* and shut Windows down completely (*fast startup* leaves the disk in a state that prevents resizing it).
- **Back up** what matters. Installing always carries some risk.

## 4. Boot and install

1. Boot from the USB (firmware boot menu, usually F12 or F8) and choose "Arctiva (live)". If the screen looks wrong, try "safe graphics". Starting from a USB stick can take one to two minutes: wait for the desktop.
2. Try it without installing: it is a full live session. A welcome window opens with an **Install Arctiva** button, and the same icon is on the desktop. Nothing on your disk changes until you run the installer.
3. Follow the installer: language, time zone and keyboard; the **profile** (Basic, Gaming or Office; Ctrl+click to pick several); the **Check** page, which warns about hibernated Windows, BitLocker, battery and network; the **disk** (erase all, **install alongside another system** or replace a partition); and your user and password.
4. If you partition by hand, make the root **Btrfs**: snapshots (section 6) need it, and the installer does not warn you. On the disk page, **encrypting the system** is optional. If you turn it on, GRUB asks for the password **in text mode** at boot before showing anything else: this is normal.
5. Review the **summary** and press Install. When it finishes, restart and remove the USB.

## 5. First steps

The first time you log in you can open **Arctiva Center** (it is in the start menu). Its pages:

- **Personalization:** light or dark mode, colour, wallpaper, taskbar (centred or left, floating) and text size. "Restore the Arctiva look" puts it back as freshly installed.
- **Updates:** updates the system with one click, showing first the Arch news that need your attention. A snapshot is saved before every update.
- **Applications:** the store. Search programs from the Arch repositories and Flathub; the source is always visible. If updates are pending, it asks you to update first.
- **Drivers:** detects your graphics card and installs what is needed (NVIDIA included).
- **Extras:** Gaming (Steam, Lutris…), Office (LibreOffice, Thunderbird), LTS kernel, Windows programs (Bottles), Heroic and ProtonPlus.

## 6. Going back if something breaks (snapshots)

Before and after every installation or update, Arctiva saves a **snapshot** of the system (Btrfs). If something stops working:

1. Restart and, in the boot menu, choose **"Arctiva snapshots"**.
2. Pick a snapshot from before the problem. The system starts as it was; changes you make there are temporary.
3. At most 10 are kept.

## 7. Games

Install the **Gaming** extra (Steam with Proton, Lutris, GameMode, MangoHud, Gamescope). **Heroic** is for your Epic, GOG and Amazon games, and **ProtonPlus** manages Proton versions. Games with kernel-level anti-cheat usually do not work on Linux: see [Are We Anti-Cheat Yet?](https://areweanticheatyet.com/) and [ProtonDB](https://www.protondb.com/).

## 8. Windows programs

Install the **Windows programs** extra (Bottles). The first time it downloads a lot, because Flatpak also fetches its shared components: Arctiva Center warns you first and shows a progress bar, and the download can take from minutes to over half an hour; do not turn off or suspend the computer meanwhile. Then double-click a `.exe` or `.msi` and Arctiva explains what will happen and opens it with Bottles. Not everything works (check [WineHQ AppDB](https://appdb.winehq.org/)). Only open programs you trust.

## 9. The store and the AUR

In **Applications** you can install and remove programs from Arch and Flathub. The **AUR** (unreviewed community recipes) is **off**; if you turn it on, you must read the PKGBUILD before every installation. AUR updates are manual and show what changed.

## 10. FAQ

- **Is it still Arch?** Yes: it uses Arch's official repositories unchanged; pacman works as usual.
- **Does it work with Secure Boot?** No, turn it off.
- **And on an old BIOS machine?** No: UEFI only.
- **Where do I ask for help?** In the Arctiva repository's *Discussions* (not on the Arch forums: they do not support derivatives).
