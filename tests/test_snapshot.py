"""R1：完整性快照必須涵蓋未追蹤檔案。"""
from codexreview import snapshot
from .helpers import RepoCase


class SnapshotTests(RepoCase):

    def test_t1_1_untracked_file_is_detected(self):
        """**本工具存在的理由。**

        原本的手動流程用 `git ls-files`，它只列 tracked 檔案 —— 審查者新增一個
        未追蹤檔案時，前後快照完全相同，使用者會得到「零改動」的結論。
        這個洞在十九輪審查裡從未被觸發，那不等於它被檢查過。
        """
        before = snapshot.take(self.r)
        (self.r / 'rogue.txt').write_text('審查者偷偷留下的東西\n', encoding='utf-8')
        diff = snapshot.compare(before, snapshot.take(self.r))
        self.assertTrue(diff.changed, '未追蹤的新檔案必須被偵測到')
        self.assertIn('rogue.txt', diff.added)

    def test_t1_2_modified_file_is_detected(self):
        before = snapshot.take(self.r)
        (self.r / 'a.txt').write_text('changed\n', encoding='utf-8')
        diff = snapshot.compare(before, snapshot.take(self.r))
        self.assertEqual(diff.modified, ('a.txt',))
        self.assertFalse(diff.added or diff.removed, '改內容不該被歸類成新增或刪除')

    def test_t1_3_deleted_file_is_detected(self):
        before = snapshot.take(self.r)
        (self.r / 'a.txt').unlink()
        diff = snapshot.compare(before, snapshot.take(self.r))
        self.assertEqual(diff.removed, ('a.txt',))

    def test_t1_4_control_no_change_is_clean(self):
        """對照組。收緊不能把「什麼都沒做」也判成有改動。"""
        self.assertFalse(snapshot.compare(snapshot.take(self.r), snapshot.take(self.r)).changed)

    def test_t1_5_gitignored_paths_are_excluded(self):
        """build 產物不該製造假警報 —— 那會讓人學會忽略這個工具。"""
        (self.r / '.gitignore').write_text('build/\n', encoding='utf-8')
        self.commit_all('ignore build')
        before = snapshot.take(self.r)
        (self.r / 'build').mkdir()
        (self.r / 'build' / 'out.bin').write_text('x', encoding='utf-8')
        self.assertFalse(snapshot.compare(before, snapshot.take(self.r)).changed,
                         'gitignored 路徑不得進入快照')

    def test_absent_and_empty_are_distinguishable(self):
        """缺檔與空檔必須可區分，否則刪掉檔案就等於通過。"""
        (self.r / 'empty.txt').write_text('', encoding='utf-8')
        empty = snapshot.digest_of(self.r, 'empty.txt')
        absent = snapshot.digest_of(self.r, 'no-such-file.txt')
        self.assertNotEqual(empty, absent)
        self.assertEqual(absent, snapshot.ABSENT)
