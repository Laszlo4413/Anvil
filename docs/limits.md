# 已知限制總帳
Status: active
Created: 2026-09-12
Updated: 2026-09-12
Expiry: [standing]

> 唯一權威來源（限制類）。需要第二本帳（技術債、介面契約缺口…）時用 `[[tool.anvil.ledgers]]` 另開一檔、另一個編號前綴，同一套檢查。編號 L 開頭連號，**永不回收、永不刪列**；作廢的條目留著並寫明為什麼錯。
> 處置只有三種：accept（接受不解，寫理由）、schedule（排進某版）、watch（觀察，**必附觸發條件**）。
> 狀態改「已解除」時解除證據必填，doctor 會檢查。新條目格式見 `_templates/LIMIT_ENTRY.md`。

| # | 首見 | 限制 | 處置 | 狀態 | 解除條件 | 解除證據 |
|---|---|---|---|---|---|---|
| L01 | v0.1.0 | commit 前的 doctor 檢查是 Claude Code 的 PreToolUse hook；在終端或其他工具直接 `git commit` 不會觸發 | schedule v0.2.0 | 已解除 | 加 git 原生 pre-commit hook 呼叫同一支檢查 | v0.2.0 `tools/install_git_hooks.py --apply` 安裝 git 原生 pre-commit；`tests/test_doctor.py::test_install_git_hooks`。仍需每次 clone 後手動裝一次（TEMPLATE_README 步驟 7） |
| L02 | v0.1.0 | doctor 只驗結構（欄位齊全、編號、受控詞彙、目標檔存在），不驗語意（內容對不對、引用對不對） | accept：語意靠人審與 `/closeout` 清單；機器驗語意的成本不划算 | 未解 | 不解 | — |
| L03 | v0.1.0 | 治理文件的 `Updated` 要手填；忘了填時 doctor 只能靠 STATUS 新鮮度間接抓，抓不到個別文件 | watch：若 `/closeout` 時發現 Updated 落後的文件超過三份就升級 | 未解 | 加 PostToolUse hook 在 Edit／Write `docs/**` 時自動改 Updated | — |
| L04 | v0.1.0 | 樣板只附 Python profile；其他語言的目錄與版本慣例要自己寫 | accept：目前所有專案都是 Python | 未解 | 出現第二種語言的專案時寫對應 profile | — |
| L05 | v0.1.0 | hook 的 `if: "Bash(git commit *)"` 前綴比對脆弱，`git -C . commit` 或用 `&&` 串接的指令可能不命中；腳本內有二次檢查但仍可能漏 | watch：漏一次就把 `if` 拿掉改成全部 Bash 都進腳本判斷 | 未解 | 官方 hook 支援更精確的比對，或改為腳本內完整判斷 | — |
| L06 | v0.2.0 | coupled 檢查在 Claude Code hook 內用 `--changes all`（看整個工作樹），若只 commit 部分檔案會誤判「已滿足」或「缺少」；git 原生 hook 用 `--changes staged` 才精確 | accept：Claude Code 的 commit 幾乎都是 `git add -A`；要精確就裝原生 hook | 未解 | 不解 | — |
