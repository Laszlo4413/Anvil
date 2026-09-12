# 更新紀錄

格式依 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，版本依[語意化版本](https://semver.org/lang/zh-TW/)。
這裡只給日期、一句話、連結；細節在各自的任務單與 ADR，不重複展開。

## [Unreleased]

## [0.2.0] - 2026-09-12

### 新增
- 中大型專案需要的四項通用機制，全部是設定鍵或工具，不加特例：`[[tool.anvil.coupled]]` 耦合檢查（改 X 必改 Y，commit 前擋）、`[[tool.anvil.ledgers]]` 多本帳（同格式同檢查、各自編號前綴）、任務單遞迴掃描（可分夾）、`tools/install_git_hooks.py`（git 原生 pre-commit，Claude Code 以外的工具也擋）。見 [任務單](docs/tasks/2026-09-12-v0.2.0-scale-mechanisms.md)。
- `docs/extending.md` 加「規模變大時的加法」；`TEMPLATE_README.md` 加「小專案的最小用法」。
- 兩份 README 分工：`README.md` 是專案 README 骨架（新專案填實），`TEMPLATE_README.md` 是樣板說明（新專案刪除）。doctor 新增第 13 項 `bootstrap` 檢查：專案改名後樣板說明檔未刪、README 殘留佔位符會警告，README 連到已刪的檔會阻斷。

### 變更
- 去除 0.1.1 沾到的單一專案特化：`docs/extending.md`、AGENTS 掛點表、`doctor_ext/_example.py` 改為領域中立的寫法與範例。
- 新增延伸點 `[[tool.anvil.governed]]`：用 glob 與 kind 把專案自己的文件納入中繼資料檢查，不必寫程式。

## [0.1.1] - 2026-09-12

### 新增
- `docs/extending.md` 延伸層指南：多線／里程碑專案怎麼對映、既有檔案怎麼指、掛接的執行原則、doctor_ext 寫法。起因是 XivForge 整合討論暴露的缺口，見 [任務單](docs/tasks/2026-09-12-v0.1.1-extension-guide.md)。
- doctor 設定新增 `limits_file`／`tasks_dir`／`decisions_dir`／`archive_dir`／`max_active_tasks`，既有專案不必改名對齊。

## [0.1.0] - 2026-09-12

### 新增
- 樣板初版：`AGENTS.md`（主規範）、`STATUS.md`（活檔）、任務單／ADR／限制總帳三種紀錄與模板、`tools/doctor.py` 十二項檢查、commit 前 hook、`/closeout` `/new-task` `/new-adr` 三個 skills、Python profile。見 [任務單](docs/tasks/2026-09-12-v0.1.0-bootstrap.md)、[ADR-0001](docs/decisions/0001-template-scope.md)、[ADR-0002](docs/decisions/0002-governance-decisions.md)。
