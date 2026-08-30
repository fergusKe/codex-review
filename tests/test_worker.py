"""R5 + R6 的整合：背景 worker 走完一輪並寫下判定。"""
import json
from codexreview import archive, config, runner, verdict, worker
from .helpers import RepoCase


class WorkerTests(RepoCase):

    def setUp(self):
        super().setUp()
        self.write_config()
        self.commit_all('config')
        self.cfg = config.Config.load(self.r)

    def _start(self):
        return runner.start(self.r, self.cfg, '請審查', spawn=lambda *a: 999)

    def test_t5_1_start_returns_without_running_the_review(self):
        """一輪可能超過十分鐘，送出必須立即返回。"""
        calls = []
        info = runner.start(self.r, self.cfg, 'msg', spawn=lambda *a: calls.append(1) or 42)
        self.assertEqual(info['pid'], 42)
        self.assertFalse(info['reply'].exists(), '回覆要等 worker 寫入，不是同步等出來的')

    def test_t5_2_status_reports_running_before_completion(self):
        info = self._start()
        st = json.loads(archive.paths_for(self.r / 'reviews', info['round'])['verdict']
                        .read_text(encoding='utf-8'))
        self.assertEqual(st['state'], 'running')

    def test_t5_3_completed_round_archives_reply_and_verdict(self):
        info = self._start()
        v = worker.run_round(self.r, info['round'],
                             execute=lambda cmd, root: (True, '審查者的回覆內容'))
        self.assertEqual(v.result, verdict.CLEAN)
        self.assertEqual(info['reply'].read_text(encoding='utf-8'), '審查者的回覆內容')
        st = json.loads(archive.paths_for(self.r / 'reviews', info['round'])['verdict']
                        .read_text(encoding='utf-8'))
        self.assertEqual((st['state'], st['result']), ('done', verdict.CLEAN))

    def test_worker_detects_tampering_by_the_reviewer(self):
        """端到端：審查者在執行期間新增了未追蹤檔案。"""
        info = self._start()

        def naughty(cmd, root):
            (root / 'reviewer-left-this.txt').write_text('oops', encoding='utf-8')
            return True, 'reply'

        v = worker.run_round(self.r, info['round'], execute=naughty)
        self.assertEqual(v.result, verdict.TAMPERED)
        self.assertIn('reviewer-left-this.txt', v.detail)

    def test_worker_reports_incomplete_when_review_fails(self):
        info = self._start()
        v = worker.run_round(self.r, info['round'],
                             execute=lambda cmd, root: (False, '額度不足'))
        self.assertEqual(v.result, verdict.INCOMPLETE)
        self.assertEqual(info['reply'].read_text(encoding='utf-8'), '額度不足')

    def test_other_rounds_archives_are_still_covered(self):
        """**排除的範圍必須精確。**

        工具自己會寫本輪的 prompt / reply / verdict，那些算進快照會讓每一輪都變成
        TAMPERED（實作時真的發生過，被 T5.3 抓到）。但修法不能是「排除整個歸檔目錄」
        —— 審查者去改**舊輪次**的紀錄正是最該被抓到的事。

        少了這條測試，把 exclude 放寬成整個目錄仍然全綠。
        """
        first = self._start()
        worker.run_round(self.r, first['round'],
                         execute=lambda cmd, root: (True, '第一輪回覆'))
        self.commit_all('archive round 1')
        second = self._start()

        def tamper_old_round(cmd, root):
            first['reply'].write_text('被竄改的第一輪回覆', encoding='utf-8')
            return True, '第二輪回覆'

        v = worker.run_round(self.r, second['round'], execute=tamper_old_round)
        self.assertEqual(v.result, verdict.TAMPERED,
                         '改動舊輪次的歸檔必須被偵測')
        self.assertIn('round-001.reply.md', v.detail)
