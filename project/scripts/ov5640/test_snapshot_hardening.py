import copy
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import snapshot_provenance as provenance
import snapshot_io_timing as timing
import package_snapshot


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'project/fpga/rtl/ov5640_snapshot/top.v'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('module top; endmodule')
        self.project = self.root / 'project/_tmp/test'
        self.build = self.root / 'build'
        self.build.mkdir()
        provenance.begin(self.root, self.project)
        self.bd = self.project / 'system.bd'
        self.bd.write_text('configured BD')
        provenance.bind_project(self.root, self.project, [self.source, self.bd])
        for name in provenance.ARTIFACTS:
            (self.build / name).write_text('artifact ' + name)
        (self.build / 'build_result.tcl').write_text(
            'set snapshot_build_complete 1\nset snapshot_sccb_structure_pass 1\n')

    def test_valid_seal_verify(self):
        provenance.seal(self.root, self.project, self.build)
        result = provenance.verify(self.root, self.build)
        self.assertEqual(result['sources'], provenance.inputs(self.root))

    def test_source_drift_before_seal(self):
        self.source.write_text('changed RTL')
        with self.assertRaises(ValueError):
            provenance.seal(self.root, self.project, self.build)
        self.assertFalse((self.build / 'build_provenance.json').exists())

    def test_source_drift_after_seal(self):
        provenance.seal(self.root, self.project, self.build)
        self.source.write_text('changed after compile')
        with self.assertRaises(ValueError): provenance.verify(self.root, self.build)

    def test_new_input_rejected(self):
        self.source.with_name('added.v').write_text('new module')
        with self.assertRaises(ValueError): provenance.check_inputs(self.root, self.project)

    def test_bd_config_drift(self):
        self.bd.write_text('different DMA config')
        with self.assertRaises(ValueError): provenance.check_inputs(self.root, self.project)

    def test_artifact_replacement(self):
        provenance.seal(self.root, self.project, self.build)
        (self.build / 'ov5640_snapshot.bit').write_text('old bit')
        with self.assertRaises(ValueError): provenance.verify(self.root, self.build)

    def test_legacy_build_rejected(self):
        with self.assertRaises(FileNotFoundError): provenance.verify(self.root, self.build)

    def test_missing_gate_rejected(self):
        (self.build / 'build_result.tcl').write_text('set snapshot_build_complete 1')
        with self.assertRaises(ValueError): provenance.seal(self.root, self.project, self.build)

    def test_escape_rejected(self):
        with self.assertRaises(ValueError): provenance.inside(self.root, '../outside')
        with self.assertRaises(ValueError): provenance.inside(self.root, self.source)

    def test_input_snapshot_cannot_be_overwritten(self):
        with self.assertRaises(FileExistsError): provenance.begin(self.root, self.project)

    def test_packaging_requires_explicit_unverified_candidate(self):
        (self.build / 'external_io_status.json').write_text(json.dumps(dict(constrained=False)))
        provenance.seal(self.root, self.project, self.build)
        dest = self.root / 'release'
        argv = ['package_snapshot.py', '--build', str(self.build), '--output', str(dest)]
        with patch.object(package_snapshot, 'ROOT', self.root), patch('sys.argv', argv):
            with self.assertRaises(RuntimeError): package_snapshot.main()
        self.assertFalse(dest.exists())
        with patch.object(package_snapshot, 'ROOT', self.root), patch('sys.argv', argv + ['--allow-unverified-io']):
            package_snapshot.main()
        result = json.loads((dest / 'release_manifest.json').read_text())
        self.assertEqual(result['sources'], provenance.inputs(self.root))
        self.assertFalse(result['validation']['external_io_timing'])
        self.assertFalse(result['validation']['external_io_constraints'])
        self.assertEqual(result['build_provenance']['sha256'], provenance.digest(dest / 'build_provenance.json'))


class TimingTests(unittest.TestCase):
    def profile(self):
        # Synthetic parser fixture only: never a physical-board timing claim.
        return dict(schema_version=1, launch_edge='falling', pclk_period_ns=12,
                    evidence='synthetic unit-test fixture', clock_uncertainty_ns=0.1,
                    input_delays_ns={p: dict(min=0.1, max=1, clock='ov1_pclk' if p in timing.DVP else 'sys_clk') for p in timing.INPUTS},
                    output_delays_ns={p: dict(min=0, max=1, clock='sys_clk') for p in timing.OUTPUTS})

    def test_falling_edge_full_coverage(self):
        text = timing.render(self.profile())
        self.assertEqual(text.count('-clock_fall'), 20)
        self.assertEqual(text.count('set_input_delay'), 22)
        self.assertEqual(text.count('set_output_delay'), 8)

    def test_missing_physical_data_no_fake_delay(self):
        p = self.profile(); p['input_delays_ns'] = None
        self.assertFalse(timing.validate(p)['constrained'])
        self.assertNotIn('set_input_delay', timing.render(p))

    def test_missing_port_rejected(self):
        p = self.profile(); del p['input_delays_ns']['ov1_href']
        with self.assertRaises(ValueError): timing.validate(p)

    def test_bad_values_and_clock_rejected(self):
        for patch in ({'min':2}, {'max':float('nan')}, {'clock':'unknown'}):
            p = self.profile(); p['input_delays_ns']['ov1_href'].update(patch)
            with self.assertRaises(ValueError): timing.validate(p)

    def test_edge_mismatch_rejected(self):
        p = self.profile(); p['launch_edge']='rising'
        with self.assertRaises(ValueError): timing.validate(p)

if __name__ == '__main__': unittest.main()
