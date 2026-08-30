"""codex-review —— 對抗性審查迴圈的執行器。

它負責**證據**，不負責判斷：證明審查者沒有動過 repository，其餘留給人。
"""
__all__ = ['snapshot', 'config', 'archive', 'verdict', 'runner']
