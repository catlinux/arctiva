# SPDX-License-Identifier: GPL-3.0-or-later
"""Proton de serie: consulta, descarga comprobada, instalación sin medias tintas, limpieza y espera entre
comprobaciones."""
import hashlib
import io
import json
import tarfile

import pytest

from arctiva_games.core import games_protondl as pd

GE_TAG, GE_DIR = "GE-Proton11-14", "GE-Proton11-14-x86_64"
WL_TAG, WL_DIR = "wineland-11.0-20261119", "proton-wineland-11.0-20261119-x86_64"


def make_tar(members, mode="w:gz"):
    """members: {ruta: contenido} o {ruta: ("symlink", destino)}."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode=mode) as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            if isinstance(data, tuple):
                info.type, info.linkname = tarfile.SYMTYPE, data[1]
                tar.addfile(info)
            else:
                raw = data.encode()
                info.size, info.mode = len(raw), 0o755
                tar.addfile(info, io.BytesIO(raw))
    return buf.getvalue()


class Resp(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}


def opener_for(files):
    def opener(url):
        if url not in files:
            raise OSError(f"404 {url}")
        return Resp(files[url])
    return opener


def release_files(tar_bytes, source=pd.GE, tag=GE_TAG, base=GE_DIR, sha=None):
    sha = sha if sha is not None else hashlib.sha512(tar_bytes).hexdigest()
    api = {"tag_name": tag, "assets": [
        {"name": "otra-cosa-aarch64" + source.ext, "browser_download_url": "https://x/arm", "size": 1},
        {"name": base + source.ext, "browser_download_url": "https://x/t", "size": len(tar_bytes)},
        {"name": base + ".sha512sum", "browser_download_url": "https://x/t.sha512sum"}]}
    return {source.api: json.dumps(api).encode(), "https://x/t": tar_bytes,
            "https://x/t.sha512sum": f"{sha}  {base}{source.ext}\n".encode()}


def ge_ok(folder=GE_DIR):
    return {f"{folder}/proton": "#!/bin/sh\n", f"{folder}/files/bin/wineserver": "x",
            f"{folder}/files/lib": ("symlink", "bin")}


def ensure(tmp_path, files, **kw):
    kw.setdefault("source", pd.GE)
    return pd.ensure(tmp_path / "dest", opener=opener_for(files), state=tmp_path / "state.json", **kw)


def test_ge_instala_la_ultima_comprobada(tmp_path):
    files = release_files(make_tar(ge_ok()))
    seen = []
    assert ensure(tmp_path, files, progress=lambda d, t: seen.append((d, t))) == (GE_DIR, True)
    dest = tmp_path / "dest"
    assert (dest / GE_DIR / "proton").is_file() and (dest / GE_DIR / pd.MARK).is_file()
    assert seen and seen[-1][0] == seen[-1][1]
    assert [p.name for p in dest.iterdir()] == [GE_DIR]                    # sin carpetas temporales
    assert ensure(tmp_path, files, force=True) == (GE_DIR, False)           # ya estaba: no descarga


def test_ge_formato_antiguo_sin_arquitectura(tmp_path):
    files = release_files(make_tar(ge_ok("GE-Proton10-25")), tag="GE-Proton10-25", base="GE-Proton10-25")
    assert ensure(tmp_path, files) == ("GE-Proton10-25", True)


def test_wineland_es_el_de_serie_y_va_en_tar_xz(tmp_path):
    assert pd.DEFAULT is pd.WINELAND
    files = release_files(make_tar({f"{WL_DIR}/proton": "x"}, mode="w:xz"), source=pd.WINELAND, tag=WL_TAG, base=WL_DIR)
    assert ensure(tmp_path, files, source=pd.WINELAND) == (WL_DIR, True)
    assert (tmp_path / "dest" / WL_DIR / "proton").is_file()


def test_solo_comprueba_una_vez_por_semana(tmp_path):
    files = release_files(make_tar(ge_ok()))
    assert ensure(tmp_path, files, now=1000) == (GE_DIR, True)
    offline = {}                                                             # sin red
    assert ensure(tmp_path, offline, now=1000 + 3600) == (GE_DIR, False)     # no consulta: aún no toca
    with pytest.raises(pd.ProtonError, match="consultar"):
        ensure(tmp_path, offline, now=1000 + pd.CHECK_EVERY + 1)             # ya toca: consulta y falla


def test_suma_mala_no_deja_nada(tmp_path):
    files = release_files(make_tar(ge_ok()), sha="0" * 128)
    with pytest.raises(pd.ProtonError, match="SHA-512"):
        ensure(tmp_path, files)
    assert list((tmp_path / "dest").iterdir()) == []


def test_enlace_absoluto_se_acepta_pero_no_se_escribe_a_traves(tmp_path):
    # Proton-Wineland trae files/share/mesa/drirc.d/99-system.conf → /usr/share/drirc.d/…: se deja tal cual.
    ok = {f"{GE_DIR}/proton": "y", f"{GE_DIR}/sistema.conf": ("symlink", "/usr/share/drirc.d/00-mesa.conf")}
    assert ensure(tmp_path, release_files(make_tar(ok)))[1] is True
    link = tmp_path / "dest" / GE_DIR / "sistema.conf"
    assert link.is_symlink() and str(link.readlink()) == "/usr/share/drirc.d/00-mesa.conf"


def test_no_se_escribe_a_traves_de_un_enlace_absoluto(tmp_path):
    victim = tmp_path / "victima"
    victim.mkdir()
    bad = {f"{GE_DIR}/proton": "y", f"{GE_DIR}/puerta": ("symlink", str(victim)), f"{GE_DIR}/puerta/malo": "x"}
    with pytest.raises(pd.ProtonError):
        ensure(tmp_path, release_files(make_tar(bad)))
    assert list(victim.iterdir()) == []
    assert [p.name for p in (tmp_path / "dest").iterdir()] == []


def test_rechaza_rutas_que_salen_de_la_carpeta(tmp_path):
    for bad in ({"../fuera": "x", f"{GE_DIR}/proton": "y"}, {"/abs/proton": "x"},
                {f"{GE_DIR}/proton": "y", f"{GE_DIR}/enlace": ("symlink", "../../../fuera")}):
        files = release_files(make_tar(bad))
        with pytest.raises(pd.ProtonError):
            ensure(tmp_path, files)
        assert not (tmp_path / "fuera").exists()
        assert [p.name for p in (tmp_path / "dest").iterdir()] == []


def test_estructura_inesperada(tmp_path):
    files = release_files(make_tar({"otra-cosa/proton": "x"}))
    with pytest.raises(pd.ProtonError, match="estructura"):
        ensure(tmp_path, files)


def test_respuestas_raras(tmp_path):
    files = {pd.GE.api: json.dumps({"tag_name": "algo raro", "assets": []}).encode()}
    with pytest.raises(pd.ProtonError, match="inesperada"):
        pd.latest(pd.GE, opener_for(files))
    files = {pd.GE.api: json.dumps({"tag_name": GE_TAG, "assets": []}).encode()}
    with pytest.raises(pd.ProtonError, match="no trae"):
        pd.latest(pd.GE, opener_for(files))


def test_limpieza_solo_lo_suyo_de_esa_fuente_y_sin_uso(tmp_path):
    def version(name, mine=True):
        d = tmp_path / name
        d.mkdir()
        (d / "proton").write_text("x")
        if mine:
            (d / pd.MARK).write_text(name)
        return d
    old, used, newest = version("GE-Proton9-20"), version("GE-Proton10-3"), version("GE-Proton11-14-x86_64")
    users = version("GE-Proton8-1", mine=False)                              # puesta por el usuario
    wineland = version("proton-wineland-11.0-20261101-x86_64")               # otra fuente: no se toca
    assert pd.cleanup(tmp_path, keep=[str(used)], source=pd.GE) == ["GE-Proton9-20"]
    assert not old.exists() and used.exists() and newest.exists() and users.exists() and wineland.exists()
