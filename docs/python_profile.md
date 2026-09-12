> 本檔由 `D:\AI project\專案架構守則.md`（2026-07-15 版）併入 Anvil 樣板（2026-09-12）。
> 它是 Anvil 的 **Python 工具 profile**：基礎層定協作紀律，本檔定 Python 專案的目錄／pyproject／進入點／版本慣例。
> 其他語言的專案不必讀本檔，改寫對應的 profile。

# 專案架構守則（Python 工具專案）

> 這份文件是 `D:\AI project` 下所有專案的**共同標準**，也是**新建專案時的參考範本**。
> 目標：每個工具都有一致的目錄結構、`pyproject.toml`、README、LICENSE、進入點與版本號，
> 讓任何一個專案「打開就懂、裝了就能跑」。
>
> 現有範例：`DiskLens`、`GoogleDriveSyncer`、`PatronVault`、`RGScribe_TW`、`ehviewer-dl`。
> 最後更新：2026-07-15。

---

## 0. 一眼看懂：一個合格專案應有的東西

```
專案根目錄/
├── README.md            # 必要 — 簡介 + 安裝 + CLI + GUI
├── LICENSE              # 必要 — MIT（Copyright (c) 2026 斯洛 萊）
├── pyproject.toml       # 必要 — 套件名、版本、相依、進入點
├── .gitignore           # 必要 — 排除 venv / 快取 / 憑證 / 輸出
├── requirements.txt     # 選用 — 快速安裝相依（與 pyproject 同步）
├── <套件名>/            # 必要 — 原始碼（見 §2 兩種佈局）
│   ├── __init__.py      #        內含 __version__
│   ├── __main__.py      #        python -m <套件名> 進入點
│   ├── cli.py           #        命令列前端
│   ├── gui.py 或 gui/   #        圖形介面前端
│   └── core/ ...        #        核心邏輯（與前端分離）
├── tests/               # 建議 — pytest 離線測試
└── docs/                # 建議 — 進階說明（安裝操作、CLI 參考、GUI 規格）
```

**檢查清單（每個專案都該打勾）**

- [ ] `README.md`：簡介、運作原理、安裝、CLI、GUI、專案結構、授權
- [ ] `LICENSE`：MIT
- [ ] `pyproject.toml`：`name` / `version` / `description` / `readme` / `license` / `requires-python` / `dependencies`
- [ ] 進入點：GUI 用 `gui-scripts`、CLI 用 `scripts`（見 §4）
- [ ] `__init__.py` 內有 `__version__`，與 pyproject 的 `version` 一致
- [ ] `.gitignore` 排除 venv、`__pycache__`、憑證、輸出、`.pytest_tmp`
- [ ] 核心邏輯與 GUI/CLI 前端**分離**（前端只是薄殼）
- [ ] 敏感檔（`credentials.json`、`token.json`、`cookie.txt`、`*.db`）**不進版控**

---

## 1. 命名慣例

| 對象 | 慣例 | 範例 |
|------|------|------|
| 專案資料夾 | 大駝峰或帶地區後綴 | `DiskLens`、`RGScribe_TW` |
| 套件（package） | 全小寫、無底線 | `disklens`、`gdsyncer`、`rgscribe` |
| 發佈名（pyproject `name`） | 小寫，可含連字號 | `disklens`、`ehviewer-dl` |
| GUI 指令 | 套件名 | `disklens`、`patronvault` |
| CLI 指令 | 套件名 或 `套件名-cli` | `rgscribe`、`disklens-cli` |

---

## 2. 兩種原始碼佈局（擇一）

### A. 扁平佈局（小型工具，最常用）
套件資料夾直接放在根目錄。適合單一套件的小工具。
> 現有例：`DiskLens/disklens/`、`PatronVault/patronvault/`、`ehviewer-dl/ehviewer_dl/`、`RGScribe_TW/rgscribe/`

```toml
[tool.setuptools]
packages = ["disklens", "disklens.core", "disklens.cli", "disklens.gui"]
```

### B. `src/` 佈局（多套件或較大專案）
所有套件放在 `src/` 下，避免測試誤抓到未安裝的原始碼。
> 現有例：`GoogleDriveSyncer/src/{gdsyncer,archivecheck}/`

```toml
[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

**原則**：單一套件 → A；有兩個以上可獨立發佈的套件、或原始碼量大 → B。

---

## 3. 前端／核心分離（重要架構原則）

GUI 與 CLI 都只是**薄前端**，真正邏輯放在核心模組，兩個前端共用。
這是所有現有專案的共同設計，也是新專案必守的原則：

```
<套件>/
├── core/ 或散落模組   # 純邏輯，不 import GUI 套件、不 print
├── cli.py             # 解析 argv → 呼叫 core → 輸出文字
└── gui.py 或 gui/     # 視窗事件 → 呼叫 core → 更新畫面
```

好處：邏輯可被 `pytest` 離線測試；GUI 壞掉不影響 CLI；未來要加 Web/API 前端也只是再包一層。

> 參考 `PatronVault`：`auth.py / core.py / cloudscan.py`（核心）被 `cli.py` 與 `gui.py` 共用。

---

## 4. 進入點慣例（GUI 不開黑窗、CLI 有文字輸出）

Windows 上 GUI 若用一般 console script 會**多開一個黑色主控台視窗**；用 `gui-scripts`
會編成 `pythonw` 執行、不開黑窗，但也因此看不到 stdout。因此**分成兩個進入點**：

```toml
# GUI 進入點（不會開黑色主控台視窗）：<套件>.exe
[project.gui-scripts]
mytool = "mytool.gui:main"

