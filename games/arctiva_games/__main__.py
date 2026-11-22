# SPDX-License-Identifier: GPL-3.0-or-later
import sys


def main():
    from .app import run  # PySide6 solo se importa si hay ventana.
    return run()


if __name__ == "__main__":
    sys.exit(main())
