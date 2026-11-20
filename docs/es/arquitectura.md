# Arquitectura de Arctiva

> **Estado:** aprobada (versión 0.1.7).
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
| «Sin repositorios propios» | El instalador (Calamares no está en los repos oficiales), el branding y las herramientas propias tienen que llegar al usuario y actualizarse por algún sitio. | Un repositorio propio **mínimo y firmado** (`[arctiva]`) solo con paquetes propios y los imprescindibles que no están en Arch. Nunca contiene versiones modificadas de paquetes oficiales (D-01). |
| AUR dentro de la tienda | El AUR no está revisado: cualquiera publica scripts que se ejecutan con permisos de compilación. Para usuarios que vienen de Windows es un riesgo de seguridad. | Se acepta con condiciones: fuente separada y bien visible, desactivada hasta que el usuario la activa, aviso antes de cada instalación y PKGBUILD consultable (D-07). |
| Tienda que mezcla pacman, AUR y Flatpak | En Arch, Discover con PackageKit funciona mal: la ArchWiki desaconseja usar interfaces PackageKit para actualizar y KDE califica de muy pobre el soporte de Arch. El refresco de bases de datos en segundo plano puede provocar actualizaciones parciales, que Arch no soporta. | Una tienda propia, dentro de Arctiva Center, que distingue las tres fuentes y nunca deja el sistema a medio actualizar (D-07). |
| Todo en una ISO completa en GitHub | GitHub Releases limita cada archivo a menos de 2 GiB. | ISO de menos de 2 GiB con escritorio completo y extras descargados durante la instalación; plan B con una réplica externa (D-14). |

## 3. Decisiones de arquitectura

### D-01 Base: Arch sin modificar y repositorio propio mínimo (**Aprobada**)

- Repositorios oficiales `core`, `extra` y `multilib` sin cambios ni retrasos. Pacman sigue siendo el único gestor de paquetes del sistema.
- Repositorio `[arctiva]` firmado con GPG y alojado en GitHub, con paquetes propios (`arctiva-settings`, `arctiva-branding`, `arctiva-keyring`, `arctiva-center`, configuración de Calamares) y compilaciones de lo imprescindible que solo está en el AUR (`calamares`, `ckbcomp`).
- Prohibido: reempaquetar o retener paquetes oficiales. Si un paquete oficial se rompe, se mitiga con avisos e instantáneas, no con un fork.

### D-02 Construcción de la ISO: archiso (**Aprobada**)

- `archiso` es la herramienta oficial con la que Arch construye su propia ISO. El perfil de Arctiva deriva del perfil `releng`.
- **Reproducibilidad:** cada publicación fija una fecha del Arch Linux Archive (`archive.archlinux.org/repos/AAAA/MM/DD`), así una ISO concreta se puede reconstruir con los mismos paquetes. El script de construcción y la fecha quedan versionados.

### D-03 Instalador: Calamares a medida (**Aprobada**)

- Alternativas valoradas: **archinstall** (oficial, pero solo en modo texto), **Anaconda** (atado a Fedora), los instaladores de Ubuntu, elementary/Pop!_OS y Vanilla OS (cada uno atado a su distribución) y un **instalador propio** (coste enorme; el particionado, sobre todo redimensionar Windows para el arranque dual, es la parte con más riesgo de perder datos).
- **Calamares** es el motor: maduro, en Qt (encaja con KDE), modular, usado por EndeavourOS, Manjaro, KaOS, Debian live y otras. Cubre idioma, teclado, zona horaria, usuarios, particionado manual y automático, instalación junto a Windows, UEFI y cifrado LUKS.
- **Su aspecto básico es la configuración por defecto, no un límite.** La interfaz se rehace con QML para que tenga la identidad de Arctiva:
  - Barra lateral y navegación propias en QML (`sidebar: qml` y `navigation: qml` en el branding).
  - Versiones QML de las páginas que trae Calamares (`welcomeq`, `localeq`, `keyboardq`, `usersq`, `summaryq`, `finishedq`) con diseño propio. El perfil (Básico, Juegos, Oficina; los dos últimos se descargan si hay conexión) se elige con `packagechooserq`, y la página «Comprobación» (ver arranque dual) usa `notesqml`.
  - Orden de las páginas: bienvenida, idioma y zona, teclado, perfil, comprobación, disco, usuarios, resumen, instalación y fin.
  - La página de particionado no tiene versión QML: se integra con una hoja de estilo Qt (`stylesheet.qss`) para que siga el mismo diseño. Si alguna parte dibujada en C++ (la barra de particiones) no la acepta, se deja como está.
  - Identidad: barra lateral con el degradado azul noche del logo, contenido claro con acento azul y avisos con icono y texto, no solo color. Tipografía provisional Noto Sans hasta elegir la corporativa.
  - Presentación en QML durante la copia de archivos.
  - **Sin parches al código C++ de Calamares**: solo configuración, branding y módulos propios (QML o Python). Si algún día hace falta un parche, se propone a upstream.
