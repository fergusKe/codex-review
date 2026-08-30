"""結果判定（R6）。"""
from __future__ import annotations
from dataclasses import dataclass

from .snapshot import Diff

CLEAN = 'CLEAN'
TAMPERED = 'TAMPERED'
INCOMPLETE = 'INCOMPLETE'


@dataclass(frozen=True)
class Verdict:
    result: str
    detail: str

    @property
    def exit_code(self) -> int:
        return 0 if self.result == CLEAN else 1


def decide(review_ok: bool, diff: Diff | None) -> Verdict:
    """三態判定。

    `INCOMPLETE` 存在的理由：審查沒有正常結束時，**不得做任何完整性宣稱**。
    把它併進 TAMPERED 會產生假警報，併進 CLEAN 會產生假保證 —— 兩者都更糟。
    """
    if not review_ok:
        return Verdict(INCOMPLETE,
                       '審查未正常結束，因此**不對 repository 完整性做任何宣稱**。\n'
                       '  請看歸檔的 reply 內容判斷原因（額度、網路、指令錯誤），再重跑這一輪。')
    if diff is None:
        return Verdict(INCOMPLETE, '缺少前後快照，無法判定完整性。')
    if diff.changed:
        return Verdict(TAMPERED,
                       '審查者修改了 repository。**兩件事同時發生：**\n'
                       '  1. 這一輪的審查結論失效 —— 它審的不是你送出的那份內容。\n'
                       '  2. 你的 repository 已被污染 —— 下面每一個路徑都要人工檢視後還原。\n'
                       '  只做第 1 件（重跑一輪）不會解決第 2 件。\n\n'
                       + diff.describe())
    return Verdict(CLEAN, '零改動。審查者只讀未寫，本輪結論可信。')
