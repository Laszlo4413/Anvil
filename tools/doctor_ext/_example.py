"""_example — 延伸層檢查的範例（檔名以 _ 開頭，doctor 不會載入；複製並改名後才生效）。

## 為什麼需要這支
基礎層的 doctor 不知道你的專案有什麼特殊結構。延伸層把自己的檢查放在 tools/doctor_ext/<name>.py，
實作 run(ctx)，doctor 會自動載入並把結果併進同一份報告，不用改基礎層的檢查。

## 檢查什麼
本範例示範一個領域中立的需求：「docs/ 內每份有 Updated 欄的文件，不能落後最近一次 commit 超過 N 天」。
基礎層只對 STATUS.md 做這件事；如果你的專案想對所有治理文件都做，就用這個。
天數從 ctx.cfg 讀自訂鍵 ext_stale_days（在 pyproject 的 [tool.anvil] 加一行即可），預設 90。

## 安全設計
只讀。ctx 提供 root、cfg、docs、git(*args)（唯讀）。回傳 [(level, message), ...]，
level 用 "BLOCK" / "WARN" / "OK"。丟出例外只會被記成警告，不會擋住基礎檢查。

## 退出碼
本檔沒有自己的退出碼；結果併入 doctor（0 = 無阻斷，1 = 有阻斷）。
"""

from __future__ import annotations

import datetime as dt
import re


def run(ctx):  # noqa: ANN001 — ctx 是 tools/doctor.py 的 Ctx
    """docs/ 內帶 Updated 欄的文件，落後最近 commit 超過 ext_stale_days 天者列為警告。"""
    days = int(ctx.cfg.get("ext_stale_days", 90))
    last = ctx.git("log", "-1", "--format=%cs")
    if not last:
        return [("OK", "沒有 git 紀錄，略過新鮮度檢查")]
    last_date = dt.date.fromisoformat(last)
    stale = []
    for p in sorted(ctx.docs.rglob("*.md")):
        if "_templates" in p.parts or "archive" in p.parts:
            continue
        head = p.read_text(encoding="utf-8").splitlines()[:15]
        m = next((re.match(r"^Updated:\s*(\d{4}-\d{2}-\d{2})", ln) for ln in head if ln.startswith("Updated:")), None)
        if not m:
            continue
        lag = (last_date - dt.date.fromisoformat(m.group(1))).days
        if lag > days:
            stale.append(f"{p.relative_to(ctx.root).as_posix()}（落後 {lag} 天）")
    if stale:
        return [("WARN", "文件 Updated 落後最近 commit 超過 %d 天：%s" % (days, "、".join(stale)))]
    return [("OK", f"docs/ 內帶 Updated 的文件都在 {days} 天內")]
