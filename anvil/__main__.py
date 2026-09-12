"""python -m anvil：佔位進入點，只印版本。

依 docs/python_profile.md §4，正式專案在這裡做「無參數開 GUI、有參數走 CLI」的分派。
"""

from __future__ import annotations

import sys

from anvil import __version__


def main() -> int:
    print(f"anvil {__version__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
