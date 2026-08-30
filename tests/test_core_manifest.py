"""R11 / R12：內容鎖與「不依賴 checkout 深度」。

本輪存在的理由是同一類錯誤第二次出現 —— 測試依賴了本機環境**碰巧**成立的性質：

    T8.3（上一輪）  工作目錄剛好叫 codex-review    → 換個資料夾就紅
    TR.2（本輪）    本機剛好有完整 git 歷史        → 淺 checkout 就紅

R11 修好已知的那一條；**R12 是會抓到下一次的守衛**。
"""
from __future__ import annotations
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'core-manifest.txt'

# 產生器的檔名有連字號，不能直接 import —— 但**測試必須用出貨的那一份**，
# 不能在測試裡複製一份判準；複製出來的那份永遠會過。
_spec = importlib.util.spec_from_file_location('gen_core_manifest', ROOT / 'tools/gen-core-manifest.py')
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

# 子行程旗標：T12 會在淺 clone 裡再跑一次整套測試，而整套包含 T12 自己。
CHILD = os.environ.get('CODEX_REVIEW_SHALLOW_CHILD') == '1'


def mismatches(recorded: dict[str, str], actual: dict[str, str]) -> list[str]:
    """判準本體。抽成函式，讓對照組 T11.3 / T11.4 能直接套用在被竄改的紀錄上。"""
    out = []
    for p in sorted(set(recorded) | set(actual)):
        if p not in recorded:
            out.append(f'未記錄：{p}')
        elif p not in actual:
            out.append(f'已消失：{p}')
        elif recorded[p] != actual[p]:
            out.append(f'內容不符：{p}')
    return out


class CoreManifest(unittest.TestCase):
    """R11：鎖的對象是一份 checked-in 的紀錄，不是歷史上的某個 commit。"""

    def setUp(self):
        self.assertTrue(MANIFEST.exists(), 'core-manifest.txt 不存在')
        self.recorded = gen.parse(MANIFEST.read_text(encoding='utf-8'))
        self.actual = gen.index_entries(ROOT)
        # 空清單會讓下面每一條斷言都變成真空通過 —— 在 setUp 就擋掉。
        self.assertTrue(self.recorded, 'manifest 沒有任何一筆紀錄')
        self.assertTrue(self.actual, 'index 裡沒有任何 codexreview/ 檔案')

    def test_T11_1_manifest_parses(self):
        for path, blob in self.recorded.items():
            self.assertTrue(path.startswith('codexreview/'), f'鎖的範圍之外：{path}')
            self.assertRegex(blob, r'^[0-9a-f]{40}$', f'不是 blob hash：{path}')

    def test_T11_2_manifest_matches_current_tree(self):
        """**這條測試不得使用任何需要祖先歷史的指令。**

        `git ls-files -s` 讀 index，在淺 clone 上一樣完整。R12 會實際去證明
        這個性質，而不是靠掃描原始碼找 `git log` 字樣。
        """
        self.assertEqual(mismatches(self.recorded, self.actual), [],
                         'codexreview/ 與 core-manifest.txt 不一致；'
                         '若這是有意的變更，跑 tools/gen-core-manifest.py --write')

    def test_T11_3_missing_entry_is_rejected(self):
        """對照組：紀錄少一筆。沒有這條，T11.2 可能退化成一個永遠不比對的迴圈。"""
        mutated = dict(self.recorded)
        mutated.pop(sorted(mutated)[0])
        self.assertNotEqual(mismatches(mutated, self.actual), [])

    def test_T11_4_tampered_hash_is_rejected(self):
        """對照組：改掉一個 hash。"""
        mutated = dict(self.recorded)
        k = sorted(mutated)[0]
        mutated[k] = '0' * 40
        self.assertNotEqual(mismatches(mutated, self.actual), [])

    def test_T11_5_generator_is_reproducible(self):
        """產生器的輸出必須與 checked-in 的檔案逐位元組相同。

        一份沒有人知道怎麼重新產生的鎖，第一次正當變更時就會被整條刪掉 ——
        而刪掉的過程看起來會很合理。這條測試是它不變成死檔的唯一保證。
        """
        self.assertEqual(gen.render(self.actual), MANIFEST.read_text(encoding='utf-8'))


