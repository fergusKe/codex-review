"""Merge Protection 實測用的故意失敗測試 —— 驗證完就刪掉這個檔案與分支。

見 workflow/MERGE-PROTECTION.md〈驗證：沒實測過的防線不算防線〉。
它同時扮演兩個角色：
  1. 一條紅掉的 required check（讓 merge 按鈕該變灰）
  2. 一筆未經批准的產品變更（讓 control-plane-audit 該擋下來）
"""
import unittest


class MergeProtectionDrill(unittest.TestCase):
    def test_deliberately_failing(self):
        self.assertEqual(1, 2, '這條是實測用的，本來就該紅')
