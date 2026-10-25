"""CLI safety works without importing optional computer-vision dependencies."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
SCRIPT = ROOT / 'vision/scripts/build_templates.py'


class TemplateBuildCliTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'project/_tmp').mkdir(parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix='template_cli_test_', dir=ROOT/'project/_tmp')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', str(SCRIPT), *map(str, args)],
            cwd=self.root, capture_output=True, text=True, encoding='utf-8', timeout=15)

    def test_default_repo_root_and_import_path_use_separate_domains(self):
        spec = importlib.util.spec_from_file_location('template_cli_layout', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        args = module.build_parser().parse_args(['--manifest', 'fixture.csv', '--output', 'fixture.npz'])
        self.assertEqual(args.repo_root, ROOT)
        self.assertEqual(module.ROOT, ROOT)
        self.assertEqual(Path(sys.path[0]), ROOT/'vision/src')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_each_dataset_and_output_argument_is_explicitly_required(self):
        for arguments, missing in [((), '--manifest'), (('--manifest', 'input.csv'), '--output'),
                                   (('--output', 'new.npz'), '--manifest')]:
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn(missing, result.stderr)
                self.assertNotIn('ModuleNotFoundError', result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_help_is_available_and_creates_no_artifacts(self):
        result = self.run_cli('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--manifest', result.stdout)
        self.assertIn('--output', result.stdout)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_existing_model_is_protected_before_optional_imports_or_input_reads(self):
        archive = self.root / 'old_model.npz'
        archive.write_bytes(b'preserve-old-model')
        result = self.run_cli('--manifest', self.root/'nonexistent.csv', '--output', archive)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('template archive exists', result.stderr)
        self.assertNotIn('ModuleNotFoundError', result.stderr)
        self.assertNotIn('manifest not found', result.stderr)
        self.assertEqual(archive.read_bytes(), b'preserve-old-model')
        self.assertEqual(list(self.root.iterdir()), [archive])


if __name__ == '__main__':
    unittest.main()
