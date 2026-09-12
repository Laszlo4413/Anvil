"""install_git_hooks — 安裝 git 原生 pre-commit，讓 doctor 在 Claude Code 之外的任何工具 commit 時也會跑。

## 為什麼需要這支
`.claude/hooks/pre_commit_check.py` 只在 Claude Code 內觸發；用終端、Codex、IDE 直接 `git commit` 時
doctor 不會跑（limits L01）。多工具或多代理人協作的專案需要一個跟工具無關的強制點，
git 自己的 pre-commit hook 就是。這支把同一支 doctor 掛進 `.git/hooks/pre-commit`。

## 做什麼
1. 找到專案的 `.git/hooks/`（支援 worktree：用 `git rev-parse --git-path hooks`）。
2. 寫入一個 sh 腳本：`ANVIL_SKIP_DOCTOR=1` 放行，否則跑 `python tools/doctor.py --quick --changes staged`，
   非零就擋下 commit。
3. 既有的 pre-commit 先備份成 `pre-commit.bak`，不覆蓋。

## 安全設計
預設**乾跑**：只印出會寫到哪、內容是什麼。加 `--apply` 才真的寫。`--uninstall` 移除（若有 .bak 則還原）。
hook 檔不進版控（.git/ 內），所以 clone 後要重跑一次；TEMPLATE_README 的開新專案步驟有寫。

## 退出碼
0 = 成功或乾跑；1 = 不在 git repo 內、或 hooks 目錄不可寫。
用法：python tools/install_git_hooks.py [--apply] [--uninstall]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HOOK_BODY = """#!/bin/sh
# Anvil pre-commit（由 tools/install_git_hooks.py 安裝；重新安裝會覆蓋本檔）
if [ "$ANVIL_SKIP_DOCTOR" = "1" ]; then
  echo "[anvil] ANVIL_SKIP_DOCTOR=1，略過 doctor；請在 commit 訊息說明原因。" >&2
  exit 0
fi
ROOT="$(git rev-parse --show-toplevel)"
python "$ROOT/tools/doctor.py" --quick --changes staged --root "$ROOT"
STATUS=$?
if [ $STATUS -ne 0 ]; then
  echo "[anvil] doctor 有阻斷項，commit 被擋下。修好再 commit；真的要略過就設 ANVIL_SKIP_DOCTOR=1 並在訊息說明。" >&2
  exit 1
fi
exit 0
"""
MARKER = "Anvil pre-commit"


def hooks_dir(root: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"], cwd=root, capture_output=True, text=True, encoding="utf-8"
        )
    except FileNotFoundError:
        return None
    if out.returncode != 0:
        return None
    p = Path(out.stdout.strip())
    return p if p.is_absolute() else (root / p)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="安裝／移除 Anvil 的 git 原生 pre-commit hook（預設乾跑）")
    ap.add_argument("--apply", action="store_true", help="真的寫入")
    ap.add_argument("--uninstall", action="store_true", help="移除 Anvil 的 hook（有 .bak 則還原）")
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    hd = hooks_dir(root)
    if hd is None:
        print("✗ 不在 git repo 內（或沒有 git）", file=sys.stderr)
        return 1
    target = hd / "pre-commit"
    backup = hd / "pre-commit.bak"

    if args.uninstall:
        if not target.exists() or MARKER not in target.read_text(encoding="utf-8", errors="replace"):
            print(f"沒有 Anvil 的 hook 可移除：{target}")
            return 0
        if not args.apply:
            print(f"[乾跑] 會移除 {target}" + (f" 並還原 {backup}" if backup.exists() else ""))
            return 0
        target.unlink()
        if backup.exists():
            backup.rename(target)
            print(f"✓ 已移除並還原備份：{target}")
        else:
            print(f"✓ 已移除：{target}")
        return 0

    existing = target.read_text(encoding="utf-8", errors="replace") if target.exists() else None
    if not args.apply:
        print(f"[乾跑] 會寫入 {target}")
        if existing is not None and MARKER not in existing:
            print(f"[乾跑] 既有 hook 會先備份成 {backup}")
        print("---- hook 內容 ----")
        print(HOOK_BODY)
        print("加 --apply 才會真的寫。")
        return 0
    try:
        hd.mkdir(parents=True, exist_ok=True)
        if existing is not None and MARKER not in existing:
            backup.write_text(existing, encoding="utf-8", newline="\n")
            print(f"既有 hook 已備份：{backup}")
        target.write_text(HOOK_BODY, encoding="utf-8", newline="\n")
        try:
            target.chmod(target.stat().st_mode | 0o111)
        except OSError:
            pass
    except OSError as e:
        print(f"✗ 寫入失敗：{e}", file=sys.stderr)
        return 1
    print(f"✓ 已安裝：{target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