- Si el resultado no alcanzara el nivel deseado, la alternativa sería una interfaz propia sobre el motor de archinstall, resolviendo aparte el redimensionado de particiones de Windows. Se valoraría con un prototipo.
- Modo de instalación: **offline**, copiando el sistema live ya probado (módulo `unpackfs`) y quitando lo exclusivo del live. Después, **extras opcionales online** (juegos, ofimática…) con el módulo `netinstall` si hay conexión. Es rápido, no depende de la red y lo instalado es lo que se ha probado.
- **Arranque dual con Windows:** muchos equipos con Windows 11 traen la partición cifrada con BitLocker (cifrado del dispositivo), y Calamares no puede redimensionar una partición cifrada ni detecta BitLocker o el inicio rápido de Windows, que deja NTFS en estado hibernado. Un lanzador propio se ejecuta antes de Calamares y comprueba el equipo (particiones BitLocker, NTFS hibernado con `ntfs-3g.probe`, presencia de Windows); la página «Comprobación», antes de la de disco, muestra el resultado:
  - **Bloqueo:** Windows hibernado o con inicio rápido. Explica cómo apagarlo del todo y ofrece salir del instalador; no se puede instalar junto a Windows hasta corregirlo (`ntfsresize`, del paquete `ntfsprogs`, se niega a reducir un NTFS hibernado). Calamares no deja desactivar «Siguiente» desde una página QML, así que el bloqueo es una recomendación y no impide borrar el disco entero.
  - **Aviso:** BitLocker activo. Reducir la partición desde Windows (Administración de discos) y tener a mano la clave de recuperación, que Windows pedirá por haber cambiado Secure Boot (D-05).
  - GRUB lista Windows en su menú (`os-prober`). Arctiva guarda la hora del firmware en UTC y Windows en hora local: la ayuda explica cómo ajustarlo.
- Riesgo: Calamares no está en los repos oficiales; se compila en `[arctiva]` y se vigilan sus versiones (la 3.4.3, de septiembre de 2026, es la fijada; compila con Qt 6). Su API QML cambia entre versiones: la versión queda fijada en el repositorio propio y cada actualización se prueba antes de publicarla.

### D-04 Disco, arranque y recuperación (**Aprobada**)

