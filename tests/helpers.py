import shutil, subprocess, tempfile, unittest
from pathlib import Path


class RepoCase(unittest.TestCase):
    """每個測試一個乾淨的 git repository。"""

    def setUp(self):
        self.td = Path(tempfile.mkdtemp(prefix='cr-test-'))
        self.r = self.td / 'repo'
        self.r.mkdir()
        for c in (['init', '-b', 'main'], ['config', 'user.email', 't@example.invalid'],
                  ['config', 'user.name', 'T']):
            subprocess.run(['git', '-C', str(self.r), *c], check=True, capture_output=True)
        (self.r / 'a.txt').write_text('a\n', encoding='utf-8')
        self.commit_all('baseline')

    def tearDown(self):
        shutil.rmtree(self.td, ignore_errors=True)

    def commit_all(self, msg):
        subprocess.run(['git', '-C', str(self.r), 'add', '-A'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.r), 'commit', '-m', msg], check=True, capture_output=True)

    def write_config(self, constraint='不得修改本 repository。', **extra):
        import json
        data = {'constraint': constraint, **extra}
        (self.r / '.codex-review.json').write_text(json.dumps(data, ensure_ascii=False),
                                                   encoding='utf-8')
