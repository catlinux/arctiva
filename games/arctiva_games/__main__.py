# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="arctiva-games")
    parser.add_argument("--play", metavar="JUEGO", help="lanza un juego instalado sin abrir la ventana")
    args = parser.parse_args(argv)
    if args.play:
        from .core import games_launch
        return games_launch.run(args.play)
    from .app import run  # PySide6 solo se importa si hay ventana.
    return run()


if __name__ == "__main__":
    sys.exit(main())
