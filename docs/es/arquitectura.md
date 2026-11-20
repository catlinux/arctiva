# Arquitectura de Archtiva

> **Estado:** propuesta pendiente de aprobación (versión 0.1.0).
> English version: [../en/architecture.md](../en/architecture.md)

Este documento analiza la viabilidad del proyecto y recoge las decisiones de arquitectura (D-01…D-16) con su justificación. Cada decisión aprobada se marcará como **Aprobada**; las que cambien se reescriben aquí y su cambio queda en el CHANGELOG.

## 1. Viabilidad

El objetivo es viable y tiene precedentes: EndeavourOS (repos oficiales de Arch más un repositorio propio pequeño, instalador Calamares), CachyOS, Garuda Linux y SteamOS 3 (Valve) demuestran que una distribución basada en Arch puede ofrecer instalación gráfica y buena experiencia de juego. También hay lecciones en contra: Manjaro mantiene repositorios propios retrasados y eso le causa incompatibilidades con el AUR, y otros proyectos de un solo mantenedor han cerrado por carga de mantenimiento.

Conclusión: **realista si el código propio se mantiene pequeño** y casi todo es integración y configuración de piezas maduras. El riesgo principal no es técnico, sino el mantenimiento continuo de un proyecto rolling release con pocas personas.

Lo que **no** es realista y no se promete:

- Compatibilidad universal con programas y juegos de Windows (ver D-12).
- Una rolling release que nunca se rompa: se mitiga con instantáneas, kernel LTS de reserva y avisos, pero el usuario debe poder ver los problemas.
- Secure Boot activado desde la versión 1.0 (ver D-05).

## 2. Ideas iniciales que conviene corregir

| Idea inicial | Problema | Propuesta |
|---|---|---|
| «Sin repositorios propios» | El instalador (Calamares no está en los repos oficiales), el branding y las herramientas propias tienen que llegar al usuario y actualizarse por algún sitio. | Un repositorio propio **mínimo y firmado** (`[archtiva]`) solo con paquetes propios y los imprescindibles que no están en Arch. Nunca contiene versiones modificadas de paquetes oficiales (D-01). |
| AUR dentro de la tienda | El AUR no está revisado: cualquiera publica scripts que se ejecutan con permisos de compilación. Ponerlo en una tienda para usuarios que vienen de Windows es un riesgo de seguridad. | El AUR es una opción avanzada que se activa a propósito, con advertencia, y no se integra en la tienda (D-07). |
| Tienda que mezcla pacman, AUR y Flatpak | En Arch, Discover con PackageKit funciona mal: la ArchWiki desaconseja usar interfaces PackageKit para actualizar y KDE califica de muy pobre el soporte de Arch. El refresco de bases de datos en segundo plano puede provocar actualizaciones parciales, que Arch no soporta. | Tienda = Discover solo con Flatpak/Flathub y firmware. Paquetes del sistema mediante un catálogo curado en Archtiva Center que siempre actualiza todo el sistema (D-07). |
| Todo en una ISO completa en GitHub | GitHub Releases limita cada archivo a menos de 2 GiB. | ISO de menos de 2 GiB con escritorio completo y extras descargados durante la instalación; plan B con una réplica externa (D-14). |

## 3. Decisiones de arquitectura

### D-01 Base: Arch sin modificar y repositorio propio mínimo

- Repositorios oficiales `core`, `extra` y `multilib` sin cambios ni retrasos. Pacman sigue siendo el único gestor de paquetes del sistema.
- Repositorio `[archtiva]` firmado con GPG y alojado en GitHub, con paquetes propios (`archtiva-settings`, `archtiva-branding`, `archtiva-keyring`, `archtiva-center`, configuración de Calamares) y compilaciones de lo imprescindible que solo está en el AUR (`calamares`, `ckbcomp`).
- Prohibido: reempaquetar o retener paquetes oficiales. Si un paquete oficial se rompe, se mitiga con avisos e instantáneas, no con un fork.

### D-02 Construcción de la ISO: archiso

- `archiso` es la herramienta oficial con la que Arch construye su propia ISO. El perfil de Archtiva deriva del perfil `releng`.
- **Reproducibilidad:** cada publicación fija una fecha del Arch Linux Archive (`archive.archlinux.org/repos/AAAA/MM/DD`), así una ISO concreta se puede reconstruir con los mismos paquetes. El script de construcción y la fecha quedan versionados.

### D-03 Instalador: Calamares

