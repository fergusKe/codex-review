"""設定與約束區塊（R3）。"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_NAME = '.codex-review.json'


class ConfigError(Exception):
    """設定不合法。呼叫端以 exit 3 結束。"""


@dataclass(frozen=True)
class Config:
    constraint: str
    session_id: str | None = None
    archive_dir: str = 'reviews'

    @staticmethod
    def load(root: Path) -> 'Config':
        p = root / CONFIG_NAME
        if not p.exists():
            raise ConfigError(
                f'找不到 {CONFIG_NAME}。\n'
                '  約束區塊必須來自設定檔，不能靠人每輪記得貼 —— 那正是它會被忘記的原因。\n'
                '  請建立設定檔並填入 constraint（不得為空）。')
        try:
            raw = json.loads(p.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ConfigError(f'{CONFIG_NAME} 無法解析：{e}') from e
        constraint = raw.get('constraint')
        if not isinstance(constraint, str) or not constraint.strip():
            raise ConfigError(
                f'{CONFIG_NAME} 的 constraint 缺少或為空。\n'
                '  **空約束等於沒有約束**，不得以此送出。')
        session = raw.get('session_id')
        if session is not None and not isinstance(session, str):
            raise ConfigError('session_id 必須是字串')
        archive = raw.get('archive_dir', 'reviews')
        if not isinstance(archive, str) or not archive.strip():
            raise ConfigError('archive_dir 必須是非空字串')
        return Config(constraint.strip(), session, archive.strip())


def compose(constraint: str, message: str) -> str:
    """送出的內容 = 約束區塊 + 使用者訊息。

    約束放**最前面**：審查者最先讀到的東西決定它整輪的行為邊界。
    """
    return f'{constraint.rstrip()}\n\n---\n\n{message.lstrip()}'
