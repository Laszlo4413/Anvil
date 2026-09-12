# 延伸層指南：把 Anvil 掛到既有專案，或掛上專案專屬的結構

> 基礎層（Anvil 複製即得的檔案）管協作紀律，對任何領域中立；延伸層是專案自己長出來的東西。
> 這份講兩者的分界怎麼守、延伸點有哪些、幾種常見的專案形狀怎麼對映。
> 具體某個專案的對映定案不放在樣板裡，放在那個專案自己的整合任務單。

## 分界規則（一句話）

**基礎層檔案的標題結構不可改、內容可加；延伸層只能新增檔案、新增設定、新增 doctor_ext 檢查，不能改基礎層檢查的判定。**

## 延伸點一覽

| 延伸點 | 機制 | 適合放什麼 |
|---|---|---|
| `[tool.anvil]` 設定 | `limits_file`、`tasks_dir`、`decisions_dir`、`archive_dir`、`max_active_tasks`、`governed` | 既有檔案已扮演基礎層角色時，把 doctor 指過去，不改名 |
| `governed` 設定 | `[[tool.anvil.governed]]` 列出額外要納管的文件 glob 與類別 | 專案自己的規劃檔、里程碑檔，要吃同一套中繼資料檢查但不在 `docs/tasks/` |
| `tools/doctor_ext/<name>.py` | 實作 `run(ctx)`，doctor 自動載入 | 專案專屬的結構檢查，或包裝專案既有的檢查工具 |
| `.claude/rules/<project>.md` | frontmatter 寫 `paths`，碰到才載入 | 只跟某些目錄有關的規矩（凍結區、保護區、命名） |
| `.claude/skills/<name>/SKILL.md` | 可勾選的流程 | 專案專屬的多步驟流程（開新版本、封存、發布） |
| `docs/<project>_conventions.md` | 一般文件，AGENTS 導航表加一列 | 專案的目錄規矩、命名、領域詞彙 |
| 模板加欄 | 複製 `docs/_templates/` 的檔再加節 | 任務單、ADR 需要專案專屬欄位時；基礎欄不刪、標題不改 |

## 形狀一：工作單位是「里程碑」而非「任務」

有些專案的工作單位是「某條路線的第 N 版」，例如多平台輸出的專案裡「平台 A 的第 5 版」。這種專案的規劃檔住在版本資料夾裡，因為**版本資料夾本身就是交付物**，收關後凍結。

| Anvil 概念 | 對映 | 怎麼設 |
|---|---|---|
| 任務單 | 各路線版本夾裡的規劃檔 | 留原地，不搬。開頭補 `Status／Updated／Expiry` 三行；未來的規劃檔用「Anvil TASK 骨架 + 專案專屬節」的模板 |
| 中繼資料檢查 | 讓 doctor 納管這些規劃檔 | `[[tool.anvil.governed]]` 加 `glob = "<路線目錄>/**/PLAN.md", kind = "task"` |
| 「同時只能一份 active 任務單」 | 「每條路線同時只有一個現行里程碑」 | `docs/tasks/` 只放跨路線工作，`max_active_tasks` 維持 1；每路線一個現行的規則寫在 doctor_ext |
| `docs/tasks/` | 跨路線與共用層的工作 | 例：整合本身、共用層重構、開新路線前的準備 |
| STATUS.md | 取代所有散落的狀態表 | 結構改成「套件版本一行 + 每個維度一張路線狀態表 + 下一步」；其他導航文件**不再寫會過期的狀態字**，由 doctor_ext 反向檢查 |

## 形狀二：套件版本與里程碑版本是兩回事

套件版本（pyproject）記**程式本身**的演進；路線里程碑用 git tag（如 `<路線>-v5-close`）。兩者互不替代。
實務上每次里程碑收關幾乎都動到共用程式，所以「收關時 bump minor」成立，但 CHANGELOG 段落要寫「程式改了什麼」，里程碑只放一句話加連結。
Anvil 的 version 檢查只看 `v*` tag，其他前綴的 tag 不干擾。

## 形狀三：既有檔案已經扮演基礎層的角色

不要為了對齊檔名而改名。用設定把 doctor 指過去：

```toml
[tool.anvil]
package = "<pkg>"
limits_file = "docs/KNOWN_LIMITS.md"     # 既有的限制總帳，名字隨專案
tasks_dir = "docs/tasks"
decisions_dir = "docs/decisions"
archive_dir = "docs/archive"
max_active_tasks = 1

[[tool.anvil.governed]]                  # 額外納管的文件（可多組）
glob = "routes/**/PLAN.md"
kind = "task"                            # task | adr | general，決定 Status 詞彙
```

既有檔案只補開頭三行中繼資料；欄位若已相容（例如編號不回收、解除附證據），doctor 直接驗得動。

## 形狀四：專案有自己的凍結區或封存區

凍結區（收關後不得修改的版本夾、封存區）不歸基礎層管。基礎層只要求：
- 凍結檔的首行有標記（`> ⛔ 已凍結（日期）：由 <路徑> 取代`），讓誤開的人第一眼看到
- 凍結區的規矩寫在 `.claude/rules/<project>.md`，用 `paths` 限定在那些目錄，只在碰到時載入

## 掛接既有專案的執行原則

1. **分階段，每階段一個 commit，doctor 全綠才進下一階段。** 第一階段只加新檔（AGENTS、STATUS、ADR、.claude、doctor），不碰既有檔；第二階段才動既有文件（退役、補中繼資料、搬模板）；第三階段才寫 doctor_ext。
2. **歷史紀錄不回溯。** 舊 commit 風格、舊檔名、舊規劃檔的格式都不改；只要求新的照新規則。要納管的歷史檔分批補中繼資料，或在 doctor_ext 明列豁免。豁免清單一長就是規則訂太寬的訊號。
3. **狀態只留一處。** 掛接時最常見的收穫是發現同一個狀態寫在三個地方；全部收進 STATUS.md，其他地方改成連結。
4. **doctor_ext 要做負向測試。** 寫完檢查後故意把被檢查的東西弄壞一次，確認它真的會紅。會誤報的檢查比沒有檢查更糟，會被當雜訊忽略。
5. **不要反過來改樣板去遷就一個專案。** 某個專案需要的東西，先問「第二個專案也會需要嗎」；會的才進基礎層的延伸點，不會的留在那個專案的延伸層。

## doctor_ext 寫法

`tools/doctor_ext/<name>.py` 實作 `run(ctx)`，回傳 `[(level, message), ...]`，level 是 `"BLOCK"`／`"WARN"`／`"OK"`。
`ctx` 提供 `root`（Path）、`cfg`（`[tool.anvil]` 合併預設值，自訂鍵也讀得到）、`docs`、`git(*args)`（唯讀）。
丟出例外只會被記成警告，不會擋住基礎檢查。範例：`tools/doctor_ext/_example.py`（檔名以 `_` 開頭不會被載入，複製改名後才生效）。

典型的延伸檢查：
- 呼叫專案既有的檢查工具，把它的退出碼翻成 BLOCK／OK
- 每條路線的現行里程碑唯一
- 導航文件提到的最大版本號對目錄實際最大版本
- 凍結區內的檔案首行有標記
- 某類文件的 `Updated` 落後太久（範例檔示範的就是這個）
