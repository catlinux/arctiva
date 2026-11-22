# Publicar una versión de Arctiva

> English version: [../en/releasing.md](../en/releasing.md)

La ISO se publica con el flujo `.github/workflows/release.yml`, que se dispara al subir una etiqueta `vX.Y.Z`. Las etiquetas las crea el mantenedor.

## Antes de etiquetar

1. `VERSION` y la sección `## [X.Y.Z]` de `CHANGELOG.md` (y `CHANGELOG.es.md`) tienen que coincidir con la etiqueta: el flujo lo comprueba y falla si no.
2. El flujo «ISO» del CI está en verde con el mismo commit (con la fecha de `iso/archive-date`; si el Archive de Arch no respondía, esa construcción usó los mirrors actuales y **no** vale: repetir cuando responda).
3. La ISO se ha probado en hardware real (ver `docs/es/pruebas.md` cuando exista).
4. Para una versión de prueba (0.x) el flujo marca la release como *prerelease*.

## Qué hace el flujo

1. Comprueba etiqueta, `VERSION` y CHANGELOG.
2. Construye la ISO con la fecha fija del Archive de `iso/archive-date`. **No hay alternativa:** si el Archive no responde, falla (una ISO publicada tiene que poder reconstruirse igual).
3. Prueba de arranque en QEMU (UEFI).
4. Firma la ISO con la subclave del repositorio (secretos `ARCTIVA_SIGNING_KEY` y `ARCTIVA_SIGNING_PASSPHRASE`, ver [firma.md](firma.md)): firma separada `.sig`, sin dejar la clave en disco.
5. Verifica la suma y la firma con la clave pública del repositorio.
6. Crea la release con la ISO, `.sha256`, `.sig` y las notas (la sección de esa versión del CHANGELOG).

## Verificar una descarga

```
sha256sum -c arctiva-X.Y.Z-x86_64.iso.sha256
gpg --import arctiva.gpg                        # clave pública: packages/arctiva-keyring/arctiva.gpg
gpg --verify arctiva-X.Y.Z-x86_64.iso.sig arctiva-X.Y.Z-x86_64.iso
```

La huella de la clave está en [firma.md](firma.md); compárala antes de fiarte de la firma.

## Después de publicar

- Actualizar las Q&A de Discussions que citen la versión o digan «no hay ISO» (`.agents/plans/discussions/qa-discussions.md`) y avisar a la web.
- Probar la ISO publicada: descargar, verificar y arrancar en una máquina virtual.