- Alternativas valoradas: **archinstall** (oficial, pero solo en modo texto), **Anaconda** (atado a Fedora), **instalador propio** (coste enorme y riesgo en particionado).
- **Calamares**: instalador gráfico maduro en Qt (encaja con KDE), modular, con soporte de branding, usado por EndeavourOS, Manjaro, KaOS, Debian live y otras. Cubre idioma, teclado, zona horaria, usuarios, particionado manual y automático, instalación junto a Windows, UEFI y cifrado LUKS.
- Modo de instalación: **offline**, copiando el sistema live ya probado (módulo `unpackfs`) y quitando lo exclusivo del live. Después, **extras opcionales online** (juegos, ofimática…) con el módulo `netinstall` si hay conexión. Es rápido, no depende de la red y lo instalado es lo que se ha probado.
- Riesgo: Calamares no está en los repos oficiales; se compila en `[archtiva]` y se vigilan sus versiones (la serie 3.4 está activa en 2026).

### D-04 Disco, arranque y recuperación

- **Solo UEFI con GPT** en la 1.0: cualquier PC compatible con Windows 10/11 lo tiene, y así la matriz de pruebas es la mitad. BIOS heredada queda descartada de momento.
- **Btrfs** con subvolúmenes (`@`, `@home`, `@cache`, `@log`) y compresión zstd.
- **Snapper + snap-pac**: instantánea automática antes y después de cada transacción de pacman.
- **GRUB + grub-btrfs**: se puede arrancar una instantánea desde el menú, que es la recuperación ante una actualización fallida. systemd-boot no puede arrancar instantáneas; Limine sí, pero sus integraciones están en el AUR. Todo lo elegido está en los repos oficiales.
- **Kernels:** `linux` (por defecto) y `linux-lts` como entrada de reserva.
- **Swap:** zram (`zram-generator`).

### D-05 Secure Boot

Arch no ofrece Secure Boot de serie (el `shim` firmado está en el AUR). En la 1.0 el usuario tendrá que desactivarlo, y la documentación y el instalador lo explicarán. Más adelante se estudiará `sbctl` con claves propias. Es una barrera real para quien viene de Windows 11 y se documenta como tal.

### D-06 Escritorio: KDE Plasma 6 sobre Wayland

- Valorados: **GNOME** (paradigma lejano a Windows y extensiones que se rompen en cada versión), **Cinnamon** (muy parecido a Windows, pero Wayland aún inmaduro), **COSMIC** (prometedor, aún joven), **Xfce** (sigue en X11).
- **Plasma**: distribución similar a Windows de serie (menú, barra de tareas, bandeja), configuración gráfica completa, Dolphin, buen soporte de VRR/HDR, juegos y portátiles, y temas globales (Look-and-Feel) que permiten dar identidad **sin parchear KDE**.
- Personalización únicamente con paquetes de configuración (`/etc/xdg`, `/etc/skel`, tema global). Así, una actualización de Plasma no rompe nada propio.
- Sesión Wayland por defecto (KDE ha anunciado que abandona la sesión X11 de Plasma).
- Gestor de inicio: **Plasma Login Manager** (oficial de KDE, en `extra`); tiene el aspecto Breeze fijo, por lo que la identidad se limita a fondo y colores. Reserva: SDDM con tema propio si el primero no convence.

### D-07 Aplicaciones: tienda, catálogo y AUR

- **Tienda:** KDE Discover solo con los motores **Flatpak (Flathub)** y **fwupd** (firmware). Flathub es la fuente por defecto de aplicaciones de escritorio: van aisladas, sus permisos se ven y se pueden cambiar, y se actualizan aparte del sistema. Discover indica el origen de cada aplicación.
- **No se instala** el motor PackageKit de Discover (ver sección 2).
- **Paquetes del sistema** (controladores, códecs, impresión, Steam, herramientas de juego): catálogo curado en Archtiva Center (D-09), que instala con `pacman -Syu --needed <paquetes>`, siempre con el sistema al día, para evitar actualizaciones parciales.
- **AUR:** opción avanzada desactivada por defecto. Se activa desde Archtiva Center con una advertencia clara e instala un asistente (`paru`) desde `[archtiva]`. Nunca se integra en la tienda.

### D-08 Actualizaciones

En el módulo de actualizaciones de Archtiva Center:

1. Detecta actualizaciones con `checkupdates` (pacman-contrib), que usa una base de datos temporal y no provoca actualizaciones parciales.
2. Muestra las noticias de archlinux.org publicadas desde la última actualización. Si alguna exige intervención manual, el proceso se detiene hasta que el usuario la lee, con la explicación y la acción concreta.
3. Lista los paquetes y marca los delicados (kernel, controladores NVIDIA, Mesa, systemd, Plasma).
4. Actualiza con `pacman -Syu` mediante un ayudante privilegiado (polkit), mostrando el registro real. snap-pac crea la instantánea antes.
5. Actualiza los Flatpak.
6. Avisa de archivos `.pacnew` y recomienda reiniciar si cambió el kernel o los controladores.
7. Traduce los errores habituales (conflictos, claves PGP, espacio en disco) a mensajes comprensibles, sin ocultar el texto original.