def _materialize_index(dest: Path) -> None:
    """把 **index** 具現化成一個只有單一 commit、沒有任何祖先歷史的 repository。

    **檢查的對象必須是 index，不是 HEAD。** 原本這裡寫的是
    `git clone --depth 1 file://<ROOT>` —— clone 的是 HEAD，而 pre-commit 執行時
    HEAD 還是上一個 commit。結果是這道守衛在一個目前違反它的 repository 裡
    永遠裝不進去：修正它的那個 commit 會被自己擋下來，唯一出路是 `--no-verify`。

    順帶也避開另一個陷阱：`git clone --depth 1 /本機路徑` 會走 hardlink 捷徑並
    直接忽略 `--depth`，非得用 `file://` 才會真的變淺。
    """
    def git(*a, cwd=None):
        return subprocess.run(['git', '-C', str(cwd or dest), *a],
                              check=True, capture_output=True, text=True)
    dest.mkdir(parents=True)
    subprocess.run(['git', '-C', str(ROOT), 'checkout-index', '-a', '--prefix=' + str(dest) + '/'],
                   check=True, capture_output=True, text=True)
    git('init', '-q', '-b', 'main')
    git('config', 'user.email', 't@example.invalid')
    git('config', 'user.name', 'T')
    git('add', '-A')
    # `--no-verify`：這裡是一個一次性的暫存 repository，不是受保護的樹；
    # 而且它剛複製過來的 .githooks 會再觸發一次完整套件，形成遞迴。
    git('commit', '-q', '--no-verify', '-m', 'materialized index')


def _run_suite(cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CODEX_REVIEW_SHALLOW_CHILD='1')
    return subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', '.', '-p', 'test_*.py'],
                          cwd=cwd, capture_output=True, text=True, env=env)


def _quote(r: subprocess.CompletedProcess) -> str:
    """把子行程的輸出每行加上 `| ` 前綴。

    子行程跑的是同一套測試，它的 `FAIL: test_...` 行與外層的長得一模一樣。
    直接貼進失敗訊息裡，任何掃輸出判斷「哪幾條測試紅了」的工具都會把子行程的
    失敗算到外層頭上 —— 突變測試的結果會因此完全失真。實測踩過一次。
    """
    return '\n'.join('| ' + l for l in (r.stdout + r.stderr).splitlines())


@unittest.skipIf(CHILD, '子行程內跳過，避免無限遞迴')
class NoAncestryCheckout(unittest.TestCase):
    """R12：整套測試必須在沒有祖先歷史的 checkout 上跑得完。

    這正是 CI runner 的預設環境（`actions/checkout` 是淺的）。
    用執行的方式證明性質，而不是猜哪些寫法有問題。
    """

    def test_T12_1_and_T12_2_suite_passes_without_ancestry(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / 'materialized'
            _materialize_index(dest)
            # T12.2 —— 先證明它真的沒有祖先歷史。少了這一行，整條測試可能
            # 在一份完整歷史上跑，綠燈而毫無意義。
            n = subprocess.run(['git', '-C', str(dest), 'rev-list', '--count', 'HEAD'],
                               check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(n, '1', f'不是單一 commit（{n} 個），這條測試沒有在驗它宣稱的事')
            r = _run_suite(dest)
            self.assertEqual(r.returncode, 0,
                             '測試套件在無祖先歷史的 checkout 上失敗：\n' + _quote(r))

    def test_T12_3_history_dependent_test_is_caught(self):
        """對照組：放回一條依賴 `git log --grep` 的測試，上面那條必須抓到。

        沒有這條，T12.1 可能因為子行程根本沒跑起來而永遠綠燈。
        """
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / 'materialized'
            _materialize_index(dest)
            (dest / 'tests/test_zz_history_dependent.py').write_text(
                'import subprocess, unittest\n'
                'class HistoryDependent(unittest.TestCase):\n'
                '    def test_needs_ancestry(self):\n'
                "        out = subprocess.run(['git', 'log', '--format=%H', '--grep=archive'],\n"
                '                             capture_output=True, text=True).stdout.strip()\n'
                "        self.assertTrue(out, '找不到封存 commit')\n",
                encoding='utf-8')
            r = _run_suite(dest)
            self.assertNotEqual(r.returncode, 0,
                                '在無祖先歷史的 checkout 上放了一條依賴歷史的測試，套件卻仍然通過 —— '
                                'T12.1 的判準沒有在檢查它宣稱的事')


if __name__ == '__main__':
    unittest.main()
