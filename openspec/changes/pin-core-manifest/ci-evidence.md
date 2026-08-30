# 伺服器端綠燈（R13）

archive 的前置條件：`main` 上最近一次 Tests workflow 必須是 success。

| 欄位 | 值 |
|---|---|
| Workflow | Tests |
| Branch | main |
| Head SHA | `87a47c5178c5e863bfb5e9daa8b00aecc91f5cdb` |
| Run id | `33307431118` |
| Conclusion | **success** |
| 取得方式 | `gh run list --branch main --limit 3 --json databaseId,name,status,conclusion,headSha` |

前一次（`e515ca7`）是 **failure** —— 就是本 change 要修的那一條
（`test_TR_2_codexreview_blobs_match_archive_commit` 在淺 checkout 上找不到封存 commit）。

**這條沒有機制，只有人。** 見 `openspec/changes/pin-core-manifest/specs/main.md` R13：
上一輪本機綠燈就 archive，CI 回報時 `Implementation allowed` 已經是 `no`，
修不了自己弄紅的 CI。這份檔案是為了讓下一次不必再靠記性。
