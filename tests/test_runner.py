"""R2：乾淨工作樹前置檢查。R7：唯讀沙箱不可放寬。"""
from codexreview import config, runner
from .helpers import RepoCase


class CleanWorktreeTests(RepoCase):

    def setUp(self):
        super().setUp()
        self.write_config()
        self.commit_all('config')
        self.spawned = []

    def _spy(self, root, cfg, n):
        self.spawned.append(n)
        return 12345

    def test_t2_1_modified_file_blocks_start(self):
        (self.r / 'a.txt').write_text('dirty\n', encoding='utf-8')
        with self.assertRaises(runner.DirtyWorktree):
            runner.start(self.r, config.Config.load(self.r), 'msg', spawn=self._spy)
        self.assertEqual(self.spawned, [],
                         '**審查不得被執行。** 只檢查 exit code 的話，'
                         '把檢查搬到執行之後也會通過測試。')

    def test_t2_2_untracked_file_blocks_start(self):
        (self.r / 'new.txt').write_text('x', encoding='utf-8')
        with self.assertRaises(runner.DirtyWorktree):
            runner.start(self.r, config.Config.load(self.r), 'msg', spawn=self._spy)
        self.assertEqual(self.spawned, [])

    def test_t2_3_control_clean_worktree_proceeds(self):
        info = runner.start(self.r, config.Config.load(self.r), 'msg', spawn=self._spy)
        self.assertEqual(self.spawned, [1], '乾淨時必須真的送出，否則這個檢查只是把工具關掉')
        self.assertEqual(info['round'], 1)
        self.assertTrue(info['prompt'].exists())

    def test_dirty_message_names_the_offending_paths(self):
        (self.r / 'a.txt').write_text('dirty\n', encoding='utf-8')
        with self.assertRaises(runner.DirtyWorktree) as cm:
            runner.require_clean(self.r)
        self.assertIn('a.txt', str(cm.exception), '訊息要指出是哪個檔案，否則使用者得自己去猜')


class SandboxTests(RepoCase):

    def test_t7_1_command_always_carries_readonly_sandbox(self):
        self.write_config(session_id='abc-123')
        self.commit_all('config')
        cfg = config.Config.load(self.r)
        p = self.r / 'prompt.md'
        p.write_text('hello', encoding='utf-8')
        cmd = runner.codex_command(cfg, p)
        self.assertIn('sandbox_mode="read-only"', cmd)
        self.assertIn('resume', cmd)
        self.assertIn('abc-123', cmd)

    def test_t7_2_no_interface_can_relax_the_sandbox(self):
        """**負向能力測試。**

        證明的是「做不到」，不是「預設不做」。一個能被旗標關掉的防線不是防線 ——
        而會去關它的人，多半正是最不該關它的那個。
        """
        from codexreview import cli
        parser = cli.build_parser()
        for hostile in (['run', '-m', 'x', '--sandbox', 'danger-full-access'],
                        ['run', '-m', 'x', '--unsafe'],
                        ['run', '-m', 'x', '--sandbox-mode', 'write']):
            with self.assertRaises(SystemExit, msg=f'{hostile} 不得被接受'):
                parser.parse_args(hostile)
        # 而且原始碼裡不存在任何可寫沙箱的字串
        src = (__import__('pathlib').Path(runner.__file__)).read_text(encoding='utf-8')
        for bad in ('danger-full-access', 'workspace-write'):
            self.assertNotIn(bad, src)