Antes de escribir esta lógica se evaluará reutilizar **arch-update** (herramienta del AUR que ya hace noticias, `.pacnew` y Flatpak, mantenida por un empaquetador de Arch). Solo se programa lo que falte.

### D-09 Herramientas propias: una sola aplicación

**Archtiva Center**, en Python 3 + PySide6 (Qt 6; ambos en los repos oficiales) y `pyalpm` para consultas de solo lectura. Módulos: bienvenida en el primer arranque, controladores, actualizaciones, extras (catálogo) y opciones avanzadas (AUR). Las acciones privilegiadas pasan por un ayudante polkit con un **conjunto cerrado de operaciones**, nunca por órdenes arbitrarias. Es una sola aplicación en lugar de varias para reducir mantenimiento.

### D-10 Gráficas

Detección con `lspci` y un archivo de correspondencias (familia → paquetes), compartido por el instalador y Archtiva Center.

| Gráfica | Paquetes |
|---|---|
| AMD Radeon (GCN en adelante) | `mesa`, `vulkan-radeon`, `lib32-mesa`, `lib32-vulkan-radeon` |
| Intel integradas y Arc | `mesa`, `vulkan-intel`, `intel-media-driver`, versiones `lib32` |
| NVIDIA Turing y posteriores (GTX 16, RTX 20+) | `nvidia-open` y `nvidia-lts-open` (módulos precompilados para los dos kernels), `nvidia-utils`, `lib32-nvidia-utils`, KMS temprano |
| NVIDIA Pascal/Maxwell (GTX 10/900) | Desde diciembre de 2025 el controlador 580xx solo está en el AUR. **No se instala automáticamente**: se usa `nouveau` y se avisa al usuario con las opciones |
| Portátiles híbridos | `switcheroo-control` e integración de Plasma para lanzar con la gráfica dedicada |

### D-11 Juegos

- `multilib` activado de serie.
- Steam nativo (`steam`, de multilib), `gamemode`, `mangohud`, `gamescope`; Proton se gestiona desde Steam.
- Heroic (Epic/GOG) y ProtonPlus o ProtonUp-Qt como Flatpak; Lutris desde `extra`.
- Se instalan como perfil «Juegos» durante la instalación o desde Archtiva Center.

### D-12 Programas de Windows

- **Bottles** como herramienta principal, **solo en Flatpak**: es el único formato que sus desarrolladores soportan.
- Al abrir un `.exe` o `.msi`, un diálogo propio explica qué va a pasar, ofrece abrirlo con Bottles y enlaza a la base de datos de compatibilidad (WineHQ AppDB, ProtonDB).
- Limitaciones que se comunican claramente: juegos con antitrampas a nivel de kernel (consultar «Are We Anti-Cheat Yet?»), suites como Adobe y Microsoft Office recientes, controladores y utilidades de hardware de Windows.
- `wine` y `winetricks` de los repos, para usuarios avanzados.

### D-13 Identidad y marca

- La política de marcas de Arch permite decir «basada en Arch Linux», pero no usar sus marcas para nombrar el producto ni dar a entender que es oficial. **Antes de publicar** se consultará a `trademarks@archlinux.org` si el nombre «Archtiva» es aceptable.
- El logotipo no debe parecerse al logotipo de Arch. El borrador actual (una «A» con una curva interior) se le parece demasiado; hay que alejarlo y tenerlo en vectorial (SVG), con versión monocroma para iconos pequeños y la pantalla de arranque.
- Arch no da soporte a las derivadas: Archtiva tendrá sus propios canales de ayuda y nunca enviará a los usuarios a los foros de Arch.

### D-14 Distribución de la ISO

GitHub Releases acepta archivos de **menos de 2 GiB** cada uno, sin límite de tamaño total ni de ancho de banda. Opciones valoradas:

| Opción | Valoración |
|---|---|
| ISO completa de más de 2 GiB en GitHub | Imposible |
| Partir la ISO en trozos | Descartada: Rufus, Ventoy y Etcher necesitan un único archivo; mala experiencia para quien viene de Windows |
| ISO de red mínima que lo descarga todo | Descartada como principal: no permite probar el escritorio sin instalar y depende de la red y del estado de los mirrors |
| **ISO de menos de 2 GiB con escritorio completo y extras descargados al instalar** | **Recomendada** |
| Réplica externa (SourceForge o servidor propio) | Plan B si la ISO supera el límite; GitHub conserva las sumas de comprobación y la firma |

Para mantenerla por debajo de 2 GiB: Plasma con una selección de paquetes en lugar de todos los meta-paquetes, compresión xz del sistema de archivos, y Steam, ofimática y juegos como perfiles online en la instalación. El CI fallará si la ISO pasa de 1,9 GiB. **El tamaño real se medirá en la fase 1**; hasta entonces es un objetivo, no un hecho.

