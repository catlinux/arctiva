# Pruebas en hardware real

> English version: [../en/testing.md](../en/testing.md)

Matriz de pruebas que se hacen en equipos físicos antes de publicar una versión. Una casilla por caso; al hacerla, se anota la fecha y la versión. Cada fallo se abre como issue en GitHub y se enlaza aquí.

**Antes de empezar:** ISO verificada (`sha256sum -c`), USB hecho con una herramienta que escriba en GPT/UEFI, **Secure Boot desactivado** (D-05) y copia de seguridad.

## 1. Portátil (Windows + Manjaro, que se reemplaza conservando Windows)

### 1.1 Arrancar sin instalar (la primera prueba, sin riesgo)

- [ ] Arranca desde el USB y llega al escritorio (anota si ha hecho falta «safe graphics»).
- [ ] Se ve el fondo, la barra centrada y el menú de inicio con buscador.
- [ ] Wifi: lista redes y conecta. Bluetooth: se ve y se empareja.
- [ ] Audio: suena por altavoces y auriculares.
- [ ] Teclado, panel táctil, brillo y teclas de función.
- [ ] Gráficas híbridas: anota qué GPU usa el escritorio.
- [ ] Arctiva Center → Controladores: detecta la gráfica.

### 1.2 Comprobaciones antes de instalar

- [ ] ¿BitLocker en Windows? (Administración de discos o `manage-bde -status`). Si sí, **tener la clave de recuperación**.
- [ ] Windows apagado del todo (no hibernado, inicio rápido desactivado).
- [ ] La página «Comprobación» del instalador muestra lo que esperas.

### 1.3 Instalación (solo tras las anteriores)

- [ ] «Reemplazar una partición» sobre la de Manjaro, conservando Windows y la partición EFI compartida.
- [ ] El instalador termina sin errores.
- [ ] Arranca Arctiva; el menú de GRUB muestra el tema y **Windows** en la lista.
- [ ] Windows arranca desde GRUB (y pide la clave de BitLocker solo si estaba activo).
- [ ] Entrada vieja `EFI/Manjaro`: decidir si se avisa o se limpia con `efibootmgr` (con tu aprobación).
- [ ] Wifi, Bluetooth, batería, suspensión y reanudación, tapa, brillo.
- [ ] Gráficas híbridas (`switcheroo-control`): una aplicación en la GPU dedicada.

### 1.4 Cifrado (si se prueba)

- [ ] Tiempo desde teclear la contraseña en GRUB hasta el inicio de sesión: ____ s (aceptable hasta unos 15 s; en QEMU con KVM son unos 30 s).

### 1.5 Una semana de uso

- [ ] Actualizaciones desde Arctiva Center (con noticias y paquetes delicados).
- [ ] Arrancar una instantánea desde GRUB y volver al estado normal.

## 2. PC de sobremesa (i5-14400F, RTX 4060)

- [ ] USB live: arranque, «safe graphics», Wayland, red y audio.
- [ ] Instalación en un disco libre o USB externo: el instalador pone el controlador NVIDIA.
- [ ] KMS temprano (sin parpadeos), monitor externo, suspensión y reanudación.
- [ ] Steam con un juego con Proton, Heroic, MangoHud.

## 3. Comprobaciones de la 0.7.x hechas en máquina virtual (QEMU/UEFI)

- [x] Instalación sin cifrar y cifrada; arranque, GRUB con tema, Plymouth, inicio de sesión, escritorio.
- [x] Tienda: buscar, instalar y quitar desde Arch y Flathub; AUR con revisión; diálogo de `.exe`.
- [ ] Logo del fabricante (BGRT) bajo Plymouth: solo se ve en hardware real.

## Cómo anotar un fallo

Abre un issue con la plantilla del repositorio: versión, equipo, qué hiciste y qué pasó (y `journalctl -b` o la captura si puedes). Enlázalo aquí junto al caso.
