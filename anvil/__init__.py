"""Anvil 樣板的佔位套件。

開新專案時把這個目錄改名成你的套件名，並同步改 pyproject.toml 的
[tool.setuptools].packages 與 [tool.anvil].package。
版本號的單一事實來源是 pyproject.toml 的 version，這裡的 __version__ 必須與它一致
（tools/doctor.py 會檢查）。
"""

__version__ = "0.1.0"
