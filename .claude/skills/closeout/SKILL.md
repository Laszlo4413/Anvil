---
name: closeout
description: 版本收關流程。把進行中的任務單結案、同步 limits／版本號／CHANGELOG／STATUS／README、跑 doctor 與 pytest、commit 並打 tag。只在使用者要求收關時執行。
disable-model-invocation: true
argument-hint: "[版本號，例如 0.2.0]"
---
# /closeout — 版本收關

目標版本：`$ARGUMENTS`（沒給就用 pyproject.toml 目前的 version）。
逐項做，每做完一項回報一行。**任何一項做不到就停下說明，不要跳過。**

## 清單

1. **任務單結案**：找 `docs/tasks/` 內 `Status: active` 的檔（應該只有一份）。填「收關」節：✅ 日期、試過但無效的路徑、附帶發現。Status 改 `done`，Expiry 改 `[retired: v<版本>]`，Updated 改今天。驗收條件逐條確認並勾選；沒過的不能勾，要寫進 limits 或下一份任務單。
2. **limits.md**：本版新發現的限制 → 新增編號（用 `_templates/LIMIT_ENTRY.md`）；本版解除的 → 狀態改「已解除」並填證據。每條處置必須是 accept／schedule／watch 之一。Updated 改今天。
3. **版本號三處**：`pyproject.toml` 的 version、`<package>/__init__.py` 的 `__version__`、CHANGELOG 把 `[Unreleased]` 的內容搬到 `## [<版本>] - <今天>`（沒有 Unreleased 內容就直接寫一句話 + 連結）。
4. **STATUS.md**：Version、Updated 改今天；「目前在做」清空或改成下一件；「最近收關」加一列連到任務單與 ADR；「下一步」更新。
5. **README／AGENTS 導航表**：新增的文件有沒有進導航表？結構樹還對不對？
6. **doctor 全跑**：`python tools/doctor.py`。要求阻斷 = 0；警告逐條看，能修就修，不能修的說明原因。
7. **pytest**：`pytest -q` 全過。
8. **commit 與 tag**：
   ```bash
   git add -A && git commit -m "chore(release): v<版本> 收關"
   git tag -a v<版本> -m "v<版本>"
   ```
   push 由使用者決定，不要自己推。
9. **回報**：版本、tag、doctor 的阻斷／警告數、有沒有跳過的項目與原因。

## 不做
- 不改 ADR 的內容（accepted 就凍結；要推翻開新 ADR）。
- 不刪任何 limits 條目、不重用編號。
- 不用 `ANVIL_SKIP_DOCTOR=1` 繞過 hook；收關時 doctor 就是要全綠。
