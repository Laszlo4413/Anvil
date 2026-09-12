# 更新紀錄

格式依 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，版本依[語意化版本](https://semver.org/lang/zh-TW/)。
這裡只給日期、一句話、連結；細節在各自的任務單與 ADR，不重複展開。

## [Unreleased]

## [0.1.1] - 2026-09-12

### 新增
- `docs/extending.md` 延伸層指南：多線／里程碑專案怎麼對映、既有檔案怎麼指、掛接的執行原則、doctor_ext 寫法。起因是 XivForge 整合討論暴露的缺口，見 [任務單](docs/tasks/2026-09-12-v0.1.1-extension-guide.md)。
- doctor 設定新增 `limits_file`／`tasks_dir`／`decisions_dir`／`archive_dir`／`max_active_tasks`，既有專案不必改名對齊。

## [0.1.0] - 2026-09-12

### 新增
- 樣板初版：`AGENTS.md`（主規範）、`STATUS.md`（活檔）、任務單／ADR／限制總帳三種紀錄與模板、`tools/doctor.py` 十二項檢查、commit 前 hook、`/closeout` `/new-task` `/new-adr` 三個 skills、Python profile。見 [任務單](docs/tasks/2026-09-12-v0.1.0-bootstrap.md)、[ADR-0001](docs/decisions/0001-template-scope.md)、[ADR-0002](docs/decisions/0002-governance-decisions.md)。
