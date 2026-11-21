# Development guide

> Versión en castellano: [../es/desarrollo.md](../es/desarrollo.md)

## Environment

- **Workstation:** Windows 11 with Visual Studio Code and Git. Editing and repository management happen here; nothing is built here.
- **Build VM:** Arch Linux in VirtualBox (EFI, 4–6 vCPU, 8 GB RAM, 80 GB dynamic disk). Builds packages and the ISO with `archiso`.
- **Test VM:** recreated for every ISO (EFI, 2–4 vCPU, 4 GB, 40 GB, VMSVGA with 128 MB).
- **CI:** GitHub Actions builds and tests from a clean state (see D-15 in [architecture.md](architecture.md)).

## Setting up the build VM

Verified on 2026-11-20 with VirtualBox on Windows 11.

1. **Create the VM** "Arctiva" (Linux, Arch Linux 64-bit) with EFI, 4 vCPU, 8 GB RAM, 128 MB VRAM and an 80 GB disk. To adjust an existing (powered-off) VM from PowerShell: `VBoxManage modifyvm Arctiva --cpus 4 --memory 8192 --vram 128` and `VBoxManage modifymedium disk <path.vdi> --resize 81920`.
2. **Install Arch** with the official ISO (https://archlinux.org/download/) and `archinstall`: whole disk with ext4, GRUB or systemd-boot, `Minimal` profile, a sudo user and extra packages `archiso git openssh base-devel`. If the VM drops to the "EFI Shell", type `fs0:\EFI\BOOT\BOOTX64.EFI`.
3. **SSH access from Windows** (the VirtualBox console has no copy and paste): with the VM powered off, `VBoxManage modifyvm Arctiva --natpf1 "ssh,tcp,127.0.0.1,2222,,22"`. Inside the VM, `sudo systemctl enable --now sshd`. From Windows: `ssh -p 2222 user@127.0.0.1`.
4. **Clone the repository** inside the VM, on its ext4 disk (not in a Windows shared folder, which breaks permissions and symlinks): `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""`, add the public key as a read-only deploy key on `catlinux/arctiva`, then `git clone git@github.com:catlinux/arctiva.git ~/arctiva`.
5. **Build the ISO** (use a working directory on disk, not `/tmp`, which lives in RAM): `mkdir -p ~/out ~/work && sudo mkarchiso -v -w ~/work -o ~/out /usr/share/archiso/configs/releng`. The unmodified `releng` profile produces an ISO of about 1.3 GB.
6. **Copy the ISO to Windows**, from Windows PowerShell: `scp -P 2222 user@127.0.0.1:out/<iso> C:\path\Arctiva-out\`. The output folder must be outside the repository.
7. **Test it** in a new VM ("Arctiva-test", EFI, 4 GB, no disk) with the ISO in the optical drive: it boots to the `archiso` live console.

> VirtualBox shared folders are not used: with kernel 7.3 the automount fails with `vboxsf: Unknown parameter 'tag'`.

> Hyper-V is active on the host, so VirtualBox runs on top of it: slower, and no nested virtualisation. QEMU/KVM tests run in CI, or inside the build VM if performance allows.

## Building the Arctiva ISO

> Checked on 2026-11-20 in the VM (4 vCPU, 4 GB): the build takes about 12 minutes and the ISO boots in VirtualBox to the desktop in about two and a half minutes. The first CI run (build and QEMU boot test) passes.

The profile lives in `iso/` (derived from `releng`) and is built with `build.sh`, inside the VM:

```sh
cd ~/arctiva && git pull
sudo ./build.sh -o ~/out          # packages from the Arch Linux Archive date in iso/archive-date
sudo ./build.sh -o ~/out -d latest  # today's packages, no pinned date
```

- The ISO is named `arctiva-<VERSION>-x86_64.iso` and comes with its `.sha256`. The script fails if it exceeds 1.9 GiB (D-14).
- The working directory (by default `/var/tmp/arctiva-work`) must not exist; mkarchiso deletes it when done. With `-k` it is kept, to measure what takes space (`du`, `pacman --root <work>/x86_64/airootfs -Qi`); delete it afterwards with `sudo rm -rf`.
- The ISO does not include package documentation (`NoExtract` in `iso/pacman.conf`) to stay under the limit.
- VirtualBox tests: the test VM has 4 GB and the build VM another 4; with 16 GB on the host both cannot run at once while other programs are open (it fails with `VERR_UNRESOLVED_ERROR`).
- If `archive.archlinux.org` is down, the script retries and then fails with a hint. Set `ARCHIVE_MIRRORS="https://mirror1 https://mirror2"` (same `repos/YYYY/MM/DD/` layout) to add fallback mirrors for the same date; `-d latest` is a last resort and the ISO is not reproducible.
- To pin another package date, change `iso/archive-date` (format `YYYY/MM/DD`).
- The ISO only boots in UEFI mode. The "safe graphics" entry boots with `nomodeset`.
- Automatic boot test, as in CI: `tests/boot-test.sh ~/out/arctiva-*.iso` (needs `qemu-system-x86_64`, `OVMF` and `7z`; without `7z` it must run with `sudo`). Firmware path in the `OVMF` variable; with access to `/dev/kvm` (`kvm` group) it takes a few minutes.
- `build.sh` first builds the in-house packages in `packages/` (`arctiva-settings`, `arctiva-branding`, `arctiva-hardware`, `arctiva-center`, Calamares and `ckbcomp`) and `installer/` with `packages/build-packages.sh` into an unsigned local `arctiva-local` repository (only until phase 3). Use `-l <dir>` to reuse a prebuilt one, or `-c <dir>` to keep the repository between builds: only packages whose version changed are rebuilt (the installer configuration always is), so Calamares is not compiled for every ISO. Clear that directory when `iso/archive-date` changes. It adds ~10 minutes and needs network; the PKGBUILDs use current packages, not the Archive date.
- Live services are enabled with `Wants=` in `iso/airootfs/etc/systemd/system/*.target.d/`: the repository holds no symbolic links because it is edited from Windows.

### On any Linux with Docker

No Arch VM needed: a privileged `archlinux` container, as in CI. Checked on Debian 13.

```sh
docker run --rm --privileged --cpus=2 -v arctiva-pkgcache:/var/cache/pacman/pkg -v "$PWD:/repo" -w /repo archlinux:latest   bash -c 'pacman -Syu --noconfirm --needed archiso && ./build.sh -o /repo/out -w /var/tmp/arctiva-work; rc=$?; chown -R 1000:1000 /repo/out; exit $rc'
```

- The `arctiva-pkgcache` volume keeps downloaded packages between builds.
- `--cpus=2` limits the load if the machine does other work; drop it to go faster.
- `chown` gives the ISO back to your user (the container writes as root; change `1000:1000` if your UID differs).

### Viewing and testing the ISO from another computer

`tests/run-live.sh` boots the ISO in QEMU/KVM with UEFI and a 40 GB virtual disk, and shows it in the browser with noVNC. It is meant for a Linux machine reached over SSH (for example, with VS Code Remote-SSH).

1. Once: `sudo apt install novnc qemu-system-x86 ovmf qemu-utils` and the user in the `kvm` group (`sudo usermod -aG kvm $USER`).
2. `tests/run-live.sh` boots the most recent ISO in `out/`.
3. Open `http://localhost:6080/vnc.html` in the browser and click "Connect". VS Code forwards the port by itself; without VS Code: `ssh -L 6080:localhost:6080 <host>`.

- `-d` boots from the virtual disk (the installed system, from phase 2 on); `-r` wipes the disk and the NVRAM and starts afresh.

### Testing the installer

The Calamares configuration lives in `installer/` (package `arctiva-calamares-config`): `calamares/` is installed to `/etc/calamares/` and `scripts/` to `/usr/lib/arctiva-installer/`. It is built with the rest of `packages/` when building the ISO.

1. `tests/run-live.sh -r` boots the ISO with an empty virtual disk (40 GB; the installer asks for 25 GiB).
2. In the live session, open "Install Arctiva" from the menu, or run `arctiva-installer -d` in Konsole (`-d` prints Calamares' log to the terminal). The launcher first checks the machine and writes the result to `/run/arctiva/equipo.json`, which the "Check" page shows.
3. When it finishes, power off and boot the installed system with `tests/run-live.sh -d`.

- When online, the installer runs `pacman -Syu` and installs `linux-lts`: the older the `iso/archive-date` date, the longer it takes.
- If you change the live-only files in `iso/airootfs/`, also change the `exclude` list in `installer/calamares/modules/unpackfs.conf`.
- To test the "Check" page without Windows, run `sudo tests/fake-windows-disk.sh <limpio|hibernado|bitlocker>` in the live session (copy the script into the VM; **it wipes the virtual disk**) and open the launcher again.
- To test "Install alongside" you need a large disk: the installer asks for 25 GiB free for Arctiva on top of Windows. Example: `DISK_SIZE=100G tests/run-live.sh -r` and, in the live session, `sudo NTFS_SIZE=60G tests/fake-windows-disk.sh limpio /dev/vda` before opening the installer. The script creates the ESP with `bootmgfw.efi` and `BCD`: `os-prober` needs both to recognise Windows.
- Manual partitioning: "New Partition Table" (GPT), a 300 MiB `fat32` ESP mounted at `/boot/efi` with the `boot` flag, and a `btrfs` root at `/` with the rest. The installer creates the `@`, `@home`, `@cache`, `@log` and `@snapshots` subvolumes.
- The disk and the NVRAM live in `~/arctiva-vm` (`VM_DIR` variable), outside the repository.
- No 3D acceleration or sound: the desktop works, but games and the real GPU are tested on hardware from a USB stick.

### Arctiva Center

The code of `arctiva-center` lives in `center/` (the PKGBUILD in `packages/arctiva-center/` receives it as `../center`). The logic in `arctiva_center/core/` does not import Qt and is tested without PySide6 or Arch: `cd center && python3 -m pytest` (needs `pytest` and Python 3.11 or later). The window (PySide6 + QML + Kirigami) is tested in the live session or on an installed system: `python3 -m arctiva_center --module updates` from `center/`, or `pacman -U` on the built package. Translations: sources in English, catalogues in `center/translations/*.ts`; `lrelease` (`/usr/lib/qt6/bin/`, package `qt6-tools`) generates the `.qm` files in `build()`.

### Publishing a package to `[arctiva]`

Packages in `packages/arctiva-*` are built, signed and published by the `Repositorio` workflow (`.github/workflows/repo.yml`) on each push to `main` that touches `packages/arctiva-*/**` or `center/**`. Only packages whose version (`pkgver`-`pkgrel`) is not yet in the published database are built, so to publish a change, **bump `pkgver` (or `pkgrel`)** in its PKGBUILD. The result goes to the `x86_64` release of `catlinux/arctiva-repo`. Signing keys: [signing.md](signing.md).

## Line endings

The repository enforces LF line endings (`.gitattributes`). Shell scripts and PKGBUILDs with CRLF fail on Linux.

## Versioning

- SemVer `x.y.z` in the [`VERSION`](../../VERSION) file; policy in D-16.
- Every behaviour change bumps the version and adds an entry to both changelogs (`CHANGELOG.md` in English and `CHANGELOG.es.md` in Spanish) in the same commit.
- Unversioned changes go under `## [Unreleased]` / `## [Sin publicar]`.
- `vX.Y.Z` tags are created only when an approved version is released.

## Documentation

- Bilingual: the English root files (`README.md`, `CHANGELOG.md`, `TODO.md`) have a Spanish counterpart (`*.es.md`); `docs/en/` and `docs/es/` contain the same documents.
- Both languages are updated together in the same commit. A document without its counterpart is a bug.
- Architecture decisions are recorded in [architecture.md](architecture.md) with their rationale.

## Commits

- Descriptive messages in Spanish, one topic per commit.
- Secrets (signing keys, tokens) are never committed: they live in GitHub Actions secrets or outside the repository.
