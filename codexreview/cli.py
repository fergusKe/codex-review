"""CLI 入口。

**這裡刻意沒有任何放寬沙箱的選項（R7）。** argparse 會拒絕不認識的參數，
所以「沒有介面能做到」是可以被測試斷言的性質，而不只是「預設不做」。
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from . import archive, config, runner, verdict

EXIT_DIRTY = 2
EXIT_CONFIG = 3
EXIT_ARCHIVE = 4


def _root() -> Path:
    return Path.cwd()


def cmd_run(args) -> int:
    root = _root()
    try:
        cfg = config.Config.load(root)
    except config.ConfigError as e:
        print(f'ERROR: {e}', file=sys.stderr); return EXIT_CONFIG
    message = Path(args.message_file).read_text(encoding='utf-8') if args.message_file else args.message
    if not message or not message.strip():
        print('ERROR: 審查訊息不得為空', file=sys.stderr); return EXIT_CONFIG
    try:
        runner.require_clean(root)
    except runner.DirtyWorktree as e:
        print(f'ERROR: {e}', file=sys.stderr); return EXIT_DIRTY
    try:
        info = runner.start(root, cfg, message)
    except archive.ArchiveError as e:
        print(f'ERROR: {e}', file=sys.stderr); return EXIT_ARCHIVE
    print(f'第 {info["round"]} 輪已在背景送出（pid {info["pid"]}）')
    print(f'  prompt: {info["prompt"].relative_to(root)}')
    print(f'  reply:  {info["reply"].relative_to(root)}（完成後寫入）')
    print(f'查詢：codex-review status {info["round"]}')
    return 0


def cmd_status(args) -> int:
    root = _root()
    try:
        cfg = config.Config.load(root)
    except config.ConfigError as e:
        print(f'ERROR: {e}', file=sys.stderr); return EXIT_CONFIG
    adir = root / cfg.archive_dir
    rounds = archive.existing_rounds(adir)
    if not rounds:
        print('尚無任何輪次'); return 0
    targets = [args.round] if args.round else rounds
    worst = 0
    for n in targets:
        p = archive.paths_for(adir, n)['verdict']
        if not p.exists():
            print(f'第 {n} 輪：查無紀錄'); worst = max(worst, 1); continue
        st = json.loads(p.read_text(encoding='utf-8'))
        if st.get('state') != 'done':
            print(f'第 {n} 輪：執行中（pid {st.get("pid", "?")}）'); continue
        result = st.get('result', verdict.INCOMPLETE)
        print(f'第 {n} 輪：{result}')
        for line in (st.get('detail') or '').splitlines():
            print(f'  {line}')
        if result != verdict.CLEAN:
            worst = 1
    return worst


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog='codex-review',
                                 description='對抗性審查迴圈的執行器')
    sub = ap.add_subparsers(dest='cmd', required=True)

    run = sub.add_parser('run', help='送出一輪審查（背景執行）')
    g = run.add_mutually_exclusive_group(required=True)
    g.add_argument('-m', '--message', help='審查訊息')
    g.add_argument('-f', '--message-file', help='從檔案讀取審查訊息')
    run.set_defaults(fn=cmd_run)

    st = sub.add_parser('status', help='查詢輪次狀態與判定')
    st.add_argument('round', nargs='?', type=int, help='輪次編號；省略則列出全部')
    st.set_defaults(fn=cmd_status)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == '__main__':
    raise SystemExit(main())
