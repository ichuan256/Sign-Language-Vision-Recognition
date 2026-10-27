"""Build the cold-start register ROM from a pinned factual register snapshot.

The JSON snapshot contains register numbers, values and delays, not Linux
driver functions. Normal generation and auditing are offline. --refresh-reference
explicitly downloads the pinned upstream file and verifies its SHA-256 before
extracting those facts. This is a candidate sensor configuration, not board proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
ANALYSIS = ROOT / "project/analysis/ov5640_stereo_20261026"
SNAPSHOT = ANALYSIS / "startup_reference_values.json"
CONTRACT = ANALYSIS / "startup_contract.json"
ROM = ROOT / "project/fpga/rtl/ov5640_stereo/ov5640_startup_table.v"
URL = "https://raw.githubusercontent.com/torvalds/linux/v6.12/drivers/media/i2c/ov5640.c"
REFERENCE_SHA256 = "a991af015db5ce528c3d29d27c21a9071d5f9db9bf0ad861d8280a76268fb605"


def refresh_reference() -> None:
    code = urllib.request.urlopen(URL, timeout=30).read()
    digest = hashlib.sha256(code).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"Pinned reference hash mismatch: {digest}")
    text = code.decode("utf-8")
    tables = {}
    for name, count in (("ov5640_init_setting", 219),
                        ("ov5640_setting_720P_1280_720", 28)):
        match = re.search(r"static const struct reg_value " + name
                          + r"\[\] = \{(.*?)\n\};", text, re.S)
        if match is None:
            raise ValueError(f"Missing reference table {name}")
        rows = re.findall(r"\{\s*(0x[\da-f]+)\s*,\s*(0x[\da-f]+)\s*,"
                          r"\s*([^,]+),\s*([^}]+)\}", match[1], re.I)
        facts = []
        for address, value, mask, delay in rows:
            facts.append({"address": f"{int(address, 16):04x}",
                          "value": f"{int(value, 16):02x}",
                          "mask": f"{int(mask.strip(), 0) or 255:02x}",
                          "post_delay_ms": int(delay.strip(), 0)})
        if len(facts) != count:
            raise ValueError(f"Reference {name}: {len(facts)} != {count}")
        tables[name] = facts
    SNAPSHOT.write_text(json.dumps({"source_url": URL, "tag": "v6.12",
        "source_sha256": digest, "source_bytes": len(code),
        "scope": "Extracted register facts; no driver function implementation",
        "tables": tables}, indent=2) + "\n", encoding="utf-8")


def make_contract() -> dict:
    reference = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if reference["source_sha256"] != REFERENCE_SHA256:
        raise ValueError("Unexpected reference snapshot")
    rows = []

    def add(stage, address, value, mask=255, delay=0, basis="design contract"):
        rows.append({"stage": stage, "address": f"{address:04x}",
                     "value": f"{value:02x}", "mask": f"{mask:02x}",
                     "post_delay_ms": delay, "basis": basis})

    # SCCB stays available in software standby. There is no VGA video stream
    # whose exposure must be migrated; this path always begins with hard reset.
    add("standby", 0x3103, 0x11, basis="reference initial clock source")
    add("standby", 0x3008, 0x82, delay=20,
        basis="software reset; conservative 20ms reset settling")
    add("standby", 0x3008, 0x42, basis="DVP register programming in standby")
    add("standby", 0x3503, 0x03, mask=0x03,
        basis="manual AEC/AGC during cold mode programming")

    for row in reference["tables"]["ov5640_init_setting"]:
        if row["address"] == "3008" and row["value"] == "02":
            continue  # stream-on is guarded by the controller's readback phase.
        add("analog_isp", int(row["address"], 16), int(row["value"], 16),
            int(row["mask"], 16), row["post_delay_ms"], "reference global init")

    known = json.loads((ANALYSIS / "known_config_contract.json").read_text(encoding="utf-8"))
    clock_addresses = {"3034", "3035", "3036", "3037", "3108"}
    for row in known["items"]:
        if row["address"] in clock_addresses:
            add("pll", int(row["address"], 16), int(row["value"], 16),
                int(row["mask"], 16), row["post_delay_ms"], "existing calculated PLL contract")

    # Preserve every reference mode-table write, including later overrides.
    for row in reference["tables"]["ov5640_setting_720P_1280_720"]:
        add("720p_mode", int(row["address"], 16), int(row["value"], 16),
            int(row["mask"], 16), row["post_delay_ms"], "reference 720p mode")

    left, top, width, height = 0, 250, 2624, 1456
    for address, value in ((0x3800, left), (0x3802, top),
                           (0x3804, left + width - 1),
                           (0x3806, top + height - 1),
                           (0x3810, 16), (0x3812, 4)):
        add("window", address, value >> 8, basis="reference DVP analog_crop/crop geometry")
        add("window", address + 1, value & 255, basis="reference DVP analog_crop/crop geometry")
    add("format_dvp", 0x3820, 1, mask=0x01, basis="SUBSAMPLING: enable binning")
    add("format_dvp", 0x3821, 1, mask=0x21,
        basis="SUBSAMPLING and non-JPEG: enable binning; disable JPEG; preserve orientation")
    add("format_dvp", 0x3002, 0x1c, mask=0x1c, basis="non-JPEG reset of JPEG/SFIFO/JFIFO")
    add("format_dvp", 0x3006, 0, mask=0x28, basis="non-JPEG disable JPEG clocks")
    add("format_dvp", 0x4730, 0, basis="separate VSYNC/HREF, not BT656")
    add("format_dvp", 0x300e, 0x18, basis="disable MIPI PHY and select DVP")
    add("format_dvp", 0x3017, 0x7f, basis="enable VSYNC/HREF/PCLK and D9..D6")
    add("format_dvp", 0x3018, 0xfc, basis="enable D5..D0; module exports D9..D2")

    # Fixed frame budget and a deterministic cold-start seed. AEC/AGC will
    # adapt after stream-on; these are not scene-optimal exposure guarantees.
    for address, value in ((0x3a02, 736), (0x3a14, 736), (0x3a18, 0x00f8)):
        add("exposure_seed", address, value >> 8, basis="VTS-4 limit / reference gain ceiling")
        add("exposure_seed", address + 1, value & 255, basis="VTS-4 limit / reference gain ceiling")
    for address, value in ((0x3500, 0x00), (0x3501, 0x0d), (0x3502, 0xd0),
                           (0x350a, 0x00), (0x350b, 0x10)):
        add("exposure_seed", address, value, basis="221-line (~10ms) / 1x cold-start seed")

    for row in known["items"]:
        if row["address"] in clock_addresses:
            continue
        value, mask = int(row["value"], 16), int(row["mask"], 16)
        if row["address"] == "4740":
            value, mask = 0x22, 0x2f
        add("target_controls", int(row["address"], 16), value, mask,
            row["post_delay_ms"], "known contract; 4740 candidate also clears PCLK gates")
    for index, row in enumerate(rows):
        row["index"] = index
        row["last"] = index == len(rows) - 1
    return {"schema_version": 1, "reference": {k: reference[k] for k in
            ("source_url", "tag", "source_sha256")},
            "scope": "cold hard-reset startup candidate; no hot mode/exposure migration",
            "mode": {"xclk_hz": 24000000, "width": 1280, "height": 720,
                     "fps_target": 30, "hts": 1892, "vts": 740,
                     "analog_crop": [left, top, width, height],
                     "output_offset": [16, 4], "format": "RGB565_LE_8bit_DVP",
                     "pclk_hz_candidate": 84000000, "sysclk_hz_candidate": 42000000,
                     "polarity_register_candidate": "22", "polarity_mask": "2f",
                     "polarity_status": "Linux-derived candidate; physical waveform unverified",
                     "exposure_seed_lines": 221, "exposure_limit_lines": 736,
                     "gain_seed_x16": 16, "gain_ceiling_x16": 248},
            "stream_on": {"address": "3008", "value": "02",
                          "owner": "startup controller, only after ID and readback success"},
            "table_count": len(rows), "items": rows}


def render_rom(contract: dict) -> str:
    lines = ["`timescale 1ns/1ps", "", "// Generated by project/scripts/ov5640/generate_startup_table.py.",
        "// Pinned register facts and arithmetic: startup_contract.json.",
        "// Cold-start candidate; board clocks, polarity and image quality remain unverified.",
        "// Deliberately excludes stream-on: the controller must verify both cameras first.",
        "module ov5640_startup_table #(",
        "    parameter [7:0] DVP_POLARITY_VALUE = 8'h22", ") (",
        "    input wire [9:0] index,", "    output reg valid,",
        "    output reg [15:0] reg_addr,", "    output reg [7:0] reg_value, write_mask,",
        "    output reg [15:0] post_delay_ms,", "    output reg last", ");",
        f"    localparam integer ENTRY_COUNT = {contract['table_count']};",
        "    always @* begin", "        valid = 1'b1;", "        reg_addr = 16'h0000;",
        "        reg_value = 8'h00;", "        write_mask = 8'hff;",
        "        post_delay_ms = 16'd0;", "        last = 1'b0;", "        case (index)"]
    stage = None
    for row in contract["items"]:
        if stage != row["stage"]:
            stage = row["stage"]
            lines.append(f"            // {stage}")
        value = "(DVP_POLARITY_VALUE & 8'h23)" if (stage == "target_controls" and
                  row["address"] == "4740") else f"8'h{row['value']}"
        fields = [f"reg_addr=16'h{row['address']}", f"reg_value={value}"]
        if row["mask"] != "ff": fields.append(f"write_mask=8'h{row['mask']}")
        if row["post_delay_ms"]: fields.append(f"post_delay_ms=16'd{row['post_delay_ms']}")
        if row["last"]: fields.append("last=1'b1")
        lines.append(f"            10'd{row['index']}: begin " + "; ".join(fields) + "; end")
    lines += ["            default: begin valid=1'b0; write_mask=8'h00; end",
              "        endcase", "    end", "endmodule", ""]
    return "\n".join(lines)


def audit(contract: dict) -> dict:
    rows = contract["items"]
    if len(rows) >= 1024: raise ValueError("Table index overflow")
    values = {0x300a: 0x56, 0x300b: 0x40}
    for row in rows:
        address, value, mask = (int(row[k], 16) for k in ("address", "value", "mask"))
        if address in (0x300a, 0x300b): raise ValueError("Read-only chip ID in write table")
        if address == 0x3008 and value == 2: raise ValueError("Unguarded stream-on in ROM")
        values[address] = (values.get(address, 0) & ~mask) | (value & mask)
    def word(address): return (values[address] << 8) | values[address + 1]
    expected_words = {0x3800: 0, 0x3802: 250, 0x3804: 2623, 0x3806: 1705,
        0x3808: 1280, 0x380a: 720, 0x380c: 1892, 0x380e: 740,
        0x3810: 16, 0x3812: 4, 0x3a02: 736, 0x3a14: 736,
        0x3a08: 221, 0x3a0a: 184, 0x3a18: 248, 0x350a: 16}
    for address, expected in expected_words.items():
        if word(address) != expected: raise ValueError(f"Bad final word {address:04x}")
    expected_bytes = {0x3034: 0x18, 0x3035: 0x20, 0x3036: 84, 0x3037: 0x13,
        0x3108: 1, 0x3814: 0x31, 0x3815: 0x31, 0x4300: 0x6f, 0x501f: 1,
        0x3a0d: 4, 0x3a0e: 3, 0x3008: 0x42, 0x300e: 0x18,
        0x3017: 0x7f, 0x3018: 0xfc, 0x4730: 0}
    for address, expected in expected_bytes.items():
        if values[address] != expected: raise ValueError(f"Bad final byte {address:04x}")
    for address, mask, expected in ((0x3820, 1, 1), (0x3821, 0x21, 1),
            (0x3503, 3, 0), (0x3406, 1, 0), (0x4740, 0x2f, 0x22),
            (0x3a00, 0x24, 0x20), (0x3002, 0x1c, 0x1c), (0x3006, 0x28, 0)):
        if values[address] & mask != expected: raise ValueError(f"Bad final bits {address:04x}")
    exposure = ((values[0x3500] << 16) | word(0x3501)) >> 4
    if exposure != 221: raise ValueError("Bad cold exposure seed")
    # Independent mode arithmetic, not values read back from generated HDL.
    prediv = values[0x3037] & 15
    sysdiv = (values[0x3035] >> 4) or 16
    rootdiv = ((values[0x3037] >> 4) & 1) + 1
    bitdiv2x = (values[0x3034] & 15) // 2
    vco = contract["mode"]["xclk_hz"] // prediv * values[0x3036]
    if not 500000000 <= vco <= 1000000000: raise ValueError("PLL VCO range")
    baseclk = vco // sysdiv // rootdiv * 2 // bitdiv2x
    pclk = baseclk // (1 << ((values[0x3108] >> 4) & 3))
    sysclk = baseclk // (1 << (values[0x3108] & 3))
    if values[0x460c] & 2: raise ValueError("Unexpected manual PCLK divider")
    mode = contract["mode"]
    if (mode["width"],mode["height"],mode["hts"],mode["vts"],mode["pclk_hz_candidate"],mode["sysclk_hz_candidate"]) != (word(0x3808),word(0x380a),word(0x380c),word(0x380e),pclk,sysclk):
        raise ValueError("Mode metadata differs from register-derived timing")
    if not 29.99 <= pclk / (1892 * 740 * 2) <= 30.01: raise ValueError("Frame timing mismatch")
    if pclk > 96000000: raise ValueError("DVP PCLK exceeds 96 MHz specification")
    if (sysclk // 1892 // 100, sysclk // 1892 // 120) != (221, 184):
        raise ValueError("Banding calculation mismatch")
    return {"verdict": "PASS", "table_count": len(rows),
            "delays_ms": sum(r["post_delay_ms"] for r in rows),
            "pclk_hz_candidate": pclk, "sysclk_hz_candidate": sysclk,
            "pclk_limit_hz": 96000000, "pclk_spec_margin_hz": 96000000-pclk,
            "arithmetic_fps": pclk / (1892 * 740 * 2),
            "checked": ["reference tables with ordered overrides", "crop/output/HTS/VTS",
                        "register-derived PLL/banding/exposure arithmetic", "PCLK <= 96 MHz", "RGB565 and non-JPEG/binning bits",
                        "DVP pad/control selection", "no ID writes or early stream-on"],
            "not_verified": ["physical polarity, clocks or FPS", "lens/ISP image quality"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-reference", action="store_true")
    parser.add_argument("--check", action="store_true", help="Verify outputs without rewriting")
    args = parser.parse_args()
    if args.refresh_reference: refresh_reference()
    contract = make_contract()
    report = audit(contract)
    outputs = {CONTRACT: json.dumps(contract, indent=2) + "\n", ROM: render_rom(contract)}
    if args.check:
        for path, content in outputs.items():
            if path.read_text(encoding="utf-8") != content:
                raise ValueError(f"Generated output drift: {path}")
    else:
        for path, content in outputs.items(): path.write_text(content, encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
