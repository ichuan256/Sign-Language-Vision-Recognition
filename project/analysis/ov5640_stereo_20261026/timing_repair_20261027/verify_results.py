"""Check final reports, complete XSim transcripts and preserve source hashes."""
from pathlib import Path
import hashlib
import json

e = Path(__file__).resolve().parent
root = e.parents[3]
tops = ["delay_conversion", "sccb_register_access", "startup_defaults",
        "startup_controller", "stereo_startup", "startup_capture",
        "dvp_capture", "stereo_capture_pair", "720p_frame"]
def read_transcript(folder, name):
    local = folder / name
    portable = local.with_suffix(".txt")
    return (local if local.exists() else portable).read_text()

tests = {}
for suffix in tops:
    name = "tb_ov5640_" + suffix
    transcript = read_transcript(e / name, "simulate.log")
    assert "TEST_PASS:" in transcript and "Fatal:" not in transcript and "Error:" not in transcript, name
    for stage in ("compile.log", "elaborate.log"):
        text = read_transcript(e / name, stage)
        assert "ERROR:" not in text and "FATAL:" not in text, (name, stage)
    tests[name] = next(line for line in transcript.splitlines() if "TEST_PASS:" in line)
timing = (e / "timing_summary.rpt").read_text()
assert "All user specified timing constraints are met." in timing
assert "unconstrained_internal_endpoints (0)" in timing
lines = timing.splitlines()
i = next(i for i, line in enumerate(lines) if line.strip().startswith("WNS(ns)"))
metrics = lines[i + 2].split()
cdc = (e / "cdc.rpt").read_text()
assert "Critical" not in cdc and "Warning" not in cdc
assert "CDC-9" in cdc, "Missing recognized reset synchronizers"
acceptance = (e / "timing_acceptance.txt").read_text()
assert "TIMING_ACCEPTANCE_PASS" in acceptance
assert acceptance.count("RESET_CHAIN") == 2 and acceptance.count("RESET_RECOVERY") == 2
assert "PIN_AND_PAD_CHECKS_PASS" in (e / "pad_and_clock_checks.txt").read_text()
paths = list((root / "project/fpga/rtl/ov5640_stereo").glob("*.v"))
paths += list((root / "project/fpga/tb/ov5640_stereo").glob("*.v"))
paths += [root / "project/fpga/scripts/ov5640_startup_cdc.tcl", e / "pin_validation_top.v"]
result = {"tool": "Vivado/XSim 2024.1", "part": "xc7z020clg400-1",
          "scope": "125 MHz isolated pin_validation_top; PCLK 11.905 ns",
          "wns_ns": float(metrics[0]), "tns_ns": float(metrics[1]),
          "setup_failing_endpoints": int(metrics[2]), "whs_ns": float(metrics[4]),
          "ths_ns": float(metrics[5]), "tests": tests,
          "source_sha256": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
          "limitations": ["24 inputs and 12 outputs lack external I/O delays",
                          "Not W6 integration, bitstream release or board test",
                          "DRC retains SCL input-buffer and standalone PS7 warnings"]}
(e / "verification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+chr(10), encoding="utf-8")
print(json.dumps({"tests_passed": len(tests), "wns_ns": result["wns_ns"], "whs_ns": result["whs_ns"]}))
