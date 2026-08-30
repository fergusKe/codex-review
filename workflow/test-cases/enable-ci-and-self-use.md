# Test Design — enable-ci-and-self-use

延續第一輪的判準：**每條需求至少一個「防線被拿掉會變紅」的案例。**
只證明「設定正確時會過」的測試不算數。

這一輪的三條需求都是**設定檔**，不是程式行為。所以要先講清楚這些測試能證明什麼：

> 靜態斷言證明的是「這份 YAML 說了它會做那件事」，**不是**「GitHub 真的做了」。
> 後者只能由伺服器端的失敗實測證明（見〈本輪測不到的部分〉）。
> 把這兩件事混為一談，就是拿一個綠燈換掉真正的驗證。

## R8 專案自帶可用的設定檔

| ID | 情境 | 動作 | 期待 |
|---|---|---|---|
| T8.1 | 設定檔存在且可解析 | 讀取 repo 根目錄的 `.codex-review.json` | 是合法 JSON，含 `constraint` 鍵 |
| T8.2 | **約束非空** | 檢查 `constraint` | 去除空白後長度 > 0 |
| T8.3 | **約束確實表達「不得修改本 repository」** | 檢查 `constraint` 同時命中「禁止修改」的意思**與**受審 repository 的範圍指稱（`本 repository` / repo 名稱） | 兩者皆命中 |
| T8.4 | 乾淨 checkout 上執行 `status` | 複製 repo 到暫存目錄 → `python3 -m codexreview.cli status` | exit 0，不因缺設定而失敗 |
| T8.5 | **對照組：把 `constraint` 換成佔位字串** | 在暫存副本裡改成 `"TODO"` → 跑 T8.3 的判準 | **必須變紅** |
| T8.6 | **約束不含本機絕對路徑** | 檢查 `constraint` 不含 `/Users/`、`/home/`、`C:\` 等絕對路徑起頭 | 不命中 |

> T8.3 是這一輪唯一有實質內容的斷言。T8.1/T8.2 只證明「有這個欄位」——
> 一個寫著 `"TODO"` 的 `constraint` 會通過 T8.1 與 T8.2，卻讓 R3 的注入變成注入空話。
> T8.5 就是拿來鎖住這個邊界的：**沒有 T8.5，T8.3 可以退化成 T8.2 而沒人發現。**
>
> **T8.3 的第一版寫錯了，這裡記下原因。** 原本要求約束含「本 repository 的絕對路徑」，
> 實作後跑突變測試，基準線在 `git worktree` 裡就是紅的 —— 判準綁到了檔案系統位置，
> 而 worktree、以及任何非同名的 clone，位置都不一樣。
>
> T8.6 把這個 bug 變成守衛：**出貨的設定檔不得含本機絕對路徑。**
> 一條負向斷言，成本比一次事故低得多。
>
> 順帶記下它為什麼沒被單獨跑測試抓到：我的工作目錄剛好叫 `codex-review`，
> 名稱比對碰巧成立。**「在我的目錄下會過」跟「在別人的目錄下會過」是兩件事**，
> 突變測試換了個目錄跑，才把這個巧合拆開。

## R9 CI 執行完整測試套件

| ID | 情境 | 期待 |
|---|---|---|
| T9.1 | 測試 workflow 存在且是合法 YAML | 可解析 |
| T9.2 | 觸發條件 | 同時含 `push`（預設分支）與 `pull_request` |
| T9.3 | **執行的指令與 PROJECT-PROFILE 一致** | 從 `PROJECT-PROFILE.md` 的 `Custom verification command` 讀出指令，斷言它出現在 workflow 裡 |
| T9.4 | **沒有任何吞掉失敗的旗標** | 整份 workflow 不含 `continue-on-error: true`；不含以 `|| true`、`|| exit 0` 結尾的執行步驟 |
| T9.5 | **對照組：加上 `continue-on-error: true`** | 在暫存副本裡加進去 → 跑 T9.4 | **必須變紅** |

> T9.3 刻意**不寫死指令字串**。寫死的話，改了 profile 而忘了改 CI，測試照樣綠 ——
> 那正是這條需求要防的漏接。從 profile 讀出來比對，才會在兩者分岔時變紅。
>
> T9.4 針對的是「CI 有跑但不會擋」這個具體的假綠燈。它比「workflow 存在」有意義得多。

## R10 Control Plane 稽核成為 required check

| ID | 情境 | 期待 |
|---|---|---|
| T10.1 | 稽核 workflow 存在且是合法 YAML | 可解析 |
| T10.2 | **確實呼叫稽核程式** | 含 `workflow/bin/audit-control-plane.py` 的執行步驟 |
| T10.3 | **checkout 取得完整歷史** | 該 workflow 的 `actions/checkout` 步驟帶 `fetch-depth: 0` |
| T10.4 | 稽核起點 | 以 PR 的 merge-base 為起點，不是固定的 `HEAD~1` |
| T10.5 | 同樣不得吞掉失敗 | 套用 T9.4 的判準 |
| T10.6 | **對照組：拿掉 `fetch-depth: 0`** | 在暫存副本裡刪掉 → 跑 T10.3 | **必須變紅** |
| T10.7 | **端到端：未授權的產品變更會被稽核拒絕** | 在暫存 repo 上，於非 ENGINEERING 階段提交一個 `codexreview/` 的改動 → 直接跑 `audit-control-plane.py` | **非零 exit**，訊息指出未授權 |

> T10.3 是這一輪最容易寫成假測試的一條。`fetch-depth: 0` 沒設的話，
> runner 只 checkout 一個 commit，merge-base 算不出來，稽核會**因為算不出範圍而略過**——
> 一個永遠綠的 required check。T10.6 鎖住它。
>
> T10.7 是唯一不靠 YAML 文字的案例：它直接跑稽核程式本身，證明**稽核邏輯真的會拒絕**，
> 而不只是「YAML 裡有一行呼叫它」。沒有 T10.7，前面六條加起來只證明了一份設定檔的字面內容。

## 不變的部分（回歸）

| ID | 情境 | 期待 |
|---|---|---|
| TR.1 | 既有 33 條測試 | 全部通過，且**不修改任何一條的斷言** |
| TR.2 | `codexreview/` 的檔案內容 | 與第一輪封存時的 blob hash 逐檔相同 |

> TR.2 是機制，不是自律。「這一輪不動 `codexreview/`」寫在 spec 裡是一句規範；
> 比對 blob hash 才讓它變成一個會失敗的檢查。

## 本輪測不到的部分

以下三件事**沒有任何自動測試能證明**，必須人工實測並記錄在 `CONTEXT.md`：

1. **ruleset 真的存在且 Active** —— 它存在 GitHub 上，repo 裡看不到。
2. **required check 的名稱選對了** —— 選到同名的錯誤 check，PR 會永遠等一個不會回報的東西。
3. **紅燈時 merge 按鈕真的是灰的** —— 這是整層的唯一直接證據。

驗證方式依 `workflow/MERGE-PROTECTION.md`〈驗證：沒實測過的防線不算防線〉：
開一個故意失敗的分支，`--no-verify` 硬推，開 PR，確認 CI 紅燈且**按鈕點不下去**。

**在完成這個實測之前，R10 只能算「已設定」，不能算「已生效」。**

## 涵蓋範圍與邊界

- 不測 GitHub Actions 的執行結果（本機跑不到 runner）。
- 不測 ruleset 設定（GitHub 側狀態，repo 內無法觀測）。
- 不測 Codex 本身；沿用第一輪的 stub。
