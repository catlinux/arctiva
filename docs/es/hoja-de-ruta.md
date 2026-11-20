# Hoja de ruta de Archtiva

> English version: [../en/roadmap.md](../en/roadmap.md)

Cada fase tiene un objetivo verificable y cierra con una versión. Las decisiones citadas (D-xx) están en [arquitectura.md](arquitectura.md). El detalle de las tareas pendientes está en [TODO.es.md](../../TODO.es.md).

| Fase | Versión | Objetivo | Criterio de terminado |
|---|---|---|---|
| 0. Fundamentos | 0.1.x | Documentación, decisiones aprobadas, licencia, marca y entorno de construcción | Arquitectura aprobada; licencia aplicada; la VM de construcción genera la ISO `releng` oficial sin cambios |
| 1. ISO live mínima | 0.2.0 | Perfil archiso propio con Plasma en modo live | La ISO arranca en VirtualBox (UEFI) hasta el escritorio con sesión automática; se reconstruye con una fecha del Arch Linux Archive; el CI la construye y supera la prueba de arranque en QEMU; se mide su tamaño (D-14) |
| 2. Instalador | 0.3.0 | Calamares con instalación offline | Instalación completa sin terminal en una VM: idioma, teclado, zona horaria, usuario, particionado automático y manual, Btrfs + Snapper + GRUB con instantáneas arrancables, `linux` y `linux-lts`; instalación junto a Windows probada |
| 3. Repositorio propio y hardware | 0.4.0 | `[archtiva]` firmado y detección de gráficas | Repositorio publicado y firmado con `archtiva-keyring`; `archtiva-settings` y `archtiva-branding` provisional; detección de gráficas en el instalador; perfil «Juegos» con multilib |
| 4. Archtiva Center | 0.5.0 | Bienvenida, controladores, actualizaciones y extras | Flujo de actualización completo (D-08) probado con un caso de noticia que exige intervención; catálogo de extras; evaluación de arch-update documentada |
| 5. Aplicaciones y Windows | 0.6.0 | Tienda y compatibilidad | Discover con Flathub; Bottles y diálogo para `.exe`; Steam, Proton y Heroic funcionando en hardware real con NVIDIA y AMD o Intel |
| 6. Identidad | 0.7.0 | Imagen propia y coherente | Logo vectorial aprobado; pantalla de arranque Plymouth, inicio de sesión, tema global, fondos y branding de Calamares |
| 7. Beta | 0.8.0–0.9.x | Calidad y publicación | Matriz de pruebas en hardware real; documentación de usuario; flujo de publicación con firma y réplica; beta pública |
| Estable | 1.0.0 | Primera versión estable | Sin errores bloqueantes abiertos; proceso de publicación mensual documentado |

## Principios de trabajo

- Una fase no empieza hasta que la anterior cumple su criterio de terminado.
- Todo cambio de comportamiento lleva versión, CHANGELOG y documentación actualizados en el mismo commit.
- La construcción y las pruebas de ISO se hacen en máquinas virtuales o en GitHub Actions, nunca en el equipo principal.
