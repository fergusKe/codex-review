"""輪次編號與歸檔（R4）。"""
from __future__ import annotations
import re
from pathlib import Path

ROUND_RE = re.compile(r'^round-(\d{3})\.(prompt|reply|verdict)\.')


class ArchiveError(Exception):
    """歸檔衝突。呼叫端以 exit 4 結束。"""


def existing_rounds(archive_dir: Path) -> list[int]:
    if not archive_dir.is_dir():
        return []
    out = set()
    for f in archive_dir.iterdir():
        m = ROUND_RE.match(f.name)
        if m:
            out.add(int(m.group(1)))
    return sorted(out)


def next_round(archive_dir: Path) -> int:
    """最大值加一。**不填補空缺** —— 輪次是時間順序，不是索引。

    中間缺號通常代表某一輪被手動刪掉了；重用那個號碼會讓歸檔與實際歷史對不上。
    """
    rounds = existing_rounds(archive_dir)
    return (rounds[-1] + 1) if rounds else 1


def paths_for(archive_dir: Path, n: int) -> dict[str, Path]:
    tag = f'round-{n:03d}'
    return {
        'prompt': archive_dir / f'{tag}.prompt.md',
        'reply': archive_dir / f'{tag}.reply.md',
        'verdict': archive_dir / f'{tag}.verdict.json',
    }


def claim(archive_dir: Path, n: int) -> dict[str, Path]:
    """佔用一組歸檔路徑。任何一個已存在就整組拒絕。

    不覆寫的理由：歸檔是稽核紀錄。一個會覆寫既有紀錄的工具，
    在最需要它的時候（有人想蓋掉某一輪）正好幫了倒忙。
    """
    ps = paths_for(archive_dir, n)
    clash = [p.name for p in ps.values() if p.exists()]
    if clash:
        raise ArchiveError(
            f'第 {n} 輪的歸檔已存在，拒絕覆寫：{"、".join(clash)}\n'
            '  歸檔是稽核紀錄，不得被蓋掉。若確定要重跑，請先自行搬走既有檔案。')
    archive_dir.mkdir(parents=True, exist_ok=True)
    return ps
