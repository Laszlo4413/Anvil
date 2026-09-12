"""_example — 延伸層檢查的範例（檔名以 _ 開頭，doctor 不會載入；複製並改名後才生效）。

## 為什麼需要這支
基礎層的 doctor 不知道你的專案有什麼特殊結構（例如 XivForge 的 engines/ 版本夾）。
延伸層把自己的檢查放在 tools/doctor_ext/<name>.py，實作 run(ctx)，doctor 會自動載入並把結果併進同一份報告，
不用改基礎層的檢查。

## 檢查什麼
本範例示範一個典型需求：「導航／狀態文件提到的最大版本號，不能落後目錄裡實際存在的最大版本」。
這正是上一輪專案兩份索引文件靜默過期的模式。

## 安全設計
只讀。ctx 提供 root、cfg、docs、git(*args)（唯讀）。回傳 [(level, message), ...]，
level 用 "BLOCK" / "WARN" / "OK"。丟出例外只會被記成警告，不會擋住基礎檢查。

## 退出碼
本檔沒有自己的退出碼；結果併入 doctor（0 = 無阻斷，1 = 有阻斷）。
"""

from __future__ import annotations

import re


def run(ctx):  # noqa: ANN001 — ctx 是 tools/doctor.py 的 Ctx
    """比對 <root>/engines/README.md 提到的最大 Vn 與 engines/**/V* 目錄的最大 n。"""
    engines = ctx.root / "engines"
    if not engines.is_dir():
        return [("OK", "沒有 engines/，略過")]
    actual = 0
    for d in engines.rglob("V*"):
        m = re.fullmatch(r"V(\d+)", d.name)
        if d.is_dir() and m:
            actual = max(actual, int(m.group(1)))
    readme = engines / "README.md"
    if not readme.exists():
        return [("WARN", "engines/ 沒有 README.md")]
    mentioned = [int(n) for n in re.findall(r"\bV(\d+)\b", readme.read_text(encoding="utf-8"))]
    top = max(mentioned) if mentioned else 0
    if top < actual:
        return [("BLOCK", f"engines/README.md 最高只提到 V{top}，目錄實際到 V{actual}：索引文件過期")]
    return [("OK", f"engines/README.md 已涵蓋到 V{actual}")]
