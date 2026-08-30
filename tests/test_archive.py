"""R4：輪次編號與防覆寫。"""
from codexreview import archive
from .helpers import RepoCase


class ArchiveTests(RepoCase):

    def setUp(self):
        super().setUp()
        self.a = self.r / 'reviews'

    def _make(self, n):
        self.a.mkdir(exist_ok=True)
        for p in archive.paths_for(self.a, n).values():
            p.write_text(f'round {n}', encoding='utf-8')

    def test_t4_1_first_round_is_one(self):
        self.assertEqual(archive.next_round(self.a), 1)

    def test_t4_2_sequential(self):
        self._make(1); self._make(2)
        self.assertEqual(archive.next_round(self.a), 3)

    def test_t4_3_gap_is_not_backfilled(self):
        """輪次是**時間順序**，不是索引。

        中間缺號通常代表某一輪被手動刪掉；重用那個號碼會讓歸檔與實際歷史對不上。
        """
        self._make(1); self._make(3)
        self.assertEqual(archive.next_round(self.a), 4)

    def test_t4_4_existing_archive_is_never_overwritten(self):
        """歸檔是稽核紀錄。會覆寫它的工具，在最需要它的時候正好幫了倒忙。"""
        self._make(1)
        original = archive.paths_for(self.a, 1)['prompt'].read_text(encoding='utf-8')
        with self.assertRaises(archive.ArchiveError):
            archive.claim(self.a, 1)
        self.assertEqual(archive.paths_for(self.a, 1)['prompt'].read_text(encoding='utf-8'),
                         original, '被拒絕時原檔內容不得改變')

    def test_partial_clash_still_refuses(self):
        """只要有**任何一個**檔案存在就整組拒絕 —— 半個歸檔比沒有更難查。"""
        self.a.mkdir(exist_ok=True)
        archive.paths_for(self.a, 2)['reply'].write_text('half', encoding='utf-8')
        with self.assertRaises(archive.ArchiveError):
            archive.claim(self.a, 2)
