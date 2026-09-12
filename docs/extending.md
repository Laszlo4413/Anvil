# 延伸層指南：把 Anvil 掛到既有專案，或掛上專案專屬的結構

> 基礎層（Anvil 複製即得的檔案）管協作紀律；延伸層是專案自己長出來的東西。
> 這份講兩者的分界怎麼守，以及幾種常見專案形狀怎麼對映。第一個實例是 XivForge（多線、多里程碑的管線工廠），
> 它的對映定案在 `D:\AI project\_討論筆記_XivForge整合Anvil.md`。

## 分界規則（一句話）

**基礎層檔案的標題結構不可改、內容可加；延伸層只能新增檔案與 doctor_ext 檢查，不能改基礎層檢查的判定。**

掛點一覽在 `AGENTS.md` 最後一節。本檔補的是「怎麼判斷該掛哪裡」。

## 形狀一：工作單位不是「任務」而是「里程碑」

有些專案的工作單位是「某條路線的第 N 版」，例如多引擎轉檔管線裡「VRChat 線的 V5」。這種專案的規劃書（PLAN）住在版本資料夾裡，因為**版本資料夾本身就是交付物**，收關後凍結。

對映方式：

| Anvil 概念 | 對映 | 怎麼設 |
|---|---|---|
| 任務單 | 各線版本夾的 PLAN.md | 留原地，不搬。開頭補 `Status／Updated／Expiry` 三行；未來的 PLAN 用「Anvil TASK 骨架 + 專案專屬節」的模板 |
| 「同時只能一份 active 任務單」 | 「每條線同時只有一個現行里程碑」 | `docs/tasks/` 只放跨線工作，`[tool.anvil].max_active_tasks` 維持 1；每線一個現行的規則寫在 `tools/doctor_ext/<project>.py` 掃版本夾 |
| `docs/tasks/` | 跨線與工廠層的工作 | 例：整合本身、共用層重構、開新線前的準備 |
| STATUS.md | 取代所有散落的狀態表 | 結構改成「套件版本一行 + 每個維度一張線狀態表 + 下一步」；其他導航文件**不再寫會過期的狀態字**，由 doctor_ext 反向檢查它們提到的最大版本沒落後目錄 |

## 形狀二：套件版本與里程碑版本是兩回事

套件版本（pyproject）記**程式本身**的演進；路線里程碑用 git tag（如 `vrchat-v5-close`）。兩者互不替代。
實務上每次里程碑收關幾乎都動到共用程式，所以「收關時 bump minor」成立，但 CHANGELOG 段落要寫「程式改了什麼」，里程碑只放一句話加連結。
Anvil 的 version 檢查只看 `v*` tag，其他前綴的 tag 不干擾。

## 形狀三：既有檔案已經扮演基礎層的角色

不要為了對齊檔名而改名。用設定把 doctor 指過去：

```toml
[tool.anvil]
package = "xivforge"
limits_file = "docs/10_已知限制總帳.md"   # 既有的限制總帳
tasks_dir = "docs/tasks"                   # 跨線任務單
decisions_dir = "docs/decisions"
archive_dir = "docs/archive"
max_active_tasks = 1
```

既有檔案只補開頭三行中繼資料；欄位若已相容（例如編號不回收、解除附證據），doctor 直接驗得動。

## 形狀四：專案有自己的「地質層」或凍結區

凍結區（收關後不得修改的版本夾、封存區）不歸基礎層管。基礎層只要求：
- 凍結檔的首行有標記（`> ⛔ 已凍結（日期）：由 <路徑> 取代`），讓誤開的人第一眼看到
- 凍結區的規矩寫在 `.claude/rules/<project>.md`，用 `paths` 限定在那些目錄，只在碰到時載入

## 掛接的執行原則

1. **分階段，每階段一個 commit，doctor 全綠才進下一階段。** 第一階段只加新檔（AGENTS、STATUS、ADR、.claude、doctor），不碰既有檔；第二階段才動既有文件（退役、補中繼資料、搬模板）；第三階段才寫 doctor_ext。
2. **歷史紀錄不回溯。** 舊 commit 風格、舊檔名、舊 PLAN 的格式都不改；只要求新的照新規則。要納管的歷史檔分批補中繼資料，或在 doctor_ext 明列豁免。豁免清單一長就是規則訂太寬的訊號。
3. **狀態只留一處。** 掛接時最常見的收穫就是發現同一個狀態寫在三個地方；全部收進 STATUS.md，其他地方改成連結。
4. **doctor_ext 要做負向測試。** 寫完檢查後故意把被檢查的東西弄壞一次，確認它真的會紅。會誤報的檢查比沒有檢查更糟，會被當雜訊忽略。

## doctor_ext 寫法

`tools/doctor_ext/<name>.py` 實作 `run(ctx)`，回傳 `[(level, message), ...]`，level 是 `"BLOCK"`／`"WARN"`／`"OK"`。
`ctx` 提供 `root`（Path）、`cfg`（`[tool.anvil]` 合併預設值）、`docs`、`git(*args)`（唯讀）。
丟出例外只會被記成警告，不會擋住基礎檢查。範例：`tools/doctor_ext/_example.py`（檔名以 `_` 開頭不會被載入，複製改名後才生效）。

典型的延伸檢查：
- 呼叫專案既有的檢查工具（`python -m <pkg>.tools.doctor --quick`），把它的退出碼翻成 BLOCK／OK
- 每條線的現行里程碑唯一
- 導航文件提到的最大版本號對目錄實際最大版本
- 凍結區內的檔案首行有標記
