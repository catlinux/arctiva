# Real-hardware testing

> Versión en castellano: [../es/pruebas.md](../es/pruebas.md)

Test matrix run on physical machines before releasing a version. One box per case; when ticking it, note the date and the version. Every failure is opened as a GitHub issue and linked here.

**Before starting:** verified ISO (`sha256sum -c`), a USB written with a tool that makes it GPT/UEFI, **Secure Boot off** (D-05) and a backup.

## 1. Laptop (Windows + Manjaro, Manjaro to be replaced keeping Windows)

### 1.1 Boot without installing (first test, no risk)

- [ ] Boots from the USB and reaches the desktop (note whether "safe graphics" was needed).
- [ ] The wallpaper, the centred taskbar and the start menu with search show up.
- [ ] Wi-Fi: lists networks and connects. Bluetooth: appears and pairs.
- [ ] Audio: plays through speakers and headphones.
- [ ] Keyboard, touchpad, brightness and function keys.
- [ ] Hybrid graphics: note which GPU the desktop uses.
- [ ] Arctiva Center → Drivers: detects the graphics card.

### 1.2 Checks before installing

- [ ] Is BitLocker on in Windows? (Disk Management or `manage-bde -status`). If so, **have the recovery key**.
- [ ] Windows fully shut down (not hibernated, fast startup off).
- [ ] The installer's "Check" page shows what you expect.

### 1.3 Installation (only after the above)

- [ ] "Replace a partition" on the Manjaro one, keeping Windows and the shared EFI partition.
- [ ] The installer finishes without errors.
- [ ] Arctiva boots; the GRUB menu shows the theme and **Windows** in the list.
- [ ] Windows boots from GRUB (and asks for the BitLocker key only if it was on).
- [ ] Old `EFI/Manjaro` entry: decide whether to warn or clean it with `efibootmgr` (with your approval).
- [ ] Wi-Fi, Bluetooth, battery, suspend and resume, lid, brightness.
- [ ] Hybrid graphics (`switcheroo-control`): an application on the dedicated GPU.

### 1.4 Encryption (if tested)

- [ ] Time from typing the password in GRUB to the login screen: ____ s (acceptable up to about 15 s; in QEMU with KVM it is about 30 s).

### 1.5 A week of use

- [ ] Updates from Arctiva Center (with news and sensitive packages).
- [ ] Boot a snapshot from GRUB and return to the normal state.

## 2. Desktop PC (i5-14400F, RTX 4060)

- [ ] Live USB: boot, "safe graphics", Wayland, network and audio.
- [ ] Installation on a free disk or external USB: the installer sets up the NVIDIA driver.
- [ ] Early KMS (no flicker), external monitor, suspend and resume.
- [ ] Steam with a Proton game, Heroic, MangoHud.

## 3. 0.7.x checks done in a virtual machine (QEMU/UEFI)

- [x] Unencrypted and encrypted installation; boot, themed GRUB, Plymouth, login, desktop.
- [x] Store: search, install and remove from Arch and Flathub; AUR with review; `.exe` dialog.
- [ ] Vendor logo (BGRT) under Plymouth: only visible on real hardware.

## Recorded results

Real-hardware tests, as reported by whoever ran them. Each line has a date and a version; what is not here has not been checked.

- **2026-11-22, ISO 0.7.4, MSI laptop (NVIDIA, Windows 11):**
  - Live boot from a Ventoy USB stick: only works with "Boot in grub2 mode" (the normal mode drops to an emergency shell); 1 min 53 s to the desktop (`systemd-analyze`: firmware 7.5 s, loader 32.3 s, kernel 48.6 s, userspace 24.7 s). See the TODO.
  - Installation **alongside Windows 11**: no problems, according to the user.
  - NVIDIA graphics: games load and run on the dedicated GPU (Battle.net and World of Warcraft, installed with Lutris).
  - In the live session the tray showed audio, Bluetooth, wifi and battery (42 %, charging).
- **2026-11-23, ISO 0.8.0, MSI laptop (NVIDIA, Windows 11), Arctiva on a partition of the same NVMe disk as Windows and the 100 MB Windows ESP:**
  - The installer failed on its last step: `grub-install` could not create `/boot/efi/EFI/arctiva` (the ESP had 64 MB free, it was not full). `fsck.vfat` showed a corrupt directory entry for that folder and the dirty bit set, and the kernel mounted the ESP read-only. It was repaired without reinstalling (ESP backup, `fsck.vfat -y` on the unmounted partition, `grub-install`, `grub-mkconfig` and the final snapshots step from the live session) and then both Windows and Arctiva booted from GRUB.
  - Still unknown why that corrupt folder was there (left over from an earlier install on that ESP, Windows fast startup or the attempt itself): see `TODO.md`.
- **2026-11-23, lighter ISO (1,768,824,832 B, 150 MB smaller), QEMU/KVM VM with UEFI:**
  - Boot in 35 s; installation with network, unencrypted and encrypted: correct. With network the installer leaves the 8 deferred applications installed and `arctiva-settings` 0.7.0 sets the state to `done`.
  - Installation **without network**: correct (3.2 GB disk versus 4.2 GB); Kate, Okular, Gwenview, Spectacle and the rest are absent and the state is `pending`. Booting that system with network, `arctiva-deferred.service` installed the 8 applications and `qt6-webengine` in a few minutes and left `done`.
  - Not checked on screen: the notifications (only tried with a simulated `notify-send`) and the new notices on the installer's welcome and summary pages.

## How to report a failure

Open an issue with the repository template: version, machine, what you did and what happened (and `journalctl -b` or a screenshot if you can). Link it here next to the case.
