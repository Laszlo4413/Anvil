# docs/archive — 退役文件

過時但留作溯源的文件放這裡。規則：

1. 搬進來的每份檔，**首行**改成退役標記（doctor 會檢查）：
   ```
   > ⛔ 已退役（YYYY-MM-DD）：由 <現行文件的相對路徑> 取代。留作溯源，不得以本檔為據。
   ```
2. 中繼資料：`Status: retired`，`Expiry: [superseded-by: <相對路徑>]`（doctor 會驗目標存在）或 `[retired: vX.Y.Z]`。
3. 不改內容、不刪。歷史交給 git，這裡只是讓誤開舊文件的人第一眼看到它過時了。
4. 本 README 不需要退役標記。