# CLI 進入點（需要文字輸出時用）：<套件>-cli.exe
[project.scripts]
mytool-cli = "mytool.cli:main"
```

再加一個 `__main__.py` 做 `python -m <套件>` 的統一分派（無參數開 GUI、有參數走 CLI）：

```python
# <套件>/__main__.py
import sys

def main() -> int:
    if len(sys.argv) > 1:
        from mytool.cli import main as cli_main
        return cli_main()
    from mytool.gui import main as gui_main
    return gui_main()

if __name__ == "__main__":
    raise SystemExit(main())
```

> 純 CLI 工具可只留 `[project.scripts]`；子命令多的工具（如 `rgscribe translate`）
> 可讓單一 `scripts` 進入點自行分派子命令，另開 `-gui` 進入點給圖形介面。

---

## 5. `pyproject.toml` 標準範本

```toml
[project]
name = "mytool"
version = "0.1.0"
description = "一句話說明這個工具做什麼（GUI + CLI）"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
dependencies = [
    "requests>=2.28",
]

[project.optional-dependencies]
dev = ["pytest>=8"]
gui = ["PySide6>=6.6"]        # 若 GUI 相依較重，可拆成選用群組

# GUI 進入點（不會開黑色主控台視窗）
[project.gui-scripts]
mytool = "mytool.gui:main"

# CLI 進入點
[project.scripts]
mytool-cli = "mytool.cli:main"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["mytool", "mytool.core"]

[tool.pytest.ini_options]
testpaths = ["tests"]
# 本機系統暫存目錄有權限問題時，改用專案內暫存
addopts = "--basetemp=.pytest_tmp"
```

**慣例說明**
- `version` 一律遵守語意化版本（見 §9）。
- `license = "MIT"` 用 SPDX 字串（`pip install -e .` 會在隔離環境取新版 setuptools，支援此寫法）。
- 建置後端可換：小工具用 `setuptools`，`RGScribe_TW` 用 `hatchling` 亦可，重點是欄位齊全。
- 選用相依（GUI、雲端、轉換…）用 `optional-dependencies` 分群，讓純 CLI 使用者不必裝一堆。

---

## 6. README 標準結構

所有現有 README 都遵循這個骨架，新專案照抄即可：

```markdown
# 專案名 — 一句話定位

兩三句話：解決什麼問題、給誰用、核心賣點。
（涉及版權/隱私內容的工具，這裡放一句免責/僅供個人使用的提醒。）

## 運作原理        # 選用但建議：幾點講清楚流程或所依賴的引擎
## 安裝            # venv → pip install -r requirements.txt（或 pip install -e .）
### 安裝成指令（選用，推薦）   # pip install -e . 產生的 exe 進入點表
## 使用
### 圖形介面 (GUI)  # 如何啟動 + 操作流程
### 命令列 (CLI)    # 指令範例 + 參數表
## 專案結構        # 目錄樹 + 每個檔案一句話
## 授權            # 連到 LICENSE + 用途聲明
```

- **安裝段**永遠先給 venv 三行，再給「安裝成指令」選項。
- **CLI 段**用表格列參數（`| 參數 | 說明 |`）。
- 內容較多時把完整操作搬到 `docs/`，README 只留快速開始並用引言連過去
  （見 `GoogleDriveSyncer` → `docs/安裝與操作說明.md`、`RGScribe_TW` → `docs/使用說明.md`）。

---

## 7. `docs/` 慣例（中大型專案）

README 放不下的內容拆到 `docs/`：

| 檔名 | 內容 |
|------|------|
| `安裝與操作說明.md` | 完整逐步安裝、憑證取得、疑難排解 |
| `CLI_REFERENCE.md` | 每個子命令與參數的完整參考 |
| `GUI_SPEC.md` | GUI 各分頁/元件規格 |
| 其他設計文件 | 各功能的設計決策（如 `HYBRID_TRANSLATION.md`） |

> `RGScribe_TW/docs/` 是最完整的範例。小工具（DiskLens、ehviewer-dl）README 已足夠、可不建 docs。

---

## 8. LICENSE 與 `.gitignore`

**LICENSE**：一律 MIT，`Copyright (c) 2026 斯洛 萊`。直接複製任一現有專案的 `LICENSE`。

**`.gitignore` 必備條目**：

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
build/
dist/

# 測試
.pytest_tmp/
.pytest_cache/

# 敏感檔（絕不進版控）
credentials.json
token.json
cookie.txt
*.db
*.sqlite

# 執行產出
output/
.rgscribe/
_duplicates/
```

