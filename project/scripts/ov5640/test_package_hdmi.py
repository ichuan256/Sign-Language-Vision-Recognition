"""Check that HDMI release metadata requires the corresponding hardware."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from package_snapshot import hdmi_design_for_hwh

ROOT = Path(__file__).resolve().parents[3]
HDMI_HWH = ROOT / 'project/board/w6/kws_hdmi.hwh'
CAMERA_HWH = ROOT / 'project/board/ov5640_snapshot/release_remove_pl_bad_frame_20261028/ov5640_snapshot.hwh'


class HdmiPackageTests(unittest.TestCase):
    def test_real_hdmi_metadata_and_camera_only_rejection(self):
        design = hdmi_design_for_hwh(HDMI_HWH)
        self.assertTrue(design['hdmi_output'])
        self.assertEqual(design['hdmi_hierarchy'], 'video/hdmi_out')
        self.assertEqual(design['hdmi_read_hp'], 'HP2')
        with self.assertRaisesRegex(ValueError, 'Missing HDMI'):
            hdmi_design_for_hwh(CAMERA_HWH)

    def test_missing_pipeline_stage_or_wrong_vdma_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'project/_tmp') as directory:
            path = Path(directory) / 'mutated.hwh'
            tree = ET.parse(HDMI_HWH)
            tree.find(".//MODULE[@FULLNAME='/video/hdmi_out/pixel_unpack']").set('MODTYPE', 'wrong')
            tree.write(path)
            with self.assertRaisesRegex(ValueError, 'pixel_unpack'):
                hdmi_design_for_hwh(path)
            for fullname, param, value in (
                ('/video/axi_vdma', 'C_INCLUDE_MM2S', '0'),
                ('/video/axi_vdma', 'C_INCLUDE_S2MM', '1'),
                ('/video/axi_vdma', 'C_M_AXIS_MM2S_TUSER_BITS', '0'),
                ('/ps7', 'C_USE_S_AXI_HP2', '0'),
            ):
                with self.subTest(param=param):
                    tree = ET.parse(HDMI_HWH)
                    tree.find(f".//MODULE[@FULLNAME='{fullname}']/PARAMETERS/PARAMETER[@NAME='{param}']").set('VALUE', value)
                    tree.write(path)
                    with self.assertRaisesRegex(ValueError, 'Incompatible'):
                        hdmi_design_for_hwh(path)


if __name__ == '__main__':
    unittest.main()
