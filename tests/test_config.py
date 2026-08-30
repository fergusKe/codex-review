"""R3：約束區塊注入。"""
import json
from codexreview import config
from .helpers import RepoCase


class ConfigTests(RepoCase):

    def test_t3_1_constraint_comes_first(self):
        """約束放最前面：審查者最先讀到的東西決定它整輪的行為邊界。"""
        composed = config.compose('不得修改本 repository。', '請看第五輪的三個 blocker。')
        self.assertTrue(composed.startswith('不得修改本 repository。'))
        self.assertIn('請看第五輪的三個 blocker。', composed)
        self.assertLess(composed.index('不得修改'), composed.index('第五輪'))

    def test_t3_2_missing_constraint_is_refused(self):
        (self.r / '.codex-review.json').write_text(json.dumps({'session_id': 'x'}),
                                                    encoding='utf-8')
        with self.assertRaises(config.ConfigError) as cm:
            config.Config.load(self.r)
        self.assertIn('constraint', str(cm.exception))

    def test_t3_3_empty_constraint_is_refused(self):
        """**空約束等於沒有約束。** 允許它會產生一個看起來有防護的空殼。"""
        for empty in ('', '   ', '\n\t '):
            (self.r / '.codex-review.json').write_text(json.dumps({'constraint': empty}),
                                                        encoding='utf-8')
            with self.assertRaises(config.ConfigError):
                config.Config.load(self.r)

    def test_missing_config_file_is_refused(self):
        with self.assertRaises(config.ConfigError) as cm:
            config.Config.load(self.r)
        self.assertIn('.codex-review.json', str(cm.exception))

    def test_control_valid_config_loads(self):
        self.write_config(constraint='不得修改。', session_id='s1', archive_dir='rounds')
        cfg = config.Config.load(self.r)
        self.assertEqual((cfg.constraint, cfg.session_id, cfg.archive_dir),
                         ('不得修改。', 's1', 'rounds'))
