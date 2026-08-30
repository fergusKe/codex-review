# Spec

## R11 核心內容鎖以 manifest 為準，不依賴 git 歷史

repository 有一份 checked-in 的 manifest，記錄 `codexreview/` 底下每個檔案的
路徑與 blob hash。回歸鎖比對的對象是這份 manifest，不是歷史上的某個 commit。

- 比對只能用**當前內容**的資訊（`git ls-files -s codexreview/`，讀 index），
  不得使用 `git log` / `rev-list` / `--grep` 等需要祖先歷史的指令
- 比對的對象是 **index 而不是 `HEAD`**：pre-commit 執行時 HEAD 還是上一個
  commit，用 `ls-tree HEAD` 會讓「改了 `codexreview/` 並重新產生 manifest」
  這件正當的事在 pre-commit 紅、commit 完又綠 —— 一個會讓人學會忽略它的檢查。
  CI 上 checkout 後 index 與 HEAD 一致，兩個環境給出同一個答案
- manifest 與實際內容不一致時，測試必須失敗
- 必須有一個**可重現**的方式重新產生 manifest（指令或腳本），
  否則它會在第一次正當變更時變成沒人敢碰的死檔

**取捨要講明白**：改成 manifest 之後，這道鎖從「與第一輪封存比對」變成
「與一份紀錄比對」，強度略降 —— 改動 `codexreview/` 的人可以順手重新產生 manifest。
接受這個取捨的理由是：那樣做會在 diff 裡留下一筆**明確的 manifest 變更**，
review 時看得到；而真正的授權邊界本來就在 Control Plane audit，不在這條測試。

## R12 測試套件不得依賴 checkout 深度

有一條測試把**即將提交的內容**（index）具現化成一個**只有單一 commit、
沒有任何祖先歷史**的 repository，並在其中執行整個測試套件，全部通過才算過。

- 這條測試執行套件時必須排除它自己，避免無限遞迴
- 必須先斷言那個 repository 真的只有一個 commit；否則整條測試可能在一份
  完整歷史上跑，綠燈而毫無意義
- 檢查的對象是 **index**，不是 `HEAD`

### 為什麼是 index 而不是 HEAD

> 這一條是實作階段發現的，而且是**致命**的：原本的做法是
> `git clone --depth 1 file://<repo>`，clone 的是 HEAD。
>
> 但 pre-commit 執行時 HEAD 還是上一個 commit。於是這道守衛在一個
> 目前違反它的 repository 裡**永遠無法被加進去** —— 修正它的那個 commit
> 本身會被自己擋下來，而唯一的出路是 `--no-verify`。
>
> **一道只能在已經乾淨的 repository 上安裝的守衛，等於裝不上去。**
>
> 這與 R11 選擇讀 index 而非 `ls-tree HEAD` 是同一個理由，只是後果嚴重得多。

用單一 commit 的具現化取代淺 clone，同時也移除了另一個陷阱：
`git clone --depth 1 /本機路徑` 會走 hardlink 捷徑並**直接忽略 `--depth`**，
必須用 `file://` 才會真的變淺 —— 一個測試寫錯就會安靜地驗證空氣的地方。

**理由**：R11 只修好已知的那一條。R12 是**會抓到下一次**的守衛。
用執行的方式證明這個性質，而不是掃描原始碼找 `git log` 字樣 ——
後者是在猜哪些寫法有問題，前者直接檢查性質本身。

## R13 archive 之前必須看到伺服器端綠燈

本 change 的 archive 前置條件：`main` 上最近一次 Tests workflow 為 success，
且該 run id 記入 evidence。

**這條沒有機制，只能靠人。** 依 `workflow/DEPLOYMENT.md` 的判準，
沒有機制的要明說是規範 —— 這裡明說。它被寫進 spec 的理由是上一輪犯過：
本機 verification 綠燈就 archive，CI 回報時已經來不及。