- **Solo UEFI con GPT** en la 1.0: cualquier PC compatible con Windows 10/11 lo tiene, y así la matriz de pruebas es la mitad. BIOS heredada queda descartada de momento. La ISO solo arranca en UEFI, así que un equipo sin UEFI no llega al instalador (Calamares no comprueba el modo de arranque).
- **Partición EFI** montada en `/boot/efi`; solo contiene GRUB, así que sirve la de Windows. **`/boot` va dentro de `@`**: cada instantánea guarda el kernel y el initramfs que corresponden a sus módulos y arranca sin desajustes.
- **Btrfs** con subvolúmenes (`@`, `@home`, `@cache`, `@log`, `@snapshots`) y compresión zstd. `@snapshots` se monta en `/.snapshots`, fuera de `@`: sin él, Snapper no puede devolver el sistema a una instantánea anterior.
- **Snapper + snap-pac**: instantánea automática antes y después de cada transacción de pacman.
- **GRUB + grub-btrfs**: se puede arrancar una instantánea desde el menú, que es la recuperación ante una actualización fallida. Las instantáneas son de solo lectura: el hook `grub-btrfs-overlayfs` de mkinitcpio les pone encima una capa temporal escribible para que arranquen. systemd-boot no puede arrancar instantáneas; Limine sí, pero sus integraciones están en el AUR. Todo lo elegido está en los repos oficiales.
- **Kernels:** `linux` (por defecto) y `linux-lts` como entrada de reserva. `linux-lts` no va en la ISO (ocuparía unos 250 MB, D-14): el instalador lo descarga si hay conexión y, si no, Arctiva Center lo ofrece después.
- **Swap:** zram (`zram-generator`). zram no permite hibernar: la 1.0 no tiene hibernación (la suspensión sí funciona). Añadirla más adelante (subvolumen `@swap` con un archivo de intercambio) queda pendiente.
- **Cifrado (opcional, desmarcado por defecto):** **LUKS1** sobre la partición de Arctiva, con `/boot` cifrado dentro. GRUB pide la contraseña **una sola vez**; un archivo de clave dentro del initramfs, que vive en la partición cifrada, desbloquea el sistema sin pedirla de nuevo (módulos `luksbootkeyfile` e `initcpiocfg` con el hook `encrypt`, que es además el que necesita `grub-btrfs-overlayfs`).
  - Por qué no LUKS2: GRUB admite Argon2 desde la 2.14 (Arch tiene la 2.16), pero Calamares no deja elegir el método de derivación de la clave y usa Argon2id con 1 GiB de memoria, con el que hay informes de GRUB sin memoria al arrancar. LUKS1 es el valor por defecto de Calamares y el camino más probado.
  - Al marcar el cifrado, el instalador avisa de que la contraseña se teclea al arrancar con la **distribución de teclado estadounidense** (mejor letras sin acentos ni ñ, y números) y de que sin ella los datos no se recuperan.
  - Más adelante: LUKS2 para desbloquear con TPM2 o FIDO2, cuando Calamares permita elegir el método o con una conversión desde el USB live.

### D-05 Secure Boot (**Aprobada**)

Arch no ofrece Secure Boot de serie (el `shim` firmado está en el AUR). En la 1.0 el usuario tendrá que desactivarlo, y la documentación y el instalador lo explicarán. Más adelante se estudiará `sbctl` con claves propias. Es una barrera real para quien viene de Windows 11 y se documenta como tal. En un equipo con BitLocker, cambiar Secure Boot hace que Windows pida la clave de recuperación en el siguiente arranque: se advierte antes, junto con dónde encontrarla.

### D-06 Escritorio: KDE Plasma 6 sobre Wayland (**Aprobada**)

- Valorados: **GNOME** (paradigma lejano a Windows y extensiones que se rompen en cada versión), **Cinnamon** (muy parecido a Windows, pero Wayland aún inmaduro), **COSMIC** (prometedor, aún joven), **Xfce** (sigue en X11).
- **Plasma**: distribución similar a Windows de serie (menú, barra de tareas, bandeja), configuración gráfica completa, Dolphin, buen soporte de VRR/HDR, juegos y portátiles, y temas globales (Look-and-Feel) que permiten dar identidad **sin parchear KDE**.
- Personalización únicamente con paquetes de configuración (`/etc/xdg`, `/etc/skel`, tema global). Así, una actualización de Plasma no rompe nada propio.
- Solo sesión Wayland: desde Plasma 6.8, KDE ya no ofrece sesión X11. Las aplicaciones X11 siguen funcionando mediante Xwayland.
- Gestor de inicio: **Plasma Login Manager** (oficial de KDE, en `extra`; Calamares 3.4 ya sabe configurarlo); tiene el aspecto Breeze fijo, por lo que la identidad se limita a fondo y colores. Reserva: SDDM con tema propio si el primero no convence.

### D-07 Aplicaciones: tienda y fuentes (**Aprobada**)

