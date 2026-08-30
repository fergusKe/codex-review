"""R8/R9/R10：出貨的設定檔與 CI workflow。

**這些是靜態斷言，證明的是「這份設定說了它會做那件事」，不是「GitHub 真的做了」。**
後者只能由伺服器端失敗實測證明（見 workflow/test-cases/enable-ci-and-self-use.md
〈本輪測不到的部分〉）。唯一的例外是 T10.7 —— 它直接執行稽核程式本身。

不引入 PyYAML：本專案 `Package manager: none`，為了三條斷言加一個相依不划算。
代價是這裡用文字比對，所以每條正向斷言都配一個對照組（T8.5/T9.5/T10.6），
確保它在防線被拿掉時真的會紅。
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / '.codex-review.json'
WORKFLOWS = ROOT / '.github/workflows'

# 吞掉失敗的旗標。CI 有跑但不會擋，比沒有 CI 更糟 —— 它會產生一個假的綠燈。
SWALLOW_RE = re.compile(r'continue-on-error:\s*true|\|\|\s*true\s*$|\|\|\s*exit\s+0\s*$', re.M)


def workflow_texts() -> dict[str, str]:
    return {p.name: p.read_text(encoding='utf-8')
            for p in sorted(WORKFLOWS.glob('*.yml')) + sorted(WORKFLOWS.glob('*.yaml'))}


def profile_field(name: str) -> str | None:
    """從 PROJECT-PROFILE.md 讀一個欄位。刻意不寫死指令字串 —— 見 T9.3。"""
    txt = (ROOT / 'PROJECT-PROFILE.md').read_text(encoding='utf-8')
    m = re.search(rf'(?m)^-?\s*`?{re.escape(name)}`?:\s*(.+?)\s*$', txt)
    return m.group(1).strip('`').strip() if m else None


# 本機絕對路徑的起頭。出貨的設定檔含這些，等於把作者的目錄結構寫進 public repo，
# 而且換一個資料夾名稱就失效。
ABS_PATH_RE = re.compile(r'/Users/|/home/|/root/|[A-Za-z]:[\\/]')


def constraint_is_meaningful(constraint: str) -> bool:
    """T8.3 的判準，抽成函式讓對照組 T8.5 能直接套用在被竄改的內容上。

    要求同時命中「禁止修改的意思」與「受審 repository 的範圍指稱」——
    只檢查非空的話，一個寫著 "TODO" 的約束會通過。

    **範圍指稱刻意不綁檔案系統位置。** 第一版判準要求含絕對路徑，
    結果在 `git worktree` 裡基準線就是紅的，任何非同名的 clone 也一樣 ——
    見 workflow/test-cases/enable-ci-and-self-use.md 的 T8.3 註記。
    """
    has_scope = any(k in constraint for k in ('本 repository', '本專案', 'codex-review'))
    has_prohibition = any(k in constraint for k in ('不得修改', '不要修改', '禁止修改'))
    return has_scope and has_prohibition


class ShippedConfig(unittest.TestCase):
    """R8：專案自帶可用的設定檔。"""

    def setUp(self):
        self.assertTrue(CONFIG.exists(), f'{CONFIG.name} 不存在')
        self.raw = json.loads(CONFIG.read_text(encoding='utf-8'))

    def test_T8_1_parses_and_has_constraint(self):
        self.assertIn('constraint', self.raw)

    def test_T8_2_constraint_non_empty(self):
        self.assertTrue(self.raw['constraint'].strip())

    def test_T8_3_constraint_actually_prohibits_modification(self):
        self.assertTrue(constraint_is_meaningful(self.raw['constraint']),
                        '約束必須同時指明本 repository 與「不得修改」，否則注入的是空話')

    def test_T8_4_status_works_on_clean_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / 'copy'
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns('.git', '__pycache__', 'reviews'))
            r = subprocess.run([sys.executable, '-m', 'codexreview.cli', 'status'],
                               cwd=dst, capture_output=True, text=True,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_T8_5_placeholder_constraint_is_rejected(self):
        """對照組。沒有這條，T8.3 可以退化成 T8.2 而沒人發現。"""
        self.assertFalse(constraint_is_meaningful('TODO'))
        self.assertFalse(constraint_is_meaningful('請填入約束'))
        # 只有範圍、沒有禁止；以及只有禁止、沒有範圍 —— 兩者都不該通過。
        self.assertFalse(constraint_is_meaningful('本 repository 是 codex-review'))
        self.assertFalse(constraint_is_meaningful('不得修改任何東西'))

    def test_T8_6_constraint_has_no_local_absolute_path(self):
        """出貨的設定檔會被 clone 到別人的機器上，路徑寫死就失效。

        這條是 T8.3 第一版判準留下的疤：把當時的 bug 變成以後過不去的守衛。
        """
        m = ABS_PATH_RE.search(self.raw['constraint'])
        self.assertIsNone(m, f'constraint 含本機絕對路徑：{m.group(0) if m else ""}')
        # 判準本身要真的抓得到，否則這是一條永遠綠的斷言。
        for bad in ('請勿修改 /Users/someone/repo 底下的檔案',
                    '不得修改 /home/ci/work 的內容',
                    '不得修改 C:\\src\\proj'):
            with self.subTest(bad=bad):
                self.assertIsNotNone(ABS_PATH_RE.search(bad))


class TestWorkflow(unittest.TestCase):
    """R9：CI 執行完整測試套件。"""

    def setUp(self):
        self.texts = workflow_texts()
        self.assertTrue(self.texts, '.github/workflows/ 下沒有任何 workflow')
        cmd = profile_field('Custom verification command')
        self.assertTrue(cmd, 'PROJECT-PROFILE.md 缺 Custom verification command')
        self.cmd = cmd
        self.test_wf = [t for t in self.texts.values() if self.cmd in t]

    def test_T9_1_and_T9_3_runs_the_profile_verification_command(self):
        """指令從 profile 讀出來比對。寫死的話，改了 profile 忘了改 CI，測試照樣綠。"""
        self.assertTrue(self.test_wf,
                        f'沒有任何 workflow 執行 profile 宣告的驗證指令：{self.cmd}')

    def test_T9_2_triggers_on_push_and_pull_request(self):
        t = self.test_wf[0]
        self.assertRegex(t, r'(?m)^\s*push:', 'workflow 未在 push 觸發')
        self.assertRegex(t, r'(?m)^\s*pull_request:', 'workflow 未在 pull_request 觸發')

    def test_T9_4_no_failure_swallowing_flags(self):
        for name, t in self.texts.items():
            with self.subTest(workflow=name):
                self.assertIsNone(SWALLOW_RE.search(t),
                                  f'{name} 含吞掉失敗的旗標；CI 有跑但不會擋等於假綠燈')

    def test_T9_5_swallowing_flag_would_be_caught(self):
        """對照組：確認 T9.4 的判準真的抓得到，而不是一個永遠不觸發的 regex。"""
        for bad in ('    continue-on-error: true\n',
                    '      run: pytest || true\n',
                    '      run: pytest || exit 0\n'):
            with self.subTest(bad=bad.strip()):
                self.assertIsNotNone(SWALLOW_RE.search(bad))


class AuditWorkflow(unittest.TestCase):
    """R10：Control Plane 稽核成為 required check。"""

    AUDIT = 'workflow/bin/audit-control-plane.py'

    def setUp(self):
        self.texts = workflow_texts()
        self.audit_wf = [(n, t) for n, t in self.texts.items() if self.AUDIT in t]
        # **在 setUp 就擋住空清單。** 少了這一行，下面每個 for 迴圈在沒有稽核
        # workflow 時完全不執行迴圈體 —— 測試全綠，卻什麼都沒驗到。
        # 這正是本專案一路在抓的那類假綠燈，不能在自己的驗收上犯。
        self.assertTrue(self.audit_wf, f'沒有任何 workflow 執行 {self.AUDIT}')

    def test_T10_1_and_T10_2_audit_workflow_invokes_the_script(self):
        self.assertTrue(self.audit_wf, f'沒有任何 workflow 執行 {self.AUDIT}')

    def test_T10_3_checkout_has_full_history(self):
        """`fetch-depth: 0` 沒設的話，runner 只 checkout 一個 commit，
        merge-base 算不出來，稽核會因為算不出範圍而略過 —— 一個永遠綠的 required check。"""
        for name, t in self.audit_wf:
            with self.subTest(workflow=name):
                self.assertRegex(t, r'(?m)^\s*fetch-depth:\s*0\s*$',
                                 f'{name} 的 checkout 未取得完整歷史')

    def test_T10_4_audit_starts_from_merge_base(self):
        for name, t in self.audit_wf:
            with self.subTest(workflow=name):
                self.assertIn('merge-base', t, f'{name} 未以 merge-base 為稽核起點')
                self.assertNotRegex(t, r'HEAD~1\b', f'{name} 使用固定的 HEAD~1 作為起點')

    def test_T10_6_missing_fetch_depth_would_be_caught(self):
        """對照組。"""
        without = re.compile(r'(?m)^\s*fetch-depth:\s*0\s*$')
        self.assertIsNone(without.search('      - uses: actions/checkout@v4\n'))
        self.assertIsNotNone(without.search('      - uses: actions/checkout@v4\n'
                                            '        with:\n          fetch-depth: 0\n'))

    def test_T10_7_audit_rejects_unauthorized_product_change(self):
        """端到端：不靠 YAML 文字，直接跑稽核程式，證明它**真的會拒絕**。

        沒有這條，前面六條加起來只證明了一份設定檔的字面內容。
        """
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / 'repo'
            shutil.copytree(ROOT / 'workflow', repo / 'workflow')
            # STATE 改成 DISCOVERY：任何產品變更在此階段都未被授權。
            sp = repo / 'workflow/STATE.md'
            txt = sp.read_text(encoding='utf-8')
            txt = re.sub(r'(?m)^Phase: .*$', 'Phase: DISCOVERY', txt)
            txt = re.sub(r'(?m)^(Spec approved|Test design approved|Verification passed): .*$',
                         r'\1: no', txt)
            txt = re.sub(r'(?m)^(Approved \w+ digest|Approved by|Active OpenSpec change): .*$',
                         r'\1: none', txt)
            sp.write_text(txt, encoding='utf-8')
            git = lambda *a: subprocess.run(['git', '-C', str(repo), *a],
                                            check=True, capture_output=True, text=True)
            git('init', '-b', 'main')
            git('config', 'user.email', 't@example.invalid'); git('config', 'user.name', 'T')
            git('add', '-A'); git('commit', '-m', 'baseline')
            base = git('rev-parse', 'HEAD').stdout.strip()
            (repo / 'codexreview').mkdir()
            (repo / 'codexreview/rogue.py').write_text('# 未經批准的產品變更\n', encoding='utf-8')
            git('add', '-A'); git('commit', '--no-verify', '-m', 'rogue')
            r = subprocess.run([sys.executable, str(repo / 'workflow/bin/audit-control-plane.py'),
                                base, 'HEAD'],
                               cwd=repo, capture_output=True, text=True,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            self.assertNotEqual(r.returncode, 0,
                                '稽核放行了未經批准的產品變更：\n' + r.stdout + r.stderr)


# TR.2（比對第一輪封存 commit）已移除，由 tests/test_core_manifest.py 的 T11.2 取代。
# 鎖的對象從「歷史上的某個 commit」換成「一份 checked-in 的紀錄」——
# 因為前者需要祖先歷史，而 CI 的 checkout 是淺的。取捨寫在 R11。


if __name__ == '__main__':
    unittest.main()
