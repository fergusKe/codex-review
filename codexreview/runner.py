"""執行一輪審查（R2、R5、R7）。"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

from . import archive, config, snapshot

# **唯讀沙箱是寫死的。R7。**
#
# 不提供覆寫它的選項，理由是：一個能被旗標關掉的防線不是防線；
# 而會去關它的人，多半正是最不該關它的那個。
# 若審查者未來需要寫入才能運作，那是設計要重新談，不是加一個 --unsafe 旗標。
SANDBOX_ARGS = ('--skip-git-repo-check', '-c', 'sandbox_mode="read-only"')
REASONING_ARGS = ('-c', 'model_reasoning_effort="high"')


def own_paths(root: Path, paths: dict) -> frozenset[str]:
    """本輪自己會寫的檔案，相對於 repository 根目錄。

    只排除這三個，不排除整個歸檔目錄 —— 審查者若去改**別輪**的紀錄，
    那是最該被抓到的事，不能一起放行。
    """
    return frozenset(p.relative_to(root).as_posix() for p in paths.values())


class DirtyWorktree(Exception):
    """工作樹不乾淨。呼叫端以 exit 2 結束。"""


def worktree_status(root: Path) -> str:
    r = subprocess.run(['git', '-C', str(root), 'status', '--porcelain',
                        '--untracked-files=all'], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or 'git status 失敗')
    return r.stdout.strip()


def require_clean(root: Path) -> None:
    """開始之前工作樹必須乾淨。

    否則審查後的「有改動」無法與「我自己編輯過」區分 —— 零改動不變式失去意義。
    這個檢查必須在**執行審查之前**，不是之後：審查一旦跑過，事情已經發生了。
    """
    dirty = worktree_status(root)
    if dirty:
        raise DirtyWorktree(
            '工作樹不乾淨，拒絕開始審查：\n'
            + '\n'.join('  ' + l for l in dirty.splitlines())
            + '\n\n  否則「審查後有改動」無法與「你自己的編輯」區分，零改動的保證就沒有意義。\n'
              '  請先 commit 或 stash。')


def codex_command(cfg: config.Config, prompt_file: Path) -> list[str]:
    """組出送給審查者的指令。沙箱參數固定。"""
    cmd = ['codex', 'exec']
    if cfg.session_id:
        cmd += ['resume', cfg.session_id]
    cmd += [*SANDBOX_ARGS, *REASONING_ARGS, prompt_file.read_text(encoding='utf-8')]
    return cmd


def start(root: Path, cfg: config.Config, message: str, *, spawn=None) -> dict:
    """送出一輪，**立即返回**（R5）。

    實際工作交給 worker 子行程：它負責前後快照、呼叫審查者、寫判定。
    這裡不等待 —— 一輪可能超過十分鐘。
    """
    require_clean(root)
    archive_dir = root / cfg.archive_dir
    n = archive.next_round(archive_dir)
    paths = archive.claim(archive_dir, n)

    paths['prompt'].write_text(config.compose(cfg.constraint, message), encoding='utf-8')
    own = own_paths(root, paths)
    before = snapshot.take(root, own)
    state = {'round': n, 'state': 'running', 'before': before, 'own': sorted(own)}
    paths['verdict'].write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

    spawn = spawn or _spawn_worker
    pid = spawn(root, cfg, n)
    state['pid'] = pid
    paths['verdict'].write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'round': n, 'pid': pid, 'prompt': paths['prompt'], 'reply': paths['reply']}


def _spawn_worker(root: Path, cfg: config.Config, n: int) -> int:
    p = subprocess.Popen(
        [sys.executable, '-m', 'codexreview.worker', str(n)],
        cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    return p.pid
