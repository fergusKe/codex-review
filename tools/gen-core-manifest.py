#!/usr/bin/env python3
"""產生 `core-manifest.txt` —— `codexreview/` 的內容鎖。

為什麼需要它：這一輪的規範是「不得改動第一輪封存的產品程式」。原本的做法是
用 `git log --grep` 找到封存 commit 再比對 tree —— 那需要祖先歷史，而 CI 的
`actions/checkout` 預設是淺 clone，於是測試在 CI 上直接紅。

**依賴 checkout 深度的測試不是設定沒配好，是設計錯了。** 所以改成比對一份
checked-in 的紀錄，只用當前 tree 的資訊。

### 為什麼讀 index 而不是 `git ls-tree HEAD`

pre-commit 執行時 HEAD 還是**上一個** commit，`ls-tree HEAD` 看到的是改動前的
內容。於是「改了 codexreview/ 並重新產生 manifest」這件正當的事，會在
pre-commit 紅、commit 完又綠 —— 一個會讓人學會忽略它的檢查。

`git ls-files -s` 讀的是 index，也就是**即將被提交的內容**；CI 上 checkout 後
index 與 HEAD 一致，兩個環境給出同一個答案。而且它同樣不需要任何歷史。

用法：
    python3 tools/gen-core-manifest.py            # 印到 stdout
    python3 tools/gen-core-manifest.py --write    # 覆寫 core-manifest.txt
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'core-manifest.txt'
LOCKED_PREFIX = 'codexreview/'

HEADER = (
    '# core-manifest.txt —— codexreview/ 的內容鎖\n'
    '#\n'
    '# 由 `python3 tools/gen-core-manifest.py --write` 產生，不要手改。\n'
    '# 格式：<blob hash><tab><path>，依 path 排序。\n'
    '#\n'
    '# 這份紀錄被改動時，diff 會明確顯示出來 —— 那正是它的用途：\n'
    '# 它擋不住有意的變更，但讓變更無法安靜地發生。\n'
)


def index_entries(root: Path = ROOT) -> dict[str, str]:
    """`codexreview/` 的 path → blob hash。只讀 index，不碰歷史。"""
    r = subprocess.run(['git', '-C', str(root), 'ls-files', '-s', LOCKED_PREFIX],
                       capture_output=True, text=True, check=True)
    out = {}
    for line in r.stdout.splitlines():
        if not line:
            continue
        meta, path = line.split('\t', 1)
        out[path] = meta.split()[1]
    return out


def render(entries: dict[str, str]) -> str:
    return HEADER + ''.join(f'{entries[p]}\t{p}\n' for p in sorted(entries))


def parse(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        blob, path = line.split('\t', 1)
        out[path] = blob
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='覆寫 core-manifest.txt')
    a = ap.parse_args()
    entries = index_entries()
    if not entries:
        print(f'index 裡沒有任何 {LOCKED_PREFIX} 檔案 —— 拒絕產生空的鎖', file=sys.stderr)
        raise SystemExit(2)
    text = render(entries)
    if a.write:
        MANIFEST.write_text(text, encoding='utf-8')
        print(f'已寫入 {MANIFEST.relative_to(ROOT)}（{len(entries)} 筆）')
    else:
        sys.stdout.write(text)


if __name__ == '__main__':
    main()
