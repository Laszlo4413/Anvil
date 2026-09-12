@AGENTS.md

<!-- 跨工具通用的規則一律寫在 AGENTS.md；這裡只放 Claude Code 專屬補充，不要重複。 -->
- 收關用 `/closeout`、開任務單用 `/new-task`、開決策紀錄用 `/new-adr`（定義在 `.claude/skills/`）。
- 編輯 `docs/**` 或 `tools/**` 時會自動載入 `.claude/rules/` 對應的規則。
