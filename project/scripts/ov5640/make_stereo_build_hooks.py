"""Derive strict dual-IP build gates from the existing single-IP gates."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
scripts=ROOT/'project/fpga/scripts'
gate=(scripts/'ov5640_snapshot_sccb_gate.tcl').read_text()
gate=gate.replace('foreach port {ov1_scl ov1_sda} pad {W9 Y8}',
    'foreach port {ov1_scl ov1_sda ov2_scl ov2_sda} pad {W9 Y8 V10 V8}')
gate=gate.replace('$port eq "ov1_sda"','$port in {ov1_sda ov2_sda}')
(scripts/'ov5640_snapshot_stereo_sccb_gate.tcl').write_text('# Derived dual-channel gate; source: ov5640_snapshot_sccb_gate.tcl\n'+gate)
emit=(scripts/'ov5640_snapshot_emit.tcl').read_text()
emit=emit.replace('ov5640_snapshot_sccb_gate.tcl','ov5640_snapshot_stereo_sccb_gate.tcl')
emit=emit.replace('system_i/camera/','system_i/(camera|camera_right)/')
(scripts/'ov5640_snapshot_stereo_emit.tcl').write_text('# Both cameras checked. External I/O remains unverified.\n'+emit)
build=(scripts/'ov5640_snapshot_build.tcl').read_text()
build=build.replace('ov5640_snapshot_emit.tcl','ov5640_snapshot_stereo_emit.tcl')
(scripts/'ov5640_snapshot_stereo_build.tcl').write_text(build)
