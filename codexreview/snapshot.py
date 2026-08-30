"""完整性快照（R1）。"""
from __future__ import annotations
import hashlib, subprocess
from dataclasses import dataclass
from pathlib import Path

ABSENT = '<absent>'


def _git(root: Path, *args: str) -> bytes:
    r = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode('utf-8', 'replace').strip() or f'git {args[0]} 失敗')
    return r.stdout


def tracked_and_untracked(root: Path) -> list[str]:
    """工作樹中所有**非 ignored** 的檔案。

    這裡是本工具存在的理由。原本手動流程用的是：

        git ls-files -z | xargs -0 shasum -a 256

    而 `git ls-files` **只列 tracked 檔案**。審查者若新增一個未追蹤的檔案，
    前後兩份快照完全相同，使用者會得到「零改動」的結論。這個洞在十九輪審查裡
    從未被觸發 —— 那不等於它被檢查過。

    `--others --exclude-standard` 補上未追蹤但未被 ignore 的檔案；
    ignored 的（build 產物、node_modules）刻意排除，否則會製造假警報。
    """
    out = _git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z')
    return sorted({p for p in out.decode('utf-8', 'surrogateescape').split('\0') if p})


def digest_of(root: Path, rel: str) -> str:
    """單一檔案的指紋。讀不到（已刪除、權限）回 ABSENT —— 缺檔與空檔必須可區分。"""
    try:
        return hashlib.sha256((root / rel).read_bytes()).hexdigest()
    except OSError:
        return ABSENT


def take(root: Path, exclude: frozenset[str] = frozenset()) -> dict[str, str]:
    """快照。`exclude` 是**本工具自己這一輪會寫的檔案**。

    為什麼要有 exclude，而且為什麼不能直接排除整個歸檔目錄：
    工具會寫入本輪的 prompt / reply / verdict，那些是自己的產物，算進去會讓每一輪
    都變成 TAMPERED。但**其他輪次的歸檔仍必須被涵蓋** —— 審查者去改舊輪次的紀錄
    正是最該被抓到的事。所以排除的是精確的三個路徑，不是一個目錄。
    """
    return {rel: digest_of(root, rel)
            for rel in tracked_and_untracked(root) if rel not in exclude}


@dataclass(frozen=True)
class Diff:
    added: tuple[str, ...]
    removed: tuple[str, ...]
    modified: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted({*self.added, *self.removed, *self.modified}))

    def describe(self) -> str:
        lines = []
        for label, group in (('新增', self.added), ('刪除', self.removed), ('修改', self.modified)):
            for p in group:
                lines.append(f'  {label}: {p}')
        return '\n'.join(lines)


def compare(before: dict[str, str], after: dict[str, str]) -> Diff:
    """before → after 的差異。

    「檔案存在但內容變成 ABSENT」算刪除，而不是修改 —— 兩者對使用者的意義不同。
    """
    added, removed, modified = [], [], []
    for rel in sorted(set(before) | set(after)):
        b, a = before.get(rel), after.get(rel)
        if b == a:
            continue
        if b is None or b == ABSENT:
            added.append(rel)
        elif a is None or a == ABSENT:
            removed.append(rel)
        else:
            modified.append(rel)
    return Diff(tuple(added), tuple(removed), tuple(modified))
