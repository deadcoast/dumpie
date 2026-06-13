"""Allow ``python -m dumpie`` to launch the CLI."""

from __future__ import annotations

import sys

from .cli import main
from .ui import console

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[muted]aborted[/muted]")
        sys.exit(130)
