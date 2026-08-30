# codex-review

對抗性審查迴圈的執行器。它負責**證據**，不負責判斷。

## 為什麼存在

用另一個 AI 對程式碼做對抗性審查時，每一輪都要做四件事：貼約束、取快照、比對快照、
存回覆。手動做的問題不是麻煩，是**它可以安靜地做錯**。

實際跑了十九輪之後才發現，用的快照指令是：

```bash
git ls-files -z | xargs -0 shasum -a 256
```

而 `git ls-files` **只列 tracked 檔案**。審查者若新增一個未追蹤的檔案，前後快照完全
相同，使用者會得到「零改動」的結論。這個洞在十九輪裡從未被觸發 ——
**那不等於它被檢查過。**

## 用法

```bash
# 1. 設定檔（constraint 不得為空）
cat > .codex-review.json <<'JSON'
{
  "constraint": "不要修改本 repository 底下任何檔案，我會前後比對 SHA-256。",
  "session_id": "選填：延續既有的審查對話",
  "archive_dir": "reviews"
}
JSON

# 2. 送出一輪（背景執行，立即返回）
python3 -m codexreview.cli run -f round-05.md

# 3. 查狀態與判定
python3 -m codexreview.cli status
```

## 三種判定

| 結果 | 意義 |
|---|---|
| `CLEAN` | 零改動，本輪結論可信 |
| `TAMPERED` | **兩件事同時發生**：結論失效，且 repository 已被污染，列出所有變動路徑 |
| `INCOMPLETE` | 審查未正常結束，**不對完整性做任何宣稱** |

`INCOMPLETE` 單獨存在是刻意的：併進 `TAMPERED` 會產生假警報，併進 `CLEAN`
會產生假保證，兩者都比誠實地說「不知道」更糟。

## 設計上的幾個決定

**唯讀沙箱寫死，沒有放寬的介面。** 能被旗標關掉的防線不是防線；而會去關它的人，
多半正是最不該關它的那個。

**工作樹不乾淨就拒絕開始。** 否則「審查後有改動」無法與「你自己的編輯」區分。
檢查在執行**之前** —— 跑過之後才發現，事情已經發生了。

**歸檔不覆寫。** 稽核紀錄被蓋掉的時候，正是最需要它的時候。

**快照只排除本輪自己寫的三個檔案**，不排除整個歸檔目錄 ——
審查者去改舊輪次的紀錄是最該被抓到的事。

## 不做的事

不判斷 blocker 真偽、不決定收斂線、不管理審查者的安裝與登入。
審查結論由人判讀。

## 開發

```bash
python3 -m unittest discover -s . -p 'test_*.py'
```

### 改動 `codexreview/` 之後要重新產生內容鎖

`core-manifest.txt` 記錄 `codexreview/` 每個檔案的 blob hash。
它擋不住有意的變更 —— 它讓變更**無法安靜地發生**：改了程式卻沒更新鎖，
測試會紅；更新了鎖，diff 裡就會有一筆明確的紀錄給 review 看。

```bash
git add codexreview/                          # 鎖比對的是 index，不是 HEAD
python3 tools/gen-core-manifest.py --write
```

### 測試套件不得依賴 git 歷史

有一條測試（`tests/test_core_manifest.py`）會把 index 具現化成一個
**只有單一 commit** 的 repository，在裡面跑完整套件。理由：CI 的
`actions/checkout` 是淺 clone，任何用 `git log` / `rev-list` / `--grep`
查祖先歷史的測試在 CI 上都會紅，而在你的機器上永遠是綠的。

這條守衛存在，是因為這件事已經發生過一次。

本專案以 [ai-project-starter](https://github.com/fergusKe/ai-project-starter) 的
規格驅動流程開發：規格與測試設計經人類批准後才進入實作，
見 `openspec/changes/` 與 `workflow/test-cases/`。
