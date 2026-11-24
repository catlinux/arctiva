# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="arctiva-games")
    parser.add_argument("--play", metavar="JUEGO", help="lanza un juego instalado sin abrir la ventana")
    parser.add_argument("--install-proton", action="store_true",
                        help="instala o actualiza el Proton de serie (Proton-Wineland) sin abrir la ventana (lo usa Arctiva Center)")
    args = parser.parse_args(argv)
    if args.install_proton:
        return install_proton()
    if args.play:
        from .core import games_launch
        return games_launch.run(args.play)
    from .app import run  # PySide6 solo se importa si hay ventana.
    return run()


def install_proton():
    import shutil
    import subprocess
    from .core import games_library, games_protondl
    keep = [g.runner for g in games_library.list_games() if g.runner != "wine"]
    shown = [-1]

    def progress(done, total):
        pct = done * 100 // total if total else 0
        if pct != shown[0] and pct % 5 == 0:
            shown[0] = pct
            print(f"Proton: {pct} %", flush=True)
    try:
        tag, fresh = games_protondl.ensure(progress=progress, keep=keep)
    except games_protondl.ProtonError as e:
        print(f"arctiva-games: {e}", file=sys.stderr)
        return 1
    print(f"{tag}: {'instalado' if fresh else 'ya estaba instalado'}")
    if fresh and shutil.which("notify-send"):
        subprocess.run(["notify-send", "--app-name=Arctiva Games", "--icon=arctiva-games", "Arctiva Games",
                        f"{tag} está listo para jugar."], check=False, capture_output=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
