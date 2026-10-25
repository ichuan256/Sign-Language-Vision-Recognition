"""Layout gates must reject invalid pointers rather than hide missing data."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from project.scripts.check_layout import bound_csv, confined, require, check_root_dirs

class LayoutContractTests(unittest.TestCase):
    def test_outside_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "outside"):
                confined(Path(folder), "../outside.csv")
    def fixture(self, root):
        p=root/"current.csv"
        p.write_bytes(b"label,path\r\na,vision/video/a.mp4\r\n")
        info={"manifest":"current.csv","sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"rows":1}
        (root/"pointer.json").write_text(json.dumps(info),encoding="utf-8")
        return p,info
    def test_valid_sha_bound_csv_is_loaded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.fixture(root)
            _,data=bound_csv(root,"pointer.json","manifest")
            self.assertEqual(data,[{"label":"a","path":"vision/video/a.mp4"}])
    def test_media_manifest_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p,_=self.fixture(root);p.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                bound_csv(root,"pointer.json","manifest")
    def test_row_count_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);_,info=self.fixture(root);info["rows"]=2
            (root/"pointer.json").write_text(json.dumps(info),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"row count"):
                bound_csv(root,"pointer.json","manifest")
    def test_checks_remain_active_without_assert_statements(self):
        with self.assertRaises(ValueError): require(False,"invalid contract")

    def roots(self, root):
        for name in ("ASR", "docs", "project", "vision"):
            (root/name).mkdir()
    def test_exact_four_roots_are_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.roots(root)
            self.assertEqual(check_root_dirs(root),[])
    def test_unrecorded_extra_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.roots(root);(root/"unexpected").mkdir()
            with self.assertRaisesRegex(ValueError,"Unexpected root"):
                check_root_dirs(root)
    def test_retained_tool_requires_exact_files_and_sha(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.roots(root);(root/"tools").mkdir()
            asset=root/"tools/tool.bin";asset.write_bytes(b"original")
            p=root/"vision/analysis/materials/20261025_merge/local_layout_residue.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"roots":{"tools":[{"path":"tools/tool.bin","bytes":8,"sha256":hashlib.sha256(asset.read_bytes()).hexdigest()}]}}),encoding="utf-8")
            self.assertEqual(check_root_dirs(root),["tools"])
            asset.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError,"SHA changed"):
                check_root_dirs(root)

if __name__=="__main__":unittest.main()
