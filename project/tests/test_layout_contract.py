"""Layout gates must reject invalid pointers rather than hide missing data."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from project.scripts.check_layout import bound_csv, confined, require

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

if __name__=="__main__":unittest.main()
