"""R6：結果判定。"""
from codexreview import verdict
from codexreview.snapshot import Diff
from .helpers import RepoCase

NO_CHANGE = Diff((), (), ())


class VerdictTests(RepoCase):

    def test_t6_1_clean(self):
        v = verdict.decide(True, NO_CHANGE)
        self.assertEqual(v.result, verdict.CLEAN)
        self.assertEqual(v.exit_code, 0)

    def test_t6_2_tampered_is_nonzero_and_lists_paths(self):
        v = verdict.decide(True, Diff(('rogue.txt',), (), ('src/app.py',)))
        self.assertEqual(v.result, verdict.TAMPERED)
        self.assertNotEqual(v.exit_code, 0)
        self.assertIn('rogue.txt', v.detail)
        self.assertIn('src/app.py', v.detail)

    def test_t6_3_tampered_message_states_both_consequences(self):
        """**訊息本身就是這一層的價值。**

        安全上它與 T6.2 冗餘（兩者都以非零 exit 結束），但使用者需要知道
        「還要去清理 repo」，而不只是「這輪白跑了」。少了第二句，
        會有人以為重跑一輪就沒事了。
        """
        detail = verdict.decide(True, Diff(('x',), (), ())).detail
        self.assertIn('審查結論失效', detail)
        self.assertIn('污染', detail)
        self.assertIn('還原', detail)

    def test_t6_4_incomplete_makes_no_integrity_claim(self):
        """審查沒正常結束時**不得做任何完整性宣稱**。

        併進 TAMPERED 會產生假警報，併進 CLEAN 會產生假保證 —— 兩者都更糟。
        """
        v = verdict.decide(False, None)
        self.assertEqual(v.result, verdict.INCOMPLETE)
        self.assertNotEqual(v.exit_code, 0)
        self.assertNotIn('零改動', v.detail)
        self.assertIn('不對 repository 完整性做任何宣稱', v.detail)

    def test_incomplete_even_when_diff_looks_clean(self):
        """審查失敗時，就算快照沒差異也不能說 CLEAN ——
        「沒跑成功」與「跑了而且沒動」是兩件事。"""
        self.assertEqual(verdict.decide(False, NO_CHANGE).result, verdict.INCOMPLETE)
