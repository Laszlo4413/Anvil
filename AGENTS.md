# AGENTS.md — Anvil（AI 協作專案樣板）

## 這是什麼

Anvil 是給「單人 + AI 代理人」協作的專案起手樣板。它只提供**協作紀律的基礎層**：
規則檔、狀態檔、三種紀錄（任務單／決策／限制）、一支 `doctor` 檢查、以及把檢查掛到 commit 上的 hook。
以 Anvil 開的新專案，改掉本節與 README 的專案說明即可；專案專屬的東西放延伸層（見最後一節），不要改基礎層規則。

## 導航（要知道 X → 讀 Y）

| 想知道 | 讀 |
|---|---|
| 現在版本、進行中的事、下一步 | [STATUS.md](STATUS.md) |
| 為什麼是這樣設計、當時拒絕了什麼 | [docs/decisions/](docs/decisions/) |
| 已知還沒解的問題與處置 | [docs/limits.md](docs/limits.md) |
| 某次任務的範圍、驗收、進度 | [docs/tasks/](docs/tasks/) |
| Python 專案的目錄／pyproject／版本慣例 | [docs/python_profile.md](docs/python_profile.md) |
| 怎麼掛到既有專案、多線／里程碑專案怎麼對映 | [docs/extending.md](docs/extending.md) |
| 過時但留作溯源的文件 | [docs/archive/](docs/archive/) |
| 各種紀錄的模板 | [docs/_templates/](docs/_templates/) |

## 常用指令

```bash
pip install -e ".[dev]"
python tools/doctor.py            # 全部檢查（收關前必跑）
python tools/doctor.py --quick    # commit 前的快速檢查（hook 呼叫的就是這個）
pytest
```

## 硬性規則（括號內是這條規則的檢查點）

1. 風險改動、刪除、不可逆操作前先問；設計偏好與取捨的**裁定歸使用者**，代理人不代裁。（settings.json 把 `git push`、`rm -rf` 設為 ask）
2. 引用使用者原話逐字；要改既有內容先說要改什麼、為什麼，**不靜默改寫**。（`.claude/rules/docs.md` 在編輯文件時提醒）
3. 寫進文件的事實先用工具查證；接手上一版留下的缺陷或待辦，**先查證再排期**。（任務單「開工前查證」欄必填）
4. 未證實或高風險的段落標 ⚠；**試過但無效的路徑也要記**，不只記成功做法。（ADR「被拒選項」欄必填，doctor 檢查非空）
5. 刪過程檔前三判準：結論已入文件、實物已封存、可重建，三者都成立才刪；**留存的也寫理由**。
6. 收關走 `/closeout`；STATUS、README、CHANGELOG 沒同步**不算收關**。（doctor 驗版本三處一致與 STATUS 新鮮度；hook 在 commit 前擋阻斷項）
7. STATUS、limits、decisions、tasks、archive 內每份文件都有 `Status／Updated／Expiry`；到期的由 doctor 抓出。（doctor）
8. `tools/` 內每支腳本的 docstring 有四段：為什麼需要／檢查什麼／安全設計／退出碼；會改動檔案的**預設乾跑**。（doctor）
9. 對話與文件用繁體中文；程式碼、識別字、commit 的 type 與 scope 用英文。

## 工作流程（依風險分級）

- **小改**（單檔、可回滾）：直接做。commit 訊息 `type(scope): 中文說明`，type 用 feat／fix／docs／chore／refactor／test。
- **中改**（跨檔、有驗收條件）：`/new-task` 開任務單 → 做 → 勾進度 → `/closeout`。
- **架構或不可逆決策**：`/new-adr` → 需要裁定的寫成 ⬜ Pending 停下等 → 裁定後再開任務單。
- 簡單問題直接回答，不過度工程化。同時 `Status: active` 的任務單只能有一份。

## 明確不做

- 不把目錄結構、技術棧、風格規則寫進本檔：讀程式碼可推、linter 該管。
- 不設「必須先讀某檔才能動」的阻斷規則：按需載入交給 `.claude/rules/` 的 `paths` 與 skills。
- 基礎層不含任何特定領域的詞彙與規矩；那些放延伸層。
- 不做續記本：歷史交給 git，紀錄只留現況與結案。

## 延伸層掛點（專案專屬的東西放這裡）

| 要加的東西 | 放哪 |
|---|---|
| 專案專屬規範（目錄規矩、命名、保護規則） | `docs/<project>_conventions.md`，並在本檔導航表加一列 |
| 只在碰特定路徑才要的規則 | `.claude/rules/<project>.md`，frontmatter 寫 `paths` |
| 專案自己的檢查 | `tools/doctor_ext/<name>.py`，實作 `run(ctx)`，doctor 自動載入 |
| 專案專屬流程 | `.claude/skills/<name>/SKILL.md` |
| 任務單、ADR 要加欄位 | 可加，不可刪基礎欄、不可改既有標題 |
| 工作單位是「某線的第 N 版」而非單一任務 | PLAN 留在版本夾，`docs/tasks/` 只放跨線工作；每線一個現行里程碑由 doctor_ext 管。見 `docs/extending.md` |
| 既有的限制總帳、任務夾不叫 Anvil 的名字 | 不改名，改 `[tool.anvil]` 的 `limits_file`／`tasks_dir`／`decisions_dir`／`archive_dir` |
