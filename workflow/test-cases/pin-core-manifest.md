# 測試設計 — pin-core-manifest

對應 change：`pin-core-manifest`（R11 / R12 / R13）

本輪要修的是同一類錯誤第二次出現：**測試依賴了本機環境碰巧成立的性質。**
所以測試設計的重點不只是「把 TR.2 修好」，而是「加一個會抓到下一次的守衛」。

---

## R11 核心內容鎖以 manifest 為準

| # | 案例 | 做法 | 判準 |
|---|---|---|---|
| T11.1 | manifest 存在且可解析 | 讀 checked-in 的 manifest 檔 | 是合法格式，至少一筆 |
| T11.2 | **manifest 與當前 tree 一致** | `git ls-tree -r HEAD codexreview/` → path→blob 對照 manifest | 兩邊完全相等（路徑集合與 hash 皆同） |
| T11.3 | **對照組：manifest 少一筆** | 移除一筆再跑 T11.2 的判準 | **必須變紅** |
| T11.4 | **對照組：改掉一個 hash** | 竄改一個 blob hash 再跑 T11.2 的判準 | **必須變紅** |
| T11.5 | **產生器可重現** | 執行重新產生的指令，輸出與 checked-in 檔案逐位元組比對 | 完全相同（idempotent） |

T11.5 是讓 manifest 不變成死檔的那一條。**一份沒有人知道怎麼重新產生的鎖，
第一次正當變更時就會被整條刪掉** —— 那比沒有鎖更糟，因為刪掉的過程看起來很合理。

### 不做原始碼掃描

R11 寫「不得使用 `git log` / `rev-list` / `--grep`」。可以寫一條測試去掃原始碼
找這些字樣 —— **本輪刻意不做**，理由與 R12 的理由是同一個：

掃字樣是在**猜哪些寫法有問題**（而且會被註解、字串誤判）；R12 的淺 clone 測試
直接檢查**性質本身** —— 任何依賴祖先歷史的寫法，在只有一個 commit 的 checkout 上
都會現形，不管它長什麼樣子。

---

## R12 測試套件不得依賴 checkout 深度

| # | 案例 | 做法 | 判準 |
|---|---|---|---|
| T12.1 | **淺 clone 上跑完整套件** | `git clone --depth 1 file://<ROOT>` → 在該 clone 執行整套測試 | exit 0 |
| T12.2 | **先確認 clone 真的是淺的** | 在 clone 內 `git rev-list --count HEAD` | **必須 == 1** |
| T12.3 | **對照組：放回一條依賴 `git log --grep` 的測試** | 在 clone 內寫入一條會查歷史的測試再跑 | **必須變紅** |

### 三個實作上一定會踩到的點，先寫在這裡

1. **本機路徑 clone 會忽略 `--depth`。** `git clone --depth 1 /path/to/repo` 走的是
   本機 hardlink 路徑，`--depth` 無效，clone 出來是完整歷史 —— 於是 T12.1 綠燈，
   卻什麼都沒驗到。**必須用 `file://` 協議。**

   T12.2 存在的唯一理由就是擋這件事。它是本輪的 anti-vacuous-pass guard，
   地位等同上一輪 `AuditWorkflow.setUp` 裡那句 `assertTrue(self.audit_wf)`。

2. **遞迴。** T12.1 在子行程裡跑整套測試，而整套測試包含 T12.1 自己。
   用環境變數（例如 `SHALLOW_CLONE_CHILD=1`）讓子行程裡的這條測試 skip。

3. **淺 clone 只含已提交的內容。** 工作區裡沒 commit 的改動不會進去。
   這是限制不是 bug —— CI 測的本來就是 commit。列在〈本輪測不到的部分〉。

---

## R13 archive 前的伺服器端綠燈

| # | 案例 | 做法 | 判準 |
|---|---|---|---|
| T13.1 | `main` 最近一次 Tests workflow 綠燈 | **人工**：看 GitHub Actions | conclusion = success，run id 記入 evidence |

**這條沒有測試，只有人。** 依 `workflow/DEPLOYMENT.md`「沒有機制的要明說是建議」，
這裡明說：它是規範，不是機制。寫進 spec 的理由是上一輪犯過 ——
本機綠燈就 archive，CI 回報時 `Implementation allowed` 已經是 `no`，修不了。

---

## 回歸

| # | 案例 | 判準 |
|---|---|---|
| TR.1 | 既有 49 條測試全部通過 | 無退化 |
| TR.2 | **舊的 TR.2（比對第一輪封存 commit）被 T11.2 取代** | 舊測試移除，新鎖到位，`codexreview/` 內容不變 |

TR.2 不是被刪掉，是**換了實作**：鎖的對象從「歷史上的某個 commit」變成
「一份 checked-in 的紀錄」。強度的取捨已寫在 R11，不在這裡重複。

---

## 本輪測不到的部分

1. **未提交的工作區改動**在淺 clone 測試裡不存在。T12 證明的是「commit 出去的東西
   在 CI 上跑得起來」，不是「你桌上這一份跑得起來」。
2. **OS / Python 版本差異**。子行程用的是同一台機器、同一個直譯器。
   R12 抓的是 checkout 深度這一個環境維度，不是全部。
3. **R13 沒有機制**，人不看就是不會發生。
4. **伺服器端 ruleset 實測仍未做** —— 紅燈 CI → 灰色 merge 按鈕那一組。
   `control-plane-audit` workflow 到目前為止**一次都沒有真的跑過**
   （它只在 `pull_request` 觸發，而至今所有 commit 都直接進 `main`）。

> 第 4 點在 `enable-ci-and-self-use` 就列過一次了，本輪仍未消除。
> **在完成那個實測之前，R10 只能算「已設定」，不能算「已生效」。**