Requisitos:

- Una tienda gráfica para buscar, instalar, actualizar y desinstalar desde **tres fuentes**: repositorios oficiales (pacman), Flathub (Flatpak) y AUR.
- El origen de cada aplicación siempre visible, con un distintivo propio por fuente. Si una aplicación existe en varias fuentes, se muestran como opciones separadas y una de ellas aparece como recomendada.
- **AUR:** desactivado por defecto. Al activarlo, y antes de cada instalación, un aviso claro de que es software de la comunidad sin revisar, con el PKGBUILD consultable. Se compila sin root mediante un asistente (`paru`) de `[arctiva]`.
- **Integridad de pacman:** ninguna operación refresca las bases de datos sin actualizar todo el sistema. Para instalar un paquete de los repositorios con el sistema desactualizado, primero hay que actualizar.
- Permisos de Flatpak visibles y modificables. Errores comprensibles, con el texto original disponible.

Decisión: **tienda propia como módulo «Aplicaciones» de Arctiva Center** (D-09). El sistema instalado no lleva Discover, para no tener dos tiendas ni el refresco periódico de PackageKit. La ISO live usa Discover solo con Flathub hasta la fase 5.

- **Catálogo:** datos AppStream de los repositorios (`archlinux-appstream-data`) y de Flathub, leídos con libappstream. Una aplicación disponible en varias fuentes se muestra una sola vez, con una opción por fuente. El AUR solo aparece si está activado, como lista de paquetes buscada en su API RPC.
- **Fuente recomendada:** los repositorios oficiales antes que Flathub, salvo las excepciones que fija `arctiva-settings` (por ejemplo Bottles, D-12). El AUR nunca es la recomendada.
- **pacman:** las consultas se hacen con `pyalpm` sobre una copia temporal de las bases de datos, como `checkupdates`; la base real no se toca fuera de una actualización. Instalar es `pacman -Syu --needed <paquetes>` a través del ayudante polkit; si hay actualizaciones pendientes, antes se pasa por el flujo de D-08 (noticias, instantánea, paquetes delicados).
- **Flatpak:** libflatpak, o la orden `flatpak` si la prueba de concepto lo aconseja. Los permisos se gestionan abriendo `flatpak-kcm`, el módulo de Plasma que ya existe.
- **AUR:** antes de instalar se muestran el PKGBUILD y el `.install` completos, los votos, la popularidad, la última actualización y el mantenedor, con un aviso reforzado si el paquete es huérfano, ha cambiado de mantenedor o es reciente. En cada actualización, diff del PKGBUILD y del `.install` respecto a lo instalado, con confirmación: en junio de 2026 Arch avisó de una oleada de paquetes maliciosos en el AUR y recomendó revisar todos los cambios. Se compila como usuario con `paru`; solo la instalación del paquete construido pasa por el ayudante. Las actualizaciones del AUR van después de `pacman -Syu`.
- **Errores:** el mismo traductor de mensajes que D-08.
- Descartados: el motor PackageKit de Discover, por el riesgo de actualizaciones parciales (sección 2); Discover con un motor propio para pacman y AUR (no existe ninguno y la interfaz de motores de Discover no es estable, así que habría que mantener código C++ al ritmo de Plasma); Pamac (solo en el AUR, ligado a Manjaro y en GTK); Bauh (sin desarrollo desde 2024 y en Qt5), y Octopi (gestor de paquetes sin Flatpak ni AppStream).
- Antes de la fase 5, una prueba de concepto en la VM valida el catálogo, las consultas con base temporal, la instalación a través del ayudante, Flatpak y el flujo del AUR. La decisión se reconsiderará si KDE incorpora a Discover un motor para pacman.

### D-08 Actualizaciones (**Aprobada**)

En el módulo de actualizaciones de Arctiva Center:

