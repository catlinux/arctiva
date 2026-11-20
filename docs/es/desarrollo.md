# Guía de desarrollo

> English version: [../en/development.md](../en/development.md)

## Entorno

- **Equipo de trabajo:** Windows 11 con Visual Studio Code y Git. Aquí se edita y se gestiona el repositorio; no se construye nada.
- **VM de construcción:** Arch Linux en VirtualBox (EFI, 4–6 vCPU, 8 GB de RAM, disco dinámico de 80 GB). Construye paquetes e ISO con `archiso`.
- **VM de pruebas:** se crea de nuevo para cada ISO (EFI, 2–4 vCPU, 4 GB, 40 GB, VMSVGA con 128 MB).
- **CI:** GitHub Actions construye y prueba en limpio (ver D-15 en [arquitectura.md](arquitectura.md)).

Los pasos detallados para preparar las VM se documentarán al completar la fase 0, una vez comprobados.

> Hyper-V está activo en el equipo anfitrión, así que VirtualBox funciona sobre él: es más lento y sin virtualización anidada. Las pruebas con QEMU/KVM se hacen en el CI o dentro de la VM de construcción si el rendimiento lo permite.

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