### D-15 Automatización (GitHub Actions)

1. **Lint:** shellcheck, `namcap` para los PKGBUILD y comprobación de enlaces de la documentación.
2. **Paquetes:** compilación en contenedor Arch limpio y firma.
3. **ISO:** `mkarchiso` en un contenedor `archlinux` privilegiado.
4. **Prueba de arranque:** QEMU/KVM sin pantalla con firmware UEFI (OVMF); se comprueba por consola serie que se llega al escritorio. Más adelante, instalación automatizada.
5. **Construcción semanal programada** con los paquetes del día, para detectar roturas de Arch antes que los usuarios.
6. **Publicación** solo con una etiqueta aprobada: ISO, `sha256`, firma GPG y notas generadas desde el CHANGELOG.

### D-16 Versionado

- El proyecto sigue SemVer `x.y.z` (archivo `VERSION`). Cada ISO publicada lleva la versión del proyecto: `archtiva-X.Y.Z-x86_64.iso`.
- Antes de la 1.0: cada fase terminada sube la versión menor; las correcciones y la documentación suben el parche.
- Desde la 1.0: mayor si obliga a migrar (por ejemplo, otro esquema de subvolúmenes), menor si añade funciones, parche si solo corrige o recompila.
- Cada paquete de `[archtiva]` tiene su propio `pkgver` en su PKGBUILD.

## 4. Qué desarrollamos y qué integramos

| Desarrollo propio (pequeño) | Integración sin código propio |
|---|---|
| Perfil archiso y scripts de construcción | Arch Linux (core, extra, multilib), pacman |
| Configuración y branding de Calamares | Calamares, KDE Plasma, Discover, Flatpak/Flathub |
| `archtiva-settings` (valores por defecto) | Btrfs, Snapper, snap-pac, grub-btrfs, zram-generator |
| `archtiva-branding` (logo, fondos, Plymouth, tema global) | Mesa, NVIDIA open, Vulkan, firmware, fwupd |
| `archtiva-keyring` y el repositorio `[archtiva]` | Steam, Proton, Lutris, Heroic, Bottles, gamemode, MangoHud |
| Archtiva Center (bienvenida, controladores, actualizaciones, extras) | reflector, pacman-contrib, CUPS, ufw + plasma-firewall |
| Flujos de GitHub Actions y pruebas | arch-update (si la evaluación lo confirma) |

## 5. Riesgos principales

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Roturas de Arch (p. ej. el cambio de NVIDIA 590) | Alto | Construcción semanal en CI, noticias que bloquean, instantáneas, kernel LTS |
| Un único mantenedor | Alto | Poco código propio, todo documentado y automatizado |
| Cambios en Calamares o KDE | Medio | Solo configuración, versiones vigiladas en CI |
| Secure Boot obligatorio en algunos equipos | Medio | Documentación clara; `sbctl` más adelante |
| ISO de más de 2 GiB | Medio | Selección de paquetes y réplica externa |
| Nombre y logo frente a la marca Arch | Medio | Consulta a Arch y logo distinto antes de publicar |
| Seguridad del AUR | Medio | Fuera de la tienda y opcional con advertencia |
| Claves de firma del repositorio | Alto | Clave maestra fuera de línea; subclave de firma en secretos de Actions |
| Pruebas en VirtualBox poco representativas (3D, Wayland) | Medio | Pruebas en hardware real con USB live antes de cada versión |

## 6. Requisitos de hardware

**Equipo anfitrión actual:** Intel i5-14400F (10 núcleos y 16 hilos), 16 GB de RAM, NVIDIA RTX 4060, 108 GB libres en C:. Hyper-V está activo, así que VirtualBox funciona sobre él: es más lento y sin virtualización anidada.

| Máquina | CPU | RAM | Disco | Notas |
|---|---|---|---|---|
| VM de construcción (Arch Linux) | 4–6 vCPU | 8 GB | 80 GB dinámico | EFI. Construye paquetes e ISO. La VM «Archtiva» actual tiene 2 vCPU, 4 GB y 10 GB: hay que ampliarla |
| VM de pruebas de la ISO | 2–4 vCPU | 4 GB | 40 GB dinámico | EFI, VMSVGA con 128 MB de vídeo. Se recrea en cada prueba |
| Hardware real | — | — | USB de 8 GB o más | La RTX 4060 del anfitrión sirve para probar NVIDIA con el USB live |
| GitHub Actions | runner estándar | 16 GB | ~14 GB libres | Suficiente para una ISO de menos de 2 GiB |

**Requisitos mínimos de Archtiva (objetivo):** x86-64 con UEFI, 4 GB de RAM (8 GB recomendados), 40 GB de disco (64 GB recomendados por las instantáneas), y gráfica con Vulkan para jugar.