1. Detecta actualizaciones con `checkupdates` (pacman-contrib), que usa una base de datos temporal y no provoca actualizaciones parciales.
2. Muestra las noticias de archlinux.org publicadas desde la última actualización. Si alguna exige intervención manual, el proceso se detiene hasta que el usuario la lee, con la explicación y la acción concreta.
3. Lista los paquetes y marca los delicados (kernel, controladores NVIDIA, Mesa, systemd, Plasma).
4. Actualiza con `pacman -Syu` mediante un ayudante privilegiado (polkit), mostrando el registro real. snap-pac crea la instantánea antes.
5. Actualiza los Flatpak.
6. Avisa de archivos `.pacnew` y recomienda reiniciar si cambió el kernel o los controladores.
7. Traduce los errores habituales (conflictos, claves PGP, espacio en disco) a mensajes comprensibles, sin ocultar el texto original.

Antes de escribir esta lógica se evaluará reutilizar **arch-update** (herramienta del AUR que ya hace noticias, `.pacnew` y Flatpak, mantenida por un empaquetador de Arch). Solo se programa lo que falte.

### D-09 Herramientas propias: una sola aplicación (**Aprobada**)

**Arctiva Center**, en Python 3 + PySide6 (Qt 6; ambos en los repos oficiales) y `pyalpm` para consultas de solo lectura. Módulos: bienvenida en el primer arranque, controladores, actualizaciones, extras (catálogo) y aplicaciones (la tienda, D-07). El ayudante, el traductor de errores y el flujo de actualización son comunes a todos los módulos. Las acciones privilegiadas pasan por un ayudante polkit con un **conjunto cerrado de operaciones**, nunca por órdenes arbitrarias. Es una sola aplicación en lugar de varias para reducir mantenimiento.

### D-10 Gráficas (**Aprobada**)

Detección con `lspci` y un archivo de correspondencias (familia → paquetes), compartido por el instalador y Arctiva Center.

| Gráfica | Paquetes |
|---|---|
| AMD Radeon (GCN en adelante) | `mesa`, `vulkan-radeon`, `lib32-mesa`, `lib32-vulkan-radeon` |
| Intel integradas y Arc | `mesa`, `vulkan-intel`, `intel-media-driver`, versiones `lib32` |
| NVIDIA Turing y posteriores (GTX 16, RTX 20+) | `nvidia-open` y `nvidia-open-lts` (módulos precompilados para los dos kernels), `nvidia-utils`, `lib32-nvidia-utils`, KMS temprano |
| NVIDIA Pascal/Maxwell (GTX 10/900) | Desde diciembre de 2025 el controlador 580xx solo está en el AUR. **No se instala automáticamente**: se usa `nouveau` y se avisa al usuario con las opciones |
| Portátiles híbridos | `switcheroo-control` e integración de Plasma para lanzar con la gráfica dedicada |

### D-11 Juegos (**Aprobada**)

- `multilib` activado de serie.
- Steam nativo (`steam`, de multilib), `gamemode`, `mangohud`, `gamescope`; Proton se gestiona desde Steam.
- Heroic (Epic/GOG) y ProtonPlus o ProtonUp-Qt como Flatpak; Lutris desde `extra`.
- Se instalan como perfil «Juegos» durante la instalación o desde Arctiva Center.

### D-12 Programas de Windows (**Aprobada**)

- **Bottles** como herramienta principal, **solo en Flatpak**: es el único formato que sus desarrolladores soportan.
- Al abrir un `.exe` o `.msi`, un diálogo propio explica qué va a pasar, ofrece abrirlo con Bottles y enlaza a la base de datos de compatibilidad (WineHQ AppDB, ProtonDB).
- Limitaciones que se comunican claramente: juegos con antitrampas a nivel de kernel (consultar «Are We Anti-Cheat Yet?»), suites como Adobe y Microsoft Office recientes, controladores y utilidades de hardware de Windows.
- `wine` y `winetricks` de los repos, para usuarios avanzados.

### D-13 Identidad y marca (**Aprobada**)

