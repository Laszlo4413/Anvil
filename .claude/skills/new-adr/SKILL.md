---
name: new-adr
description: 從模板開一份決策紀錄（docs/decisions/），用於架構級或不可逆的決策。強制寫脈絡、使用者原話、至少兩個選項（含被拒選項與理由）、後果與重審條件。需要使用者裁定的寫成 Pending 停下等。
argument-hint: "<決策標題>"
---
# /new-adr — 開決策紀錄

輸入：`$ARGUMENTS`（決策標題）。

## 步驟

1. **編號**：看 `docs/decisions/` 目前最大的 NNNN，加一（四位、連續、不回收）。
2. **複製模板**：`docs/_templates/ADR.md` → `docs/decisions/<NNNN>-<英文短標題>.md`。刪首行 HTML 註解。`##` 標題不可改。
3. **脈絡與問題**：起因 → 發展 → 為何現在要決定。不預設讀者知道結論；兩層原因（遠因、近因）都寫。
4. **使用者裁定原話**：逐字抄使用者說過的話。還沒裁的寫 ⬜ Pending。
5. **選項**：至少兩個。每個被拒選項寫**為什麼不選**；試過的寫試到哪裡失敗。這一節是 ADR 最有價值的部分，doctor 會檢查至少兩項。
6. **決定／後果／重審條件**：重審條件寫「什麼情況出現就回來重看」。
7. **Status**：有 Pending → `proposed`，停下等使用者；使用者裁定後改 `accepted`，把原話補進第 4 節。
8. 若這份 ADR 推翻舊的：舊 ADR Status 改 `superseded`、Expiry 改 `[superseded-by: <本檔名>]`，Updated 改今天；舊 ADR 其他內容不動。
9. 回報路徑與 Pending 項目。

## 不做
- 不替使用者做設計偏好或風險取捨的裁定。
- accepted 的 ADR 不改內容。
