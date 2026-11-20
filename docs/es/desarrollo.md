# Guía de desarrollo

> English version: [../en/development.md](../en/development.md)

## Entorno

- **Equipo de trabajo:** Windows 11 con Visual Studio Code y Git. Aquí se edita y se gestiona el repositorio; no se construye nada.
- **VM de construcción:** Arch Linux en VirtualBox (EFI, 4–6 vCPU, 8 GB de RAM, disco dinámico de 80 GB). Construye paquetes e ISO con `archiso`.
- **VM de pruebas:** se crea de nuevo para cada ISO (EFI, 2–4 vCPU, 4 GB, 40 GB, VMSVGA con 128 MB).
- **CI:** GitHub Actions construye y prueba en limpio (ver D-15 en [arquitectura.md](arquitectura.md)).

## Preparar la VM de construcción

Comprobado el 2026-11-20 con VirtualBox en Windows 11.

1. **Crear la VM** «Arctiva» (Linux, Arch Linux 64 bits) con EFI, 4 vCPU, 8 GB de RAM, 128 MB de VRAM y un disco de 80 GB. Desde PowerShell, para ajustar una VM existente (apagada): `VBoxManage modifyvm Arctiva --cpus 4 --memory 8192 --vram 128` y `VBoxManage modifymedium disk <ruta.vdi> --resize 81920`.
2. **Instalar Arch** con la ISO oficial (https://archlinux.org/download/) y `archinstall`: disco completo con ext4, GRUB o systemd-boot, perfil `Minimal`, usuario con sudo y paquetes adicionales `archiso git openssh base-devel`. Si la VM cae a la «EFI Shell», escribir `fs0:\EFI\BOOT\BOOTX64.EFI`.
3. **Acceso por SSH desde Windows** (la consola de VirtualBox no permite copiar y pegar): con la VM apagada, `VBoxManage modifyvm Arctiva --natpf1 "ssh,tcp,127.0.0.1,2222,,22"`. Dentro de la VM, `sudo systemctl enable --now sshd`. Desde Windows: `ssh -p 2222 usuario@127.0.0.1`.
4. **Clonar el repositorio** dentro de la VM, sobre su disco ext4 (no en una carpeta compartida de Windows, que rompe permisos y enlaces simbólicos): `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""`, añadir la clave pública como *deploy key* de solo lectura en `catlinux/arctiva` y `git clone git@github.com:catlinux/arctiva.git ~/arctiva`.
5. **Construir la ISO** (usar un directorio de trabajo en disco, no `/tmp`, que está en RAM): `mkdir -p ~/out ~/work && sudo mkarchiso -v -w ~/work -o ~/out /usr/share/archiso/configs/releng`. Con el perfil `releng` sin cambios genera una ISO de unos 1,3 GB.
6. **Traer la ISO a Windows**, desde PowerShell de Windows: `scp -P 2222 usuario@127.0.0.1:out/<iso> C:\ruta\Arctiva-out\`. La carpeta de salida debe estar fuera del repositorio.
7. **Probarla** en una VM nueva («Arctiva-test», EFI, 4 GB, sin disco) con la ISO en la unidad óptica: arranca hasta la consola live de `archiso`.

> Las carpetas compartidas de VirtualBox no se usan: con el kernel 7.3 el montaje automático falla con `vboxsf: Unknown parameter 'tag'`.

> Hyper-V está activo en el equipo anfitrión, así que VirtualBox funciona sobre él: es más lento y sin virtualización anidada. Las pruebas con QEMU/KVM se hacen en el CI o dentro de la VM de construcción si el rendimiento lo permite.

## Construir la ISO de Arctiva

> Comprobado el 2026-11-20 en la VM (4 vCPU, 4 GB): la construcción tarda unos 12 minutos y la ISO arranca en VirtualBox hasta el escritorio en unos 2 minutos y medio. El primer run del CI (construcción y prueba de arranque en QEMU) pasa.

El perfil está en `iso/` (derivado de `releng`) y se construye con `build.sh`, dentro de la VM:

```sh
cd ~/arctiva && git pull
sudo ./build.sh -o ~/out          # paquetes del Arch Linux Archive de iso/archive-date
sudo ./build.sh -o ~/out -d latest  # paquetes del día, sin fecha fijada
```

- La ISO sale como `arctiva-<VERSION>-x86_64.iso` con su `.sha256`. El script falla si pasa de 1,9 GiB (D-14).
- El directorio de trabajo (por defecto `/var/tmp/arctiva-work`) no debe existir; mkarchiso lo borra al acabar. Con `-k` se conserva, para medir qué ocupa espacio (`du`, `pacman --root <trabajo>/x86_64/airootfs -Qi`); después hay que borrarlo con `sudo rm -rf`.
- La ISO no lleva la documentación de los paquetes (`NoExtract` en `iso/pacman.conf`) para no pasar del límite.
- Pruebas en VirtualBox: la VM de pruebas tiene 4 GB y la de construcción otros 4; con 16 GB en el anfitrión no caben las dos encendidas a la vez si hay otros programas abiertos (falla con `VERR_UNRESOLVED_ERROR`).
- Para fijar otra fecha de paquetes, cambia `iso/archive-date` (formato `AAAA/MM/DD`).
- La ISO solo arranca en UEFI. La entrada «safe graphics» arranca con `nomodeset`.
- Prueba de arranque automática, como en el CI: `tests/boot-test.sh ~/out/arctiva-*.iso` (necesita `qemu-system-x86_64`, `OVMF` y `7z`; sin `7z` hay que ejecutarlo con `sudo`). Ruta del firmware en la variable `OVMF`; con acceso a `/dev/kvm` (grupo `kvm`) tarda unos minutos.
- `build.sh` compila antes los paquetes propios de `packages/` (Calamares y `ckbcomp`) con `packages/build-packages.sh` en un repositorio local `arctiva-local` sin firma (solo hasta la fase 3). Usa `-l <directorio>` para reutilizar uno ya compilado. Añade ~10 minutos y necesita red; los PKGBUILD usan los paquetes del día, no la fecha del Archive.
- Los servicios del live se activan con `Wants=` en `iso/airootfs/etc/systemd/system/*.target.d/`: el repositorio no guarda enlaces simbólicos porque se edita desde Windows.

### En cualquier Linux con Docker

Sin VM de Arch: un contenedor `archlinux` con privilegios, igual que el CI. Comprobado en Debian 13.

```sh
docker run --rm --privileged --cpus=2 -v arctiva-pkgcache:/var/cache/pacman/pkg -v "$PWD:/repo" -w /repo archlinux:latest   bash -c 'pacman -Syu --noconfirm --needed archiso && ./build.sh -o /repo/out -w /var/tmp/arctiva-work; rc=$?; chown -R 1000:1000 /repo/out; exit $rc'
```

- El volumen `arctiva-pkgcache` guarda los paquetes descargados entre construcciones.
- `--cpus=2` limita la carga si el equipo hace otras cosas; quítalo para ir más rápido.
- `chown` devuelve la ISO a tu usuario (el contenedor escribe como root; cambia `1000:1000` si tu UID es otro).

### Ver y probar la ISO desde otro equipo

`tests/run-live.sh` arranca la ISO en QEMU/KVM con UEFI y un disco virtual de 40 GB, y la muestra en el navegador con noVNC. Sirve para trabajar en un Linux al que se entra por SSH (por ejemplo, con VS Code Remote-SSH).

1. Una vez: `sudo apt install novnc qemu-system-x86 ovmf qemu-utils` y el usuario en el grupo `kvm` (`sudo usermod -aG kvm $USER`).
2. `tests/run-live.sh` arranca la ISO más reciente de `out/`.
3. Abre `http://localhost:6080/vnc.html` en el navegador y pulsa «Connect». VS Code reenvía el puerto solo; sin VS Code: `ssh -L 6080:localhost:6080 <equipo>`.

- `-d` arranca desde el disco virtual (el sistema instalado, desde la fase 2); `-r` borra el disco y la NVRAM y empieza de cero.
- El disco y la NVRAM se guardan en `~/arctiva-vm` (variable `VM_DIR`), fuera del repositorio.
- Sin aceleración 3D ni sonido: el escritorio funciona, pero los juegos y la gráfica real se prueban en hardware con un USB.

## Finales de línea

El repositorio fuerza finales de línea LF (`.gitattributes`). Los scripts de shell y los PKGBUILD con CRLF fallan en Linux.

## Versionado

- SemVer `x.y.z` en el archivo [`VERSION`](../../VERSION); política en D-16.
- Cada cambio de comportamiento sube la versión y añade su entrada en los dos CHANGELOG (`CHANGELOG.md` en inglés y `CHANGELOG.es.md` en castellano), en el mismo commit.
- Lo que aún no tiene versión va en `## [Unreleased]` / `## [Sin publicar]`.
- Las etiquetas `vX.Y.Z` solo se crean al publicar una versión aprobada.

## Documentación

- Bilingüe: los archivos de la raíz en inglés (`README.md`, `CHANGELOG.md`, `TODO.md`) tienen su par en castellano (`*.es.md`); `docs/en/` y `docs/es/` contienen los mismos documentos.
- Ambos idiomas se actualizan juntos en el mismo commit. Un documento sin su par es un error.
- Las decisiones de arquitectura se registran en [arquitectura.md](arquitectura.md) con su justificación.

## Commits

- Mensajes en castellano, descriptivos, un tema por commit.
- Nunca se suben secretos (claves de firma, tokens): van en los secretos de GitHub Actions o fuera del repositorio.