- Nombre: **Arctiva** (antes «Archtiva»). Ya no contiene la marca «Arch». La política de marcas de Arch permite describirlo como «basada en Arch Linux»; nunca se presentará como oficial.
- No se han encontrado distribuciones ni software con ese nombre. Existe una marca registrada «ARCTIVA» en EE. UU. en la clase 5 (productos farmacéuticos), distinta del software (clase 9). Riesgo bajo; se revisará antes de la 1.0.
- Logotipo propio y vectorial en `branding/logo/`: un arco abierto, como una puerta sin barreras, cruzado por una órbita luminosa. Tiene forma redondeada, distinta del pico del logotipo de Arch. Hay versiones a color, monocroma e icono de aplicación.
- El nombre y el logotipo no están cubiertos por la licencia del código: su uso se rige por [TRADEMARKS.es.md](../../TRADEMARKS.es.md).
- Arch no da soporte a las derivadas: Arctiva tendrá sus propios canales de ayuda y nunca enviará a los usuarios a los foros de Arch.

### D-14 Distribución de la ISO (**Aprobada**)

GitHub Releases acepta archivos de **menos de 2 GiB** cada uno, sin límite de tamaño total ni de ancho de banda. Opciones valoradas:

| Opción | Valoración |
|---|---|
| ISO completa de más de 2 GiB en GitHub | Imposible |
| Partir la ISO en trozos | Descartada: Rufus, Ventoy y Etcher necesitan un único archivo; mala experiencia para quien viene de Windows |
| ISO de red mínima que lo descarga todo | Descartada como principal: no permite probar el escritorio sin instalar y depende de la red y del estado de los mirrors |
| **ISO de menos de 2 GiB con escritorio completo y extras descargados al instalar** | **Recomendada** |
| Réplica externa (SourceForge o servidor propio) | Plan B si la ISO supera el límite; GitHub conserva las sumas de comprobación y la firma |

Para mantenerla por debajo de 2 GiB: Plasma con una selección de paquetes en lugar de todos los meta-paquetes, compresión xz del sistema de archivos, y Steam, ofimática y juegos como perfiles online en la instalación. El CI fallará si la ISO pasa de 1,9 GiB.

**Medido el 2026-11-20** (paquetes del 2026-11-19): con `linux-lts` y la documentación de los paquetes la ISO ocupaba 2,12 GiB. Sin ellos ocupa **1,75 GiB**. Lo que más pesa: el firmware (unos 500 MB que ya vienen comprimidos), Firefox, `qt6-webengine` (lo exigen Discover y las aplicaciones de KDE) y las traducciones (unos 480 MB sin comprimir, que se conservan todas). Si vuelve a acercarse al límite, el siguiente candidato es limitar las traducciones de la ISO.

### D-15 Automatización (GitHub Actions) (**Aprobada**)

1. **Lint:** shellcheck, `namcap` para los PKGBUILD y comprobación de enlaces de la documentación.
2. **Paquetes:** compilación en contenedor Arch limpio y firma.
3. **ISO:** `mkarchiso` en un contenedor `archlinux` privilegiado. El runner estándar deja unos 14 GB libres, justos para construir: si no bastan, se borran antes las herramientas preinstaladas que no se usan.
4. **Prueba de arranque:** QEMU/KVM sin pantalla con firmware UEFI (OVMF); se comprueba por consola serie que se llega al escritorio. Más adelante, instalación automatizada.
5. **Construcción semanal programada** con los paquetes del día, para detectar roturas de Arch antes que los usuarios. GitHub desactiva las tareas programadas de un repositorio público tras 60 días sin actividad: si ocurre, hay que reactivarla.
6. **Publicación** solo con una etiqueta aprobada: ISO, `sha256`, firma GPG y notas generadas desde el CHANGELOG.

### D-16 Versionado (**Aprobada**)

- El proyecto sigue SemVer `x.y.z` (archivo `VERSION`). Cada ISO publicada lleva la versión del proyecto: `arctiva-X.Y.Z-x86_64.iso`.
- Antes de la 1.0: cada fase terminada sube la versión menor; las correcciones y la documentación suben el parche.
- Desde la 1.0: mayor si obliga a migrar (por ejemplo, otro esquema de subvolúmenes), menor si añade funciones, parche si solo corrige o recompila.
- Cada paquete de `[arctiva]` tiene su propio `pkgver` en su PKGBUILD.

