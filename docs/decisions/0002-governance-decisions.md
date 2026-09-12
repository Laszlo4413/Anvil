# ADR-0002：治理層的九項裁定（主檔、commit 風格、hook 強度、檔名語言、ADR、中繼資料、記憶畢業、套用順序、守則去向）
Status: accepted
Created: 2026-09-12
Updated: 2026-09-12
Expiry: [standing]

## 脈絡與問題

研究報告第 8 節列了十個需要使用者裁定的問題（Q1 命名已由 ADR-0001 涵蓋）。這些問題各自都小，
但合起來決定了樣板的形狀，且其中兩項（commit 風格、檔名語言）在自家專案間是互相衝突的，
必須明示選一套。使用者裁定「依照你的建議」，本 ADR 把每一項的建議值、被拒選項與理由固定下來。

## 使用者裁定原話（逐字）

- 2026-09-12：「同意
並依照你的建議開始進行
專案樣板的名稱依你建議」
- 2026-09-12（看過網路範例後）：「同意」（針對「借三句、不借架構、開全域 CLAUDE.md、範例移到參考資料夾」）

## 選項（含被拒選項與被拒理由，必填）

| # | 題目 | 採用 | 拒絕的選項與理由 |
|---|---|---|---|
| Q2 | 主檔 | `AGENTS.md` 為唯一主檔，`CLAUDE.md` 只寫 `@AGENTS.md` + Claude 專屬補充 | CLAUDE.md 當主檔：只有 Claude Code 讀；Codex／Cursor／Copilot 都直接吃 AGENTS.md，Anthropic 官方在 issue #6235 的答覆也是 import。Windows 不用 symlink（要管理員權限）。 |
| Q3 | commit 訊息 | `type(scope): 中文說明`，type／scope 英文 | 純中文敘事（XivForge 現行）：無法被工具分類；純英文：使用者母語繁中，說明部分沒必要翻譯。五個 Python 專案已自發用 conventional 前綴。 |
| Q4 | hook 強度 | `PreToolUse` 在 `git commit` 前跑 `doctor --quick`，有阻斷則 exit 2 擋下；`ANVIL_SKIP_DOCTOR=1` 逃生口 | 只靠 `/closeout` 提醒：回到「靠記得」；Stop hook 每輪都擋：連擋 8 次會被系統放行且干擾大；CI 擋：單人專案沒有 PR 流程，掛點太晚。 |
| Q5 | 檔名語言 | 基礎層檔名英文、內容繁中；延伸層隨專案 | 中文檔名：GitHub 連結會變成百分號編碼、腳本路徑要處理引號；AI-OS 用英文檔名沒出過問題。 |
| Q6 | 要不要 ADR | 要，ADR-lite 五欄（脈絡／原話／選項含被拒／決定／後果與重審），只記架構級與不可逆決策 | 不做：XivForge 的「裁定紀錄」與 AI-OS 的 Decision Gate 證明這個需求真實存在，社群 2026 年也把 ADR 當代理人跨 session 唯一存活的 artifact；MADR 全欄位：decision-makers／consulted／informed 是團隊用的。 |
| Q7 | 搬多少 AI-OS | 只搬 `Status／Updated／Expiry` 三欄與受控詞彙到治理文件，doctor 抓到期 | Index-first 定點讀取 + 禁止全文讀：需要阻斷規則才能運作，Claude Code 原生的 rules `paths` 與 skills 已是真正的按需載入；40 條 domain routing、CONTRACTS 四檔、REGISTRY：三方協作專屬。 |
| Q8 | 記憶畢業 | auto memory 記回饋與現況，AGENTS.md 留規則，兩邊不重複；feedback 類記憶在兩個以上專案出現就提案寫進樣板。現有的「不靜默改寫、查證繼承缺陷、脈絡完整、繁中」已畢業到全域 `~/.claude/CLAUDE.md` 與 Anvil AGENTS.md | 全放記憶：記憶不跨機器、MEMORY.md 只載前 200 行；全放 AGENTS.md：專案現況會變動，寫死會過期。 |
| Q9 | 套用順序 | Anvil 自己 → XivForge（依研究報告第 6 節對照表）→ 五個 Python 工具不回頭改 | 先套 XivForge：它最複雜，第一次就撞延伸層邊界會分不清是樣板問題還是掛法問題。 |
| Q10 | 守則去向 | 併入 `docs/python_profile.md`；根目錄原檔加退役標記指向樣板 | 兩邊都留：兩份都像對的文件比沒文件危險。 |

## 決定

上表「採用」欄全部生效，已實作於 Anvil v0.1.0。

## 後果與何時該重審

- 正面：兩線衝突（commit 風格、檔名語言）有了明確答案；治理強度有強制點但留逃生口。
- 負面／代價：XivForge 既有的中文敘事 commit 與中文檔名不回溯改，掛到延伸層後會是兩種風格並存，只要求新 commit 照新規則。
- 重審條件：(a) Claude Code 原生支援 AGENTS.md（屆時 CLAUDE.md 可刪）；(b) 使用者開始在 Claude Code 之外大量 commit（屆時 L01 要升級成 git 原生 pre-commit hook）；(c) hook 逃生口被用超過三次（代表 doctor 的阻斷項訂太嚴）。
