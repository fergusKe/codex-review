# Spec

## R8 專案自帶可用的設定檔

repository 根目錄有 `.codex-review.json`，內容至少包含非空的 `constraint`。

- 在乾淨的 checkout 上執行 `python3 -m codexreview.cli status` 必須成功（不得因缺設定而失敗）
- `constraint` 的內容必須包含「不得修改本 repository」的意思 —— 這是工具的核心約束，
  不能只是一個佔位字串

## R9 CI 執行完整測試套件

`.github/workflows/` 有一個 workflow，在 `push` 到預設分支與所有 `pull_request` 時觸發，
執行 `python3 -m unittest discover -s . -p 'test_*.py'`。

- 測試失敗時 workflow 必須失敗（不得用 `continue-on-error` 之類的旗標吞掉）
- 依 `workflow/CI.md`：互不依賴的工作平行跑，不串成一條

## R10 Control Plane 稽核成為 required check

`.github/workflows/` 有一個 workflow 執行 `workflow/bin/audit-control-plane.py`，
稽核範圍以 PR 的 merge-base 為起點。

- checkout 必須取得完整歷史（`fetch-depth: 0`），否則稽核拿不到 base
- 未授權的產品變更必須讓這個 workflow 失敗

**理由**：這一層是唯一擋得住 `git commit --no-verify` 的東西。
沒有它，本機所有 gate 都可以用一個旗標關掉。

## 不變的部分

第一輪批准的 R1–R7 行為完全不變。這一輪不得修改 `codexreview/` 底下任何檔案的行為。