## 4. Qué desarrollamos y qué integramos

| Desarrollo propio (pequeño) | Integración sin código propio |
|---|---|
| Perfil archiso y scripts de construcción | Arch Linux (core, extra, multilib), pacman |
| Interfaz QML, configuración y branding de Calamares | Calamares, KDE Plasma, Discover (solo en la live), Flatpak/Flathub |
| Tienda: módulo «Aplicaciones» de Arctiva Center (D-07) | pyalpm, paru, libflatpak, AppStream, flatpak-kcm |
| `arctiva-settings` (valores por defecto) | Btrfs, Snapper, snap-pac, grub-btrfs, zram-generator |
| `arctiva-branding` (logo, fondos, Plymouth, tema global) | Mesa, NVIDIA open, Vulkan, firmware, fwupd |
| `arctiva-keyring` y el repositorio `[arctiva]` | Steam, Proton, Lutris, Heroic, Bottles, gamemode, MangoHud |
| Arctiva Center (bienvenida, controladores, actualizaciones, extras) | reflector, pacman-contrib, CUPS, ufw + plasma-firewall |
| Flujos de GitHub Actions y pruebas | arch-update (si la evaluación lo confirma) |

## 5. Riesgos principales

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Roturas de Arch (p. ej. el cambio de NVIDIA 590) | Alto | Construcción semanal en CI, noticias que bloquean, instantáneas, kernel LTS |
| Un único mantenedor | Alto | Poco código propio, todo documentado y automatizado |
| Cambios en Calamares o KDE | Medio | Solo configuración, versiones vigiladas en CI |
| Secure Boot obligatorio en algunos equipos | Medio | Documentación clara; `sbctl` más adelante |
| Windows con BitLocker en arranque dual | Alto | Avisos en el instalador y la documentación: clave de recuperación a mano, reducir la partición desde Windows, inicio rápido desactivado |
| ISO de más de 2 GiB | Medio | Selección de paquetes y réplica externa |
| Nombre y logo frente a otras marcas | Bajo | Nombre sin «Arch», logo propio, revisión antes de la 1.0 |
| Seguridad del AUR | Medio | Desactivado por defecto, separado, con avisos y con diff del PKGBUILD en cada actualización |
| Coste de construir la tienda propia | Medio | Comparte el ayudante, el traductor de errores y el flujo de D-08; prueba de concepto antes de la fase 5 |
| Claves de firma del repositorio | Alto | Clave maestra fuera de línea; subclave de firma en secretos de Actions |
| Pruebas en VirtualBox poco representativas (3D, Wayland) | Medio | Pruebas en hardware real con USB live antes de cada versión |

## 6. Requisitos de hardware

**Equipo anfitrión actual:** Intel i5-14400F (10 núcleos y 16 hilos), 16 GB de RAM, NVIDIA RTX 4060, 108 GB libres en C:. Hyper-V está activo, así que VirtualBox funciona sobre él: es más lento y sin virtualización anidada.

| Máquina | CPU | RAM | Disco | Notas |
|---|---|---|---|---|
| VM de construcción (Arch Linux) | 4–6 vCPU | 8 GB | 80 GB dinámico | EFI. Construye paquetes e ISO. La VM «Arctiva» ya está preparada con 4 vCPU, 8 GB y 80 GB (ver [desarrollo.md](desarrollo.md)) |
| VM de pruebas de la ISO | 2–4 vCPU | 4 GB | 40 GB dinámico | EFI, VMSVGA con 128 MB de vídeo. Se recrea en cada prueba |
| Hardware real | — | — | USB de 8 GB o más | La RTX 4060 del anfitrión sirve para probar NVIDIA con el USB live |
| GitHub Actions | runner estándar | 16 GB | ~14 GB libres | Suficiente para una ISO de menos de 2 GiB |

**Requisitos mínimos de Arctiva (objetivo):** x86-64 con UEFI, 4 GB de RAM (8 GB recomendados), 40 GB de disco (64 GB recomendados por las instantáneas), y gráfica con Vulkan para jugar.
