"""確保敏感檔與產出夾不會被 git 追蹤——「靠約定擋住」的防線要有測試看著。"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SENSITIVE = [".env", ".env.*", "credentials.json", "token.json", "cookie.txt", "*.db", "*.sqlite"]
OUTPUT_DIRS = ("output/", "out/", ".pytest_tmp/", "__pycache__/")


def _tracked() -> list[str] | None:
    try:
        r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError:
        return None
    return r.stdout.splitlines() if r.returncode == 0 else None


def test_gitignore_lists_sensitive_patterns():
    lines = {ln.strip() for ln in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
    missing = [g for g in SENSITIVE if g not in lines]
    assert not missing, f".gitignore 缺：{missing}"
    assert all(d in lines for d in OUTPUT_DIRS), ".gitignore 缺產出夾"


def test_no_sensitive_file_is_tracked():
    tracked = _tracked()
    if tracked is None:
        pytest.skip("不是 git repo 或沒有 git")
    leaked = [
        f for f in tracked
        if not f.endswith(".example") and any(fnmatch.fnmatch(f.rsplit("/", 1)[-1], g) for g in SENSITIVE)
    ]
    assert not leaked, f"敏感檔被追蹤：{leaked}"
    assert not [f for f in tracked if f.startswith(("output/", "out/", ".pytest_tmp/"))]
