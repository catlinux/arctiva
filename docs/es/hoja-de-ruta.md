# Hoja de ruta de Arctiva

> English version: [../en/roadmap.md](../en/roadmap.md)

Cada fase tiene un objetivo verificable y cierra con una versión. Las decisiones citadas (D-xx) están en [arquitectura.md](arquitectura.md). El detalle de las tareas pendientes está en [TODO.es.md](../../TODO.es.md).

| Fase | Versión | Objetivo | Criterio de terminado |
|---|---|---|---|
| 0. Fundamentos | 0.1.x | Documentación, decisiones aprobadas, licencia, marca y entorno de construcción | Arquitectura aprobada; licencia aplicada; la VM de construcción genera la ISO `releng` oficial sin cambios |
| 1. ISO live mínima | 0.2.0 | Perfil archiso propio con Plasma en modo live | La ISO arranca en VirtualBox (UEFI) hasta el escritorio con sesión automática; se reconstruye con una fecha del Arch Linux Archive; el CI la construye y supera la prueba de arranque en QEMU; se mide su tamaño (D-14) |
| 2. Instalador | 0.3.0 | Calamares a medida con instalación offline (D-03) | Interfaz QML propia aprobada; instalación completa sin terminal en una VM: idioma, teclado, zona horaria, usuario, particionado automático y manual, Btrfs + Snapper + GRUB con instantáneas arrancables, `linux` y `linux-lts`; instalación junto a Windows probada |
| 3. Repositorio propio y hardware | 0.4.0 | `[arctiva]` firmado y detección de gráficas | Repositorio publicado y firmado con `arctiva-keyring`; `arctiva-settings` y `arctiva-branding` provisional; detección de gráficas en el instalador; perfil «Juegos» con multilib |
| 4. Arctiva Center | 0.5.0 | Bienvenida, controladores, actualizaciones y extras | Flujo de actualización completo (D-08) probado con un caso de noticia que exige intervención; catálogo de extras; evaluación de arch-update documentada |
| 5. Identidad y escritorio | 0.6.0 | Imagen propia y escritorio sencillo, parecido a Windows | Logo vectorial aprobado; tema gráfico de GRUB (siempre visible), pantalla de arranque Plymouth, inicio de sesión, tema global con disposición tipo Windows, fondos y branding de Calamares; módulo «Personalización» con los ajustes básicos y «Restaurar el aspecto de Arctiva»; límites de las instantáneas |
| 6. Aplicaciones y Windows | 0.7.0 | Tienda y compatibilidad | Tienda propia en Arctiva Center (D-07), con repositorios, Flathub y AUR diferenciados; Bottles y diálogo para `.exe`; probado en máquinas virtuales |
| 7. Beta | 0.8.0–0.9.x | Calidad y publicación | Matriz de pruebas en hardware real; documentación de usuario; flujo de publicación con firma y réplica; beta pública |
| Estable | 1.0.0 | Primera versión estable | Sin errores bloqueantes abiertos; proceso de publicación mensual documentado |

## Plan detallado

Estado de cada trabajo: `[x]` hecho (con la versión en que se cerró) y `[ ]` pendiente. Lo pendiente más inmediato, por prioridad, está en [TODO.es.md](../../TODO.es.md).

### Fase 0: fundamentos (0.1.x) — terminada

- [x] Análisis de viabilidad, arquitectura (D-01…D-16) y documentación inicial bilingüe (0.1.0)
- [x] Licencia GPL-3.0-or-later y política de marca en `TRADEMARKS` (0.1.2)
- [x] Nombre Arctiva y logotipo vectorial a color, monocromo e icono (0.1.1–0.1.3)
- [x] VM de construcción con Arch y `archiso`; la ISO `releng` oficial se construye y arranca (0.1.4)
- [x] Aprobación de todas las decisiones de arquitectura (0.1.5–0.1.6)
- [x] Hacer público el repositorio (0.3.11)

### Estudios previos

- [x] E1: tienda y fuentes de aplicaciones; tienda propia en Arctiva Center (D-07) (0.1.6)
- [x] E2: diseño del instalador, cifrado y avisos de Windows (D-03, D-04) (0.1.7)
- [ ] Prueba de concepto de la tienda en la VM (antes de la fase 6)
- [ ] Comprobaciones del instalador en la VM (antes de la fase 2): módulos QML de Calamares, lectura del resultado del lanzador, cifrado con una contraseña, instantánea con raíz cifrada, `os-prober`, alcance de `stylesheet.qss`

### Fase 1: ISO live mínima (0.2.0) — terminada

- [x] Perfil archiso `iso/` derivado de `releng`, arranque solo UEFI (0.2.0)
- [x] Plasma con sesión automática del usuario `live` y entrada «safe graphics» (0.2.0)
- [x] `build.sh` reproducible con fecha del Arch Linux Archive (0.2.0)
- [x] Tamaño medido: 1,75 GiB, por debajo del límite de 1,9 GiB (D-14) (0.2.0)
- [x] Flujo de CI con construcción y prueba de arranque en QEMU (0.2.0)
- [x] Construcción con Docker en cualquier Linux (0.2.0)
- [x] `tests/run-live.sh`: arrancar y ver la ISO en el navegador desde otro equipo (0.2.0)

