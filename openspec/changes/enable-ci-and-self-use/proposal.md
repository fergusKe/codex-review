# enable-ci-and-self-use

## 問題

第一輪把工具做出來了，但它**還不能被實際使用**，也**沒有任何自動化把關**：

1. 沒有設定檔。`.codex-review.json` 是產品檔案，ARCHIVE 階段加不進去 ——
   這不是缺陷，是流程正確地要求開第二輪。
2. 沒有 CI。33 條測試只在本機跑過；`workflow/CI.md` 要求 required check，
   而 `workflow/MERGE-PROTECTION.md` 說得更直接：本機所有防線都掛在 pre-commit 上，
   而 `--no-verify` 一行就能關掉它。

## 提案

- 加入 `.codex-review.json`：讓這個工具能審查它自己。
- 加入 GitHub Actions workflow：每次 push / PR 跑測試。
- 加入 `templates/github-workflow-control-plane-audit.yml` 的副本，
  讓 Control Plane 稽核成為 required check。

## 範圍

**做**：設定檔、測試 workflow、Control Plane 稽核 workflow。

**不做**：不加新功能、不改既有七條需求的行為、不動 CLI 介面。
這一輪純粹是「讓它能用、讓它被把關」。

## 為什麼分成兩輪

不是為了示範流程，是流程本身要求的：ARCHIVE 之後不允許實作，
要加任何產品檔案都必須重新取得人類批准。第一輪批准的範圍是「七條需求」，
CI 與設定檔不在裡面。
