"""Small stdlib regressions for manifest protection and source-family routing."""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.clipping.media_paths import resolve_source, find_ffmpeg

spec = importlib.util.spec_from_file_location('manifest_builder', ROOT / 'scripts/build_fullframe_manifest_20261024.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class MaterialPathTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '_tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='material_paths_test_', dir=ROOT / '_tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, path='video/done/wsy/batch/你好/sample.mp4', *, exists=True, expected=b'original'):
        media = self.root / path
        if exists and '..' not in Path(path).parts:
            media.parent.mkdir(parents=True, exist_ok=True)
            media.write_bytes(b'original')
        row = {'类别': Path(path).parent.name, '输出路径': path, '样本编号': Path(path).stem,
               'part': Path(path).parts[2] if len(Path(path).parts) > 2 else 'wsy'}
        source = self.root / 'source.csv'
        with source.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=builder.FIELDS)
            writer.writeheader(); writer.writerow(row)
        audit = self.root / 'audit.json'
        audit.write_text(json.dumps({'full_manifest': {'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
            'records': [{'path': path, 'sha256': hashlib.sha256(expected).hexdigest(),
                         'label': row['类别'], 'sample_id': row['样本编号'], 'contributor': row['part']}]}), encoding='utf-8')
        return source, audit, self.root / 'new.csv'

    def build(self, fixture, **kwargs):
        return builder.build_manifest(self.root, *fixture, **kwargs)

    def test_verified_subset_keeps_contract_and_ignores_unselected_media(self):
        fixture = self.fixture()
        for path in ['video/inbox/same.mp4', 'video/archive/same.mp4', 'video/done/.cache/extra.mp4']:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(b'original')
        result = self.build(fixture)
        self.assertEqual(result['counts'], {'included': 1})
        self.assertTrue(fixture[2].read_bytes().startswith(b'\xef\xbb\xbf'))
        self.assertEqual(builder.read_rows(fixture[2]), builder.read_rows(fixture[0]))

    def test_inputs_existing_output_and_existing_report_are_protected(self):
        source, audit, target = self.fixture()
        original = source.read_bytes()
        with self.assertRaises(ValueError):
            self.build((source, audit, source))
        self.assertEqual(source.read_bytes(), original)
        target.write_text('do not replace', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            self.build((source, audit, target))
        self.assertEqual(target.read_text(), 'do not replace')
        report = self.root / 'old_report.json'; report.write_text('{}')
        with self.assertRaises(FileExistsError):
            self.build((source, audit, self.root / 'other.csv'), report_path=report)

    def test_missing_default_blocks_and_allow_missing_records_skip(self):
        source, audit, target = self.fixture(exists=False)
        with self.assertRaises(ValueError):
            self.build((source, audit, target))
        self.assertFalse(target.exists())
        report = json.loads(target.with_suffix('.csv.validation.json').read_text())
        self.assertEqual(report['counts'], {'missing': 1})
        result = self.build((source, audit, self.root / 'allowed.csv'), allow_missing=True)
        self.assertTrue(result['success']); self.assertEqual(result['included_rows'], 0)

    def test_shallow_done_layer_is_rejected(self):
        fixture = self.fixture('video/done/你好/sample.mp4')
        with self.assertRaises(ValueError):
            self.build(fixture, allow_missing=True)
        self.assertFalse(fixture[2].exists())

    def test_explicitly_audited_deep_historical_layout_is_preserved(self):
        fixture = self.fixture('video/done/wsy/第2 第3课/第二课学习/你好/sample.mp4')
        result = self.build(fixture)
        self.assertEqual(result['counts'], {'included': 1})
        self.assertEqual(builder.read_rows(fixture[2]), builder.read_rows(fixture[0]))
        self.assertEqual(builder.read_rows(fixture[2])[0]['part'], 'wsy')

    def test_path_escape_cannot_hide_under_allow_missing(self):
        fixture = self.fixture('../escaped.mp4', exists=False)
        with self.assertRaises(ValueError):
            self.build(fixture, allow_missing=True)
        with self.assertRaises(ValueError):
            builder.confined(self.root, self.root.parent / 'outside.csv')

    def test_sha_mismatch_blocks_unless_explicitly_excluded(self):
        source, audit, target = self.fixture(expected=b'other version')
        with self.assertRaises(ValueError):
            self.build((source, audit, target), allow_missing=True)
        self.assertFalse(target.exists())
        self.assertEqual(json.loads(target.with_suffix('.csv.validation.json').read_text())['counts'], {'sha_mismatch': 1})
        result = self.build((source, audit, self.root / 'excluded.csv'), skip_sha_mismatch=True)
        self.assertEqual(result['counts'], {'sha_mismatch': 1}); self.assertEqual(result['included_rows'], 0)

    def test_audit_and_source_manifest_binding_is_checked(self):
        source, audit, target = self.fixture()
        source.write_bytes(source.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'Audit does not describe'):
            self.build((source, audit, target))

    def touch(self, relative):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'fixture')
        return path.resolve()

    def test_same_lesson_bv_and_nl_remain_distinct_and_new_layout_wins(self):
        bv = self.touch('video/raw/BV1Hs411E7aP/BV1Hs411E7aP_p01.mp4')
        nl = self.touch('video/raw/NL_tutorial/P1-lesson.mp4')
        self.touch('video/BV1Hs411E7aP_p01.mp4')
        self.touch('video/P1-lesson.mp4')
        self.assertEqual(resolve_source(self.root, family='BV1Hs411E7aP', lesson='p01'), bv)
        self.assertEqual(resolve_source(self.root, family='NL_tutorial', lesson=1), nl)
        with self.assertRaises(ValueError):
            resolve_source(self.root, family='BV1Hs411E7aP', recorded_path='video/P1-lesson.mp4')

    def test_legacy_fallback_and_explicit_source_root(self):
        bv = self.touch('video/BV1Hs411E7aP_p02.mp4')
        nl = self.touch('video/P2-lesson.mp4')
        self.assertEqual(resolve_source(self.root, family='BV1Hs411E7aP', lesson=2), bv)
        self.assertEqual(resolve_source(self.root, family='NL_tutorial', recorded_path='F:/old/video/P2-lesson.mp4'), nl)
        override = self.touch('external/NL_tutorial/P2-other.mp4')
        self.assertEqual(resolve_source(self.root, family='NL_tutorial', lesson=2, source_root=self.root/'external'), override)

    def test_ambiguous_nl_and_tool_preference(self):
        self.touch('video/raw/NL_tutorial/P8-first.mp4')
        self.touch('video/raw/NL_tutorial/P8-second.mp4')
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            resolve_source(self.root, family='NL_tutorial', lesson=8)
        new = self.touch('tools/portable/losslesscut/resources/ffmpeg.exe')
        self.touch('工具/losslesscut/resources/ffmpeg.exe')
        self.assertEqual(find_ffmpeg(self.root), new)

    def test_all_clipping_help_and_manifest_help_have_no_import_side_effects(self):
        scripts = [p for p in (ROOT/'tools/clipping').glob('*.py') if p.name != 'media_paths.py']
        scripts.append(ROOT/'scripts/build_fullframe_manifest_20261024.py')
        for script in scripts:
            with self.subTest(script=script.name):
                result = subprocess.run([sys.executable, '-X', 'utf8', str(script), '--help'],
                    capture_output=True, text=True, encoding='utf-8', timeout=15, cwd=self.root)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('usage:', result.stdout)


if __name__ == '__main__':
    unittest.main()
