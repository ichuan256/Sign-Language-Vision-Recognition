"""Domain layout and safety checks; never scan real media or launch ffprobe."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').is_file())
SCRIPT = ROOT/'vision/scripts/dataset/inventory_video_materials.py'
spec = importlib.util.spec_from_file_location('material_inventory', SCRIPT)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class MaterialInventoryTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'project/_tmp').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='inventory_layout_test_', dir=ROOT/'project/_tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def pointer_fixture(self):
        manifest = self.root/'vision/data/manifests/arbitrary_active_selection.csv'
        manifest.parent.mkdir(parents=True)
        manifest.write_text('类别,输出路径,样本编号,part\n', encoding='utf-8-sig')
        pointer = manifest.parent/'current_available_fullframe.json'
        pointer.write_text(json.dumps({'manifest': manifest.relative_to(self.root).as_posix(),
            'sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(), 'rows': 0}), encoding='utf-8')
        return manifest, pointer

    def test_directory_groups_keep_domain_source_family_contributor_and_batch(self):
        cases = {
            'vision/video/done/new_person/new_batch/你好/sample.mp4': 'vision/video/done/new_person/new_batch',
            'vision/video/done/你好/sample.mp4': 'vision/video/done/你好',
            'vision/video/raw/BV1Hs411E7aP/source.mp4': 'vision/video/raw/BV1Hs411E7aP',
            'vision/video/raw/NL_tutorial/P1-lesson.mp4': 'vision/video/raw/NL_tutorial',
            'vision/video/inbox/pending/sample.mp4': 'vision/video/inbox/pending',
            'vision/video/archive/history/sample.mp4': 'vision/video/archive/history',
            'vision/data/legacy/material/你好/sample.mp4': 'vision/data/legacy/material',
            'ASR/.sd_cache/hello.mp4': 'ASR/.sd_cache',
            'video/raw/BV1Hs411E7aP/source.mp4': 'video/raw/BV1Hs411E7aP',
        }
        for relative, expected in cases.items():
            with self.subTest(relative=relative):
                self.assertEqual(inventory.directory_group(relative), expected)

    def test_selected_hashes_exclude_unselected_historical_audit_records(self):
        selected = 'vision/video/done/person/batch/你好/one.mp4'
        historical = 'vision/video/done/person/batch/再见/two.mp4'
        records = {selected: {'sha256': 'A'*64}, historical: {'sha256': 'B'*64}}
        self.assertEqual(inventory.selected_hashes([{'输出路径': selected}], records), {'a'*64})
        self.assertEqual(inventory.selected_hashes([{'输出路径': 'missing.mp4'}], records), set())

    def test_source_hints_and_protected_assets_remain_distinct(self):
        bv = inventory.material_roles('vision/video/raw/BV1Hs411E7aP/BV1Hs411E7aP_p01.mp4')
        nl = inventory.material_roles('vision/video/raw/NL_tutorial/P1-lesson.mp4')
        self.assertEqual(bv['source_family'], 'BV1Hs411E7aP')
        self.assertEqual(nl['source_family'], 'NL_tutorial')
        self.assertEqual(bv['protected_role'], 'original_source_media')
        self.assertEqual(inventory.material_roles('ASR/.sd_cache/你好.mp4')['protected_role'], 'active_asr_phrase_library')
        self.assertEqual(inventory.material_roles('vision/data/legacy/material/你好/01_你好_示范01.mp4')['protected_role'], 'retained_legacy_test_fixture')
        self.assertEqual(inventory.material_roles('vision/video/inbox/pending/a.mp4')['protected_role'], 'pending_review_material')
        self.assertTrue(inventory.material_roles('vision/video/done/你好/a.mp4')['shallow_done_layout'])
        self.assertFalse(inventory.material_roles('vision/video/done/person/batch/你好/a.mp4')['shallow_done_layout'])
        self.assertEqual(inventory.material_roles('vision/video/archive/unknown/a.mp4')['protected_role'], '')

    def test_defaults_resolve_active_pointer_and_real_repository_root(self):
        args = inventory.build_parser().parse_args([])
        self.assertEqual(args.root, ROOT)
        self.assertIsNone(args.manifest)
        manifest, pointer = self.pointer_fixture()
        with patch.object(inventory, 'scan', side_effect=AssertionError('must not scan')), \
             patch.object(inventory, 'probe', side_effect=AssertionError('must not probe')):
            paths = inventory.inventory_paths(self.root, stamp='fixture_stamp')
        self.assertEqual(paths['manifest'], manifest)
        self.assertEqual(paths['pointer_path'], pointer)
        self.assertEqual(paths['pointer']['rows'], 0)
        self.assertEqual(paths['audit'], self.root/'vision/analysis/dataset/label_source_audit_20261025.json')
        self.assertEqual(paths['output'], self.root/'vision/analysis/materials/fixture_stamp')
        self.assertFalse(paths['output'].exists())

    def test_explicit_inputs_do_not_require_pointer_or_636_row_hash_binding(self):
        paths = inventory.inventory_paths(self.root, manifest='custom/available.csv',
            audit='custom/historical_636_audit.json', output='project/_tmp/new_inventory')
        self.assertEqual(paths['manifest'], self.root/'custom/available.csv')
        self.assertEqual(paths['audit'], self.root/'custom/historical_636_audit.json')
        self.assertIsNone(paths['pointer'])
        self.assertFalse(paths['output'].exists())
        with self.assertRaises(ValueError):
            inventory.inventory_paths(self.root, manifest='../outside.csv')
        with self.assertRaises(ValueError):
            inventory.inventory_paths(self.root, manifest='custom.csv', output='../outside')

    def test_pointer_sha_mismatch_fails_before_inventory(self):
        manifest, _ = self.pointer_fixture()
        manifest.write_bytes(manifest.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'pointer'):
            inventory.inventory_paths(self.root)
        self.assertFalse((self.root/'vision/analysis').exists())

    def test_existing_output_is_rejected_before_scan_or_probe(self):
        self.pointer_fixture()
        output = self.root/'existing'
        output.mkdir()
        marker = output/'keep.txt'
        marker.write_text('preserve')
        with patch.object(sys, 'argv', [str(SCRIPT), '--root', str(self.root), '--output', str(output)]), \
             patch.object(inventory, 'scan', side_effect=AssertionError('must not scan')), \
             patch.object(inventory, 'probe', side_effect=AssertionError('must not probe')):
            with self.assertRaises(SystemExit) as stopped:
                inventory.main()
        self.assertEqual(stopped.exception.code, 2)
        self.assertEqual(marker.read_text(), 'preserve')

    def test_historical_powershell_scripts_stop_before_original_body_with_or_without_apply(self):
        for name in ('organize_workspace_materials_20261025.ps1', 'recycle_unused_materials_20261025.ps1'):
            script = ROOT/'vision/scripts/dataset'/name
            source = script.read_text(encoding='utf-8-sig')
            self.assertLess(source.index("throw 'FROZEN HISTORICAL RECORD"), source.index("$ErrorActionPreference"))
            for flags in ([], ['-Apply']):
                with self.subTest(script=name, flags=flags):
                    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                        '-File', str(script), *flags], cwd=self.root, capture_output=True, text=True, timeout=15)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('FROZEN HISTORICAL RECORD', result.stdout + result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
