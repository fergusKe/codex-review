# Proposal — pin-core-manifest

## 問題

第二輪加的 CI 在 `main` 上是紅的。紅的不是產品，是回歸鎖 `TR.2`：

```
FAIL: test_TR_2_codexreview_blobs_match_archive_commit
AssertionError: '' is not true : 找不到第一輪的封存 commit
```

`TR.2` 用 `git log --grep` 在歷史裡找第一輪的封存 commit。`actions/checkout` 預設
淺 checkout，runner 上沒有那段歷史，於是找不到。

它 fail-closed 了（找不到就失敗，不是靜悄悄跳過），這點是對的。但**一條在 CI 環境
跑不起來的測試，等於一條遲早會被關掉的測試。**

## 這是同一類錯誤的第二次

| | 本機碰巧成立 | CI 沒有 |
|---|---|---|
| T8.3（已修） | 工作目錄剛好叫 `codex-review` | 換個目錄就紅 |
| TR.2（本輪） | 本機有完整 git 歷史 | 淺 checkout 就紅 |

兩次都是**測試依賴了環境裡碰巧存在的東西**。修 T8.3 時我只處理了目錄名，
沒回頭問「還有哪些環境假設」—— 那才是該問的問題。所以這一輪不只修 TR.2，
還要加一道**會抓到下一次**的守衛。

## 明確拒絕的做法

給 Tests workflow 加 `fetch-depth: 0`。它能讓 CI 變綠，但只是讓某一份 CI 設定
剛好餵飽這條測試。哪天有人為了加速改回淺 checkout，測試又紅 ——
而下一個人多半會選擇停掉測試，不是改回設定。

**依賴 checkout 深度的測試，不是「需要設定配合」，是設計錯了。**

## 非目標

- 不改 R1–R10 任何一條的行為。
- 不動 `codexreview/` 的產品邏輯。
- 不加新功能。


## 修訂紀錄

- **R12 的做法在實作階段被推翻並重寫。** 原本寫的是
  `git clone --depth 1 file://<repo>` —— clone 的是 HEAD，而 pre-commit 執行時
  HEAD 還是上一個 commit。結果是這道守衛在一個**目前違反它**的 repository 裡
  永遠無法被加進去：修正它的那個 commit 會被自己擋下來，唯一出路是 `--no-verify`。

  這是同一類錯誤的**第三次**：判準綁到了環境碰巧成立的性質（HEAD 的內容），
  而不是綁到真正要檢查的東西（即將提交的內容）。R11 與 R12 現在都讀 index。

  發現後走 `revert-to-spec` 回 SPECIFICATION 重新取得批准，
  沒有先改程式再補文件。
