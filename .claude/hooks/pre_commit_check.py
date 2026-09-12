"""pre_commit_check — Claude Code 的 PreToolUse hook：在 git commit 前跑 doctor --quick。

## 為什麼需要這支
AGENTS.md 硬性規則 6「STATUS、README、CHANGELOG 沒同步不算收關」如果只是文字，代理人在上下文壓縮後就會忘。
這支把它變成強制點：doctor 有阻斷項時 commit 進不去。

## 做什麼
1. 從 stdin 讀 Claude Code 傳來的 JSON，取 tool_input.command。
2. 不是 git commit 就放行（settings.json 的 if 已先過濾一次，這裡是第二道，見 limits L05）。
3. ANVIL_SKIP_DOCTOR=1 時印提示放行（逃生口；用了要在 commit 訊息說明原因）。
4. 跑 `python tools/doctor.py --quick --root <專案根>`；非零就把輸出寫到 stderr 並 exit 2。

## 安全設計
只讀。不改檔、不改 git 狀態。找不到 doctor.py 時放行並警告（不讓 hook 本身壞掉擋住所有 commit）。
專案根取 CLAUDE_PROJECT_DIR，沒有就用目前目錄。

## 退出碼
0 = 放行；2 = 阻斷（Claude Code 會把 stderr 回饋給 Claude）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows 管線預設 cp950，會讓中文輸出解碼失敗
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    try:
        data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, OSError):
        data = {}
    command = str((data.get("tool_input") or {}).get("command", ""))
    if "git commit" not in command:
        return 0
    if os.environ.get("ANVIL_SKIP_DOCTOR") == "1":
        print("[anvil] ANVIL_SKIP_DOCTOR=1，略過 doctor；請在 commit 訊息說明原因。", file=sys.stderr)
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    doctor = os.path.join(root, "tools", "doctor.py")
    if not os.path.exists(doctor):
        print(f"[anvil] 找不到 {doctor}，放行。", file=sys.stderr)
        return 0
    # --changes all：hook 觸發時 `git add -A && git commit` 還沒 stage，所以看整個工作樹的變更
    r = subprocess.run(
        [sys.executable, doctor, "--quick", "--changes", "all", "--root", root],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        sys.stderr.write(
            "[anvil] doctor 有阻斷項，這次 commit 被擋下。修好再 commit；"
            "真的要略過就設 ANVIL_SKIP_DOCTOR=1 並在訊息說明。\n\n"
        )
        sys.stderr.write(r.stdout)
        sys.stderr.write(r.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
