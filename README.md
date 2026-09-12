<!-- 這是 Anvil 樣板產生的專案 README 骨架。把尖括號佔位符填實、刪掉本註解與下一行的提示。樣板本身的說明見 TEMPLATE_README.md（開專案後刪除該檔）。 -->
> 本專案以 [Anvil](TEMPLATE_README.md) 樣板起始。開專案後刪除這一行與 `TEMPLATE_README.md`。

# <專案名> — <一句話定位>

<兩三句話：解決什麼問題、給誰用、核心賣點。涉及版權或隱私的工具，這裡放一句免責或僅供個人使用的提醒。>

## 運作原理

<幾點講清楚流程或所依賴的引擎；為什麼這樣設計、為什麼不那樣做。決策細節連到 docs/decisions/。>

## 安裝

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   /   macOS、Linux: source .venv/bin/activate
pip install -e ".[dev]"
python tools/doctor.py          # 全綠再開工
```

### 安裝成指令（選用）

<列出 pip install -e . 後可用的進入點，例如 `<套件名>`（GUI）與 `<套件名>-cli`（CLI）。純函式庫可刪本節。>

## 使用

### <介面一，例如圖形介面>

<怎麼啟動、操作流程。>

### <介面二，例如命令列>

```bash
<指令範例>
```

| 參數 | 說明 |
|---|---|
| `<參數>` | <說明> |

## 專案結構

```
<專案名>/
├── AGENTS.md  STATUS.md  CHANGELOG.md     # 規範、現況、變更（見 AGENTS.md 導航表）
├── <套件名>/                              # 原始碼：core 與 cli／gui 薄殼分離
├── docs/                                  # 決策、限制總帳、任務單、模板
├── tools/                                 # doctor 與治理腳本
└── tests/
```

## 已知限制

權威來源是 [docs/limits.md](docs/limits.md)，編號跨版本穩定；這裡不重複展開。

## 授權

MIT，見 [LICENSE](LICENSE)。<用途聲明，例如僅供個人使用。>
