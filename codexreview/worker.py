"""背景 worker：跑一輪審查並寫下判定（R5、R6）。

單獨成一個模組是為了讓 `runner.start` 能立即返回。它不該被直接呼叫。
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

from . import archive, config, runner, snapshot, verdict


def run_round(root: Path, n: int, *, execute=None) -> verdict.Verdict:
    cfg = config.Config.load(root)
    paths = archive.paths_for(root / cfg.archive_dir, n)
    state = json.loads(paths['verdict'].read_text(encoding='utf-8'))
    before = state['before']
    own = frozenset(state.get('own', ()))

    execute = execute or _execute
    ok, output = execute(runner.codex_command(cfg, paths['prompt']), root)
    paths['reply'].write_text(output, encoding='utf-8')

    after = snapshot.take(root, own) if ok else None
    diff = snapshot.compare(before, after) if after is not None else None
    v = verdict.decide(ok, diff)

    state.update({'state': 'done', 'result': v.result, 'detail': v.detail,
                  'changed_paths': list(diff.paths()) if diff else []})
    state.pop('before', None)   # 判定寫完之後不需要留原始快照，檔案會很大
    state.pop('own', None)
    paths['verdict'].write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    return v


def _execute(cmd: list[str], root: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    except (OSError, ValueError) as e:
        return False, f'無法執行審查指令：{e}'
    return r.returncode == 0, (r.stdout or '') + (r.stderr or '')


if __name__ == '__main__':
    run_round(Path.cwd(), int(sys.argv[1]))
