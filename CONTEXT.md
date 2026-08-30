# CONTEXT

## 這個專案要解決什麼

用另一個 AI（Codex）對一份程式碼做**對抗性審查**，一輪一輪跑。實務上跑了十九輪之後，
流程本身變成問題：每一輪都要手動貼同一段約束、手動存快照、手動比對、手動存回覆，
而其中**至少有一個步驟長期是錯的**（見〈零改動不變式〉）。

這個工具把那條迴圈變成可重複執行的指令。

## Domain vocabulary

| 詞 | 意義 |
|---|---|
| **Round（輪次）** | 一次「送出 → 取得回覆」的完整循環，有編號 |
| **Constraint block（約束區塊）** | 每輪都必須原文重複的禁令：不得修改被審 repository、不得碰指定的其他路徑 |
| **Integrity snapshot（完整性快照）** | 送出前後對 repository 內容取的指紋，用來證明審查者沒有動過任何東西 |
| **零改動不變式** | 審查者只能讀不能寫。違反時**同時**發生兩件事：這一輪的審查結論失效，且 repository 已被污染 |
| **Blocker** | 必須修掉才能簽核的發現 |
| **Convergence line（收斂線）** | 可判定的停止條件；沒有它，對抗審查不會自己結束 |

## 已知的真實缺陷（本工具存在的直接理由）

**快照只涵蓋 tracked 檔案。** 實際使用的指令是

```
git ls-files -z | xargs -0 shasum -a 256
```

`git ls-files` **只列出 tracked 檔案**。審查者若新增一個未追蹤的檔案，前後兩份快照
完全相同，而使用者會得到「零改動」的結論。這個洞存在了十九輪都沒被發現 ——
因為它從未被觸發，而不是因為它被檢查過。

**沒被觸發過的防線，不是防線。**

## 非目標

- 不做「自動判斷 blocker 是否為真」。審查結論由人判讀。
- 不代替人類決定收斂線。
- 不管理 Codex 的安裝與登入。

## 約束

- 審查者以唯讀沙箱執行；本工具不放寬那個設定。
- 一輪可能超過十分鐘，必須背景執行。
- 工作樹不乾淨時不得開始 —— 否則「零改動」無法與「我自己的編輯」區分。

## 伺服器端綠燈紀錄

`openspec/changes/pin-core-manifest` 的 R13 要求 archive 之前先看到 `main` 的
Tests workflow 綠燈，並把 run id 留下來。

| Change | Head SHA | Run id | Conclusion |
|---|---|---|---|
| `pin-core-manifest` | `87a47c5` | `33307431118` | success |

前一次（`e515ca7`）是 failure —— 就是本 change 修掉的那條依賴 git 歷史的測試。

**紀錄放在這裡而不是 `workflow/evidence/`，是因為 Control Plane 的 evidence
命名空間是封閉的**：只認 `core/<timestamp>.md`、`browser.md`、`api.md` 三種，
其餘路徑在 VERIFICATION 會被當成未授權的產品變更擋下（實測 DENY）。
放進 `openspec/changes/<change>/` 也不行 —— 那會改變 change 的內容 digest，
讓人類批准失效（實測 archive 被擋）。

要讓「伺服器端綠燈」成為真正的 evidence，得在 Starter 新增一種 evidence 型別，
那是跨生命週期的改動；Starter 目前凍結在 v1.0-rc.5。**在那之前 R13 只有規範，
沒有機制** —— 這一行本身就是它的紀錄。

## 伺服器端執法層（已實測）

`main` 受 Branch Ruleset `Protect main` 保護，2026-08-30 設定並實測。

| 項目 | 值 |
|---|---|
| Ruleset id | `21856100` |
| Enforcement | **active** |
| Target | `refs/heads/main` |
| Required checks | `test-suite`、`control-plane-audit` |
| Require branches up to date | 是 |
| 其他規則 | `pull_request`、`deletion`、`non_fast_forward` |
| **Bypass actors** | **空 —— 沒有任何人可以 override，包含 repository owner** |

### 實測紀錄

依 `workflow/MERGE-PROTECTION.md`〈驗證：沒實測過的防線不算防線〉，
在 PR #1 上跑過失敗情境：

1. 用 `git commit --no-verify` 繞過本機所有 gate，推一條故意失敗的測試
2. `test-suite` 紅燈；`control-plane-audit` 也紅 —— 它認出這是
   **ARCHIVE 階段的未授權產品變更**（`A: tests/test_zz_merge_protection_drill.py`）
3. `mergeStateStatus` 由 `UNSTABLE` 變 `BLOCKED`，**Merge 按鈕變灰**（API 與目視雙重確認）

`control-plane-audit` 只在 `pull_request` 觸發，**PR #1 是它第一次真的執行**。
在此之前它是一個從未被證明會動的 required check。

驗證後 PR 關閉、分支刪除。

### 後果

`main` 不再能直接 push。所有變更都要走 PR 並通過兩個 check ——
包含 Control Plane 的 transition commit。
