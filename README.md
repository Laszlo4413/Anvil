# Anvil — AI 協作專案的起手樣板

給「單人開發者 + AI 代理人」用的專案基礎層。它解決一個具體問題：**規則寫在文件裡不會自己被遵守**，
代理人的上下文一重置就忘。Anvil 把紀律做成三樣會失敗的東西：一支 `doctor` 檢查腳本、一個擋 commit 的 hook、
一組固定骨架的紀錄模板。

Anvil 不規定語言與框架；`docs/python_profile.md` 是 Python 工具專案的 profile，其他語言另寫。

## 運作原理

| 機制 | 做什麼 | 對應的教訓 |
|---|---|---|
| `AGENTS.md` | 唯一主規範，跨工具；`CLAUDE.md` 只寫 `@AGENTS.md` | 主檔要短、要能驗證、不放讀程式碼可推的東西 |
| `STATUS.md` | 唯一的「活」檔：版本、進行中、下一步 | 只有一份檔會頻繁改，其他都是穩定參考 |
| `docs/tasks/` `docs/decisions/` `docs/limits.md` | 任務單、決策紀錄、限制總帳，各有固定標題 | 紀錄骨架固定，代理人才不會即興發明結構 |
| 文件中繼資料 `Status／Updated／Expiry` | 文件誕生時宣告自己的死法 | 過期的索引文件沒人發現，是上一輪專案的實際事故 |
| `tools/doctor.py` | 十二項檢查，✗⚠✓ 三級，exit 1 有阻斷 | 鐵律沒有檢查就會被違反 |
| `.claude/hooks/pre_commit_check.py` | `git commit` 前自動跑 `doctor --quick`，阻斷則擋下 | 靠「記得跑」的檢查終究會腐化 |
| `.claude/skills/` | `/new-task` `/new-adr` `/closeout` 三個流程 | 多步驟流程做成可勾選的清單，不寫成散文規則 |

## 用 Anvil 開新專案

```bash
# 1. 複製（GitHub 上用 Use this template，或直接複製資料夾）
cp -r Anvil MyProject && cd MyProject && rm -rf .git

# 2. 改名：pyproject 的 name／version、套件目錄 anvil/ → mypkg/、[tool.anvil].package
# 3. 改 AGENTS.md「這是什麼」與本 README 的專案說明；STATUS.md 的 Version 對齊 pyproject
# 4. 寫 docs/decisions/0001-*.md：專案定位、範圍、明確不做（取代「專案綱要」）
# 5. 跑 doctor，紅的就是待填清單；全綠後首次 commit 並打 tag
python tools/doctor.py
git init -b main && git add -A && git commit -m "chore: 以 Anvil 樣板起始" && git tag -a v0.1.0 -m "v0.1.0"
```

之後：中改走 `/new-task`，收關走 `/closeout`；hook 會在 commit 時擋住有阻斷項的狀態。
在 Claude Code 之外直接 `git commit` 不會觸發 hook（見 `docs/limits.md` L01），收關前自己跑一次 `doctor`。

## 專案結構

```
Anvil/
├── AGENTS.md  CLAUDE.md  README.md  STATUS.md  CHANGELOG.md  LICENSE
├── pyproject.toml            # [tool.anvil] 是 doctor 的設定
├── anvil/                    # 佔位套件（含 __version__），開新專案時改名
├── tools/
│   ├── doctor.py             # 檢查腳本（只讀不寫）
│   └── doctor_ext/           # 延伸層自帶檢查的掛點
├── docs/
│   ├── decisions/            # ADR：NNNN-標題.md
│   ├── limits.md             # 已知限制總帳（編號不回收）
│   ├── tasks/                # 任務單：YYYY-MM-DD-vX.Y.Z-標題.md
│   ├── archive/              # 退役文件，首行有 ⛔ 標記
│   ├── _templates/           # 模板：標題不可改，首行註解「複製後填實」
│   ├── python_profile.md     # Python 工具專案的結構慣例
│   └── extending.md          # 延伸層指南：掛到既有專案、多線／里程碑專案怎麼對映
├── tests/                    # pytest；含 .gitignore 防線測試與 doctor 自檢
└── .claude/
    ├── settings.json         # hooks 與 permissions（進版控）
    ├── hooks/pre_commit_check.py
    ├── rules/                # docs.md、tools.md：碰到對應路徑才載入
    └── skills/               # closeout、new-task、new-adr
```

## 授權

MIT，見 [LICENSE](LICENSE)。
