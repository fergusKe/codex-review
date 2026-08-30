# Spec

## R11 核心內容鎖以 manifest 為準，不依賴 git 歷史

repository 有一份 checked-in 的 manifest，記錄 `codexreview/` 底下每個檔案的
路徑與 blob hash。回歸鎖比對的對象是這份 manifest，不是歷史上的某個 commit。

- 比對只能用**當前 tree** 的資訊（例如 `git ls-tree HEAD codexreview/`），
  不得使用 `git log` / `rev-list` / `--grep` 等需要祖先歷史的指令
- manifest 與實際內容不一致時，測試必須失敗
- 必須有一個**可重現**的方式重新產生 manifest（指令或腳本），
  否則它會在第一次正當變更時變成沒人敢碰的死檔

**取捨要講明白**：改成 manifest 之後，這道鎖從「與第一輪封存比對」變成
「與一份紀錄比對」，強度略降 —— 改動 `codexreview/` 的人可以順手重新產生 manifest。
接受這個取捨的理由是：那樣做會在 diff 裡留下一筆**明確的 manifest 變更**，
review 時看得到；而真正的授權邊界本來就在 Control Plane audit，不在這條測試。

## R12 測試套件不得依賴 CI 的 checkout 深度

有一條測試在 repository 的**淺 clone**（`--depth 1`）上執行整個測試套件，
全部通過才算過。

- 這條測試執行套件時必須排除它自己，避免無限遞迴
- 它證明的是「套件在只有一個 commit 的 checkout 上可以跑完」——
  這正是 CI runner 的預設環境

**理由**：R11 只修好已知的那一條。R12 是**會抓到下一次**的守衛。
用執行的方式證明這個性質，而不是掃描原始碼找 `git log` 字樣 ——
後者是在猜哪些寫法有問題，前者直接檢查性質本身。

## R13 archive 之前必須看到伺服器端綠燈

本 change 的 archive 前置條件：`main` 上最近一次 Tests workflow 為 success，
且該 run id 記入 evidence。

**這條沒有機制，只能靠人。** 依 `workflow/DEPLOYMENT.md` 的判準，
沒有機制的要明說是規範 —— 這裡明說。它被寫進 spec 的理由是上一輪犯過：
本機 verification 綠燈就 archive，CI 回報時已經來不及。
