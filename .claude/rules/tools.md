---
paths:
  - "tools/**"
  - ".claude/hooks/**"
---
# 寫腳本時的規則（碰到上面的路徑才載入）

- **docstring 四段必備**（doctor 檢查關鍵字）：`## 為什麼需要這支`、`## 檢查什麼`（會改東西的寫 `## 做什麼`）、`## 安全設計`、`## 退出碼`。模板在 `docs/_templates/TOOL_DOCSTRING.md`。「為什麼需要」寫觸發它誕生的實際事故，不寫理想。
- **會改動檔案的腳本預設乾跑**，`--apply` 才真的動；先印出會動什麼再動。
- **不覆蓋既有腳本**：要大改先另存備份或開新檔；已驗證通過的腳本視為唯讀。
- **退出碼有語意**：0 成功／1 有阻斷或失敗／2 用法錯誤。不要用退出碼當唯一成敗判準去呼叫外部程式（有些程式拋例外仍回 0），要看輸出。
- **只用標準函式庫**，除非 pyproject 已列該依賴。
- **延伸層檢查**放 `tools/doctor_ext/<name>.py`，實作 `run(ctx)` 回傳 `[(level, message)]`；不改 `tools/doctor.py` 的基礎檢查。範例：`tools/doctor_ext/_example.py`。
- Windows 相容：路徑用 `pathlib`，讀寫檔明寫 `encoding="utf-8"`，stdout 先 `reconfigure(encoding="utf-8")`。
