---
paths:
  - "docs/**"
  - "STATUS.md"
  - "README.md"
  - "CHANGELOG.md"
  - "AGENTS.md"
---
# 編輯文件時的規則（碰到上面的路徑才載入）

- **不靜默改寫**：引用使用者原話逐字；要改既有內容先說要改什麼、為什麼。任務單與 ADR 的「裁定原話」節只能追加，不能修改。
- **用模板，不自創結構**：新任務單／ADR 從 `docs/_templates/` 複製，`##` 標題不可改、不可刪，可加。首行的 HTML 註解填完要刪。
- **中繼資料**：治理文件開頭必有 `Status:`、`Updated:`、`Expiry:`（STATUS.md 另有 `Version:`）。改內容就改 `Updated`。
  - Expiry 只有四種：`[standing]`、`[until: vX.Y.Z]`、`[superseded-by: 相對路徑]`、`[retired: vX.Y.Z]`
  - 任務單 Status：draft｜active｜done｜dropped；ADR：proposed｜accepted｜rejected｜superseded；其他：active｜retired
- **同時 active 的任務單只能一份**。開新的前先把舊的收關或改 draft。
- **limits.md**：編號永不回收、永不刪列；狀態改「已解除」時解除證據必填；處置只有 accept／schedule／watch，watch 必附觸發條件。
- **ADR accepted 後不改寫**：要推翻就開新 ADR，舊的 Status 改 superseded、Expiry 改 `[superseded-by: 新檔]`。
- **退役文件**：搬進 `docs/archive/`，首行改成 `> ⛔ 已退役（日期）：由 <路徑> 取代。`，Status 改 retired。
- **CHANGELOG 是索引**：只給日期、一句話、連結；細節留在任務單與 ADR。
- **STATUS.md 是唯一活檔**：開工、收關都改它；其他文件不寫「目前進度」。
- 事實宣稱先查證再寫；未證實的段落標 ⚠；試過但無效的路徑也要記。
