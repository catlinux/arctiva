# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import sys

from .modules import MODULES


def build_parser():
    parser = argparse.ArgumentParser(prog="arctiva-center")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--welcome", action="store_true",
                       help="abre la bienvenida del primer inicio de sesión")
    group.add_argument("--check", action="store_true",
                       help="busca actualizaciones sin abrir ventana (aviso periódico)")
    group.add_argument("--module", choices=MODULES, help="abre la ventana en ese módulo")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.check:
        return 0  # Se implementa con el módulo de actualizaciones.
    module = "welcome" if args.welcome else (args.module or "welcome")
    from .app import run  # PySide6 solo se importa si hay ventana.
    return run(module)


if __name__ == "__main__":
    sys.exit(main())