> **安全原則**：憑證、cookie、token、資料庫、下載產出一律排除。
> 提供 `*.example.txt` 範本（如 `ehviewer-dl/cookie.example.txt`）供使用者照填。

---

## 9. 版本號慣例（語意化版本 SemVer）

格式 `主版本.次版本.修訂號`（`MAJOR.MINOR.PATCH`）：

| 遞增 | 時機 |
|------|------|
| **PATCH**（0.1.0 → 0.1.1） | 修 bug、不影響用法 |
| **MINOR**（0.1.0 → 0.2.0） | 新增功能、向下相容 |
| **MAJOR**（0.x → 1.0.0） | 破壞性變更；或「功能完整、可正式使用」的第一個穩定版 |

**單一事實來源**：版本號寫在 `pyproject.toml` 的 `version`，
`__init__.py` 用 `__version__` 對應（兩者需一致）：

```python
# <套件>/__init__.py
__version__ = "0.1.0"
```

- 開發中、尚未穩定 → `0.x.y`。
- 已驗證可正式使用 → `1.0.0`（現有 `ehviewer-dl` 已是 1.0.0，其餘為 0.1.0）。

> **與 Git 的搭配（tag / release）將在後續「版本追蹤建議」另行處理，先不動。**

---

## 10. 測試慣例

- 用 `pytest`，測試放 `tests/`，全部**離線**（不打真實網路/雲端）。
- 相依外部服務的邏輯要能以假資料測試（`GoogleDriveSyncer` 有 86 個離線測試可參考）。
- pyproject 設 `testpaths = ["tests"]`；本機暫存有權限問題時加 `addopts = "--basetemp=.pytest_tmp"`。

```powershell
pip install -e ".[dev]"
pytest
```

---

## 11. 新專案快速起手（Checklist 流程）

1. 建資料夾 `D:\AI project\<專案名>\`，選定套件名（小寫）。
2. 複製本文件 §5 的 `pyproject.toml`、任一 `LICENSE`、§8 的 `.gitignore`。
3. 建套件資料夾 + `__init__.py`（含 `__version__ = "0.1.0"`）+ `__main__.py`。
4. 核心邏輯放 `core/`；`cli.py`、`gui.py` 只做薄前端。
5. 依 §6 骨架寫 `README.md`。
6. `pip install -e .` 驗證兩個進入點都能跑。
7. 需要時建 `tests/` 與 `docs/`。
8. `git init -b main` → 首次 commit → 上 GitHub → 打 tag（見 §12）。

---

## 12. Git 與版本發佈流程

### 分支慣例
- 預設分支一律 `main`（不用 `master`）。`git init -b main`；既有 repo：`git branch -m master main`。
- 功能開發用 `feature/xxx` 分支，完成後併回 `main`（`git merge` 或 PR）。**別讓進度只停在功能分支。**

### 版本號 = git tag（核心）
版本號要對應到 git 上的一個時間點，否則無法「回到某一版」或產生 GitHub Release。
每次要定版時：

```powershell
# 1. 確認 pyproject.toml 的 version 與 <套件>/__init__.py 的 __version__ 一致
# 2. 更新 CHANGELOG.md（把 [Unreleased] 改成該版本 + 日期）
# 3. commit 後打 annotated tag（v 前綴），再推上去
git tag -a v0.2.0 -m "<專案> 0.2.0"
git push
git push --tags          # 或 git push origin v0.2.0
```

推上 tag 後，GitHub 的 Releases 頁會自動出現該版本；可再按「Draft a release」貼上 CHANGELOG 內容。

### 版本三處必須一致
`pyproject.toml` 的 `version`、`<套件>/__init__.py` 的 `__version__`、git tag `vX.Y.Z`。
改版時三處一起改。（RGScribe_TW 曾發生 commit 說「更新到 0.3.0」但檔案仍是 0.1.0 的漂移——就是沒同步造成。）

> 進階（選用）：可改用 `setuptools-scm` / `hatch-vcs` 讓 `version` 直接從 git tag 產生，
> 從此只需打 tag、不必手動改檔案。個人小專案維持手動同步也完全可行。

### CHANGELOG.md
採 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/) 格式，每版記
`新增 / 修正 / 變更 / 移除`。開發中的內容先累積在最上方的 `## [Unreleased]`，定版時改成版本號。

### 目前各專案版本（2026-07-15 建立標籤）
| 專案 | 版本 | 分支 | 備註 |
|------|------|------|------|
| DiskLens | v0.1.0 | main | — |
| GoogleDriveSyncer | v0.1.0 | main | 由 master 改名 |
| PatronVault | v0.1.0 | main | 尚未設定 GitHub remote |
| RGScribe_TW | v0.3.0 | main | 修正版本漂移、feature 併回 main |
| ehviewer-dl | v1.0.0 | main | 新建 git repo，尚未設定 remote |
| XivForge | v0.1.0 | main | 2026-07-16 新建；尚未設定 remote |