### Fase 2: instalador (0.3.0)

- [x] Paquetes `calamares` 3.4.3 y `ckbcomp`, y repositorio local para la ISO (0.2.1)
- [x] Configuración base: particionado automático y manual, Btrfs con subvolúmenes, LUKS1 opcional con una sola contraseña, GRUB, Snapper con instantáneas arrancables (0.2.2)
- [x] Copia del kernel al sistema instalado, limpieza de lo exclusivo de la live y `linux-lts` si hay red (0.2.2)
- [x] Lanzador y página «Comprobación» (BitLocker, inicio rápido de Windows) (0.2.3)
- [x] Interfaz QML con la identidad de Arctiva y aprobación de las maquetas (0.2.4–0.2.6)
- [x] Perfiles Básico, Juegos y Oficina (0.2.7–0.2.8)
- [x] Pruebas en máquinas virtuales: instalación sin terminal, junto a Windows simulado, cifrada, particionado manual (0.3.0)

### Fase 3: repositorio propio y hardware (0.4.0) — terminada

- [x] Clave de firma (maestra fuera de línea, subclave en el CI) y paquete `arctiva-keyring` (0.3.6)
- [x] Repositorio `[arctiva]` firmado y publicado, con compilación de paquetes en el CI (0.3.9)
- [x] `arctiva-settings` (valores por defecto, zram, multilib, reflector) y `arctiva-branding` provisional
- [x] Detección de gráficas (D-10) en el instalador (0.3.2), compartida con Arctiva Center (0.3.14)
- [x] Perfil «Juegos» completo con multilib (D-11) (0.3.2: `lib32-nvidia-utils` con Steam)
- [x] El sistema instalado usa `[arctiva]`; instalación completa probada en QEMU (0.4.0)

### Fase 4: Arctiva Center (0.5.0) — terminada

- [x] Aplicación base PySide6 y ayudante polkit con operaciones cerradas (0.3.11)
- [x] Bienvenida en el primer arranque (0.3.16)
- [x] Controladores (0.3.14)
- [x] Actualizaciones (D-08): noticias que bloquean, paquetes delicados, `.pacnew`, errores traducidos (0.3.12)
- [x] Evaluación de arch-update documentada
- [x] Catálogo de extras (0.3.15)
- [x] GRUB reinstalado en la partición EFI al actualizar el paquete `grub` (0.3.17)

### Fase 5: identidad y escritorio (0.6.0)

- [x] Logotipo vectorial aprobado (0.1.6)
- [x] Tipografía corporativa y lema del logotipo en trazos (0.5.3)
- [x] Tema gráfico de GRUB, siempre visible, Plymouth, pantalla de inicio de sesión, tema global y fondos (0.5.4–0.5.9); la ISO live sigue con systemd-boot (ver el TODO)
- [x] Escritorio tipo Windows: barra abajo con iconos centrados, menú de inicio con buscador; en Plasma 6 el panel solo se mueve en el modo de edición (0.5.5)
- [x] Módulo «Personalización» en Arctiva Center (claro/oscuro, acento, fondo, alineación de la barra, escala, luz nocturna) y «Restaurar el aspecto de Arctiva»
- [x] Límites de las instantáneas y su espacio visible en Arctiva Center
- [x] Branding de Calamares y de Arctiva Center (tipografía, presentación)

### Fase 6: aplicaciones y Windows (0.7.0)

- [x] Tienda: catálogo, búsqueda y página «Aplicaciones» para Arch y Flathub (0.6.2–0.6.4)
- [x] AUR en la tienda (0.6.5)
- [x] Bottles y diálogo para abrir `.exe` y `.msi`; extras Heroic y ProtonPlus (0.6.6)

- [ ] Tienda «Aplicaciones» con repositorios, Flathub y AUR diferenciados (D-07)
- [ ] Bottles y diálogo para abrir `.exe` y `.msi` (D-12)
- [x] Quitar Discover de la ISO live (0.6.7)

### Fase 7: beta (0.8.0–0.9.x)

- [ ] Steam, Proton y Heroic probados en hardware real con NVIDIA y con AMD o Intel
- [ ] Matriz de pruebas en hardware real, cuando todo esté implementado: USB en el PC (NVIDIA RTX 4060) y portátil con Windows y Manjaro (sustituir Manjaro por Arctiva conservando Windows y su partición EFI)
- [ ] Documentación de usuario
- [ ] Publicación firmada (ISO, `sha256`, firma GPG) con réplica externa
- [ ] Beta pública y canales de ayuda propios

### Estable (1.0.0)

- [ ] Sin errores bloqueantes abiertos
- [ ] Proceso de publicación mensual documentado
- [ ] Revisión de la marca «Arctiva» antes de publicar

## Principios de trabajo

- Una fase no empieza hasta que la anterior cumple su criterio de terminado.
- Todo cambio de comportamiento lleva versión, CHANGELOG y documentación actualizados en el mismo commit.
- La construcción y las pruebas de ISO se hacen en máquinas virtuales o en GitHub Actions, nunca en el equipo principal.
