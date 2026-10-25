# -*- coding: utf-8 -*-
"""R3.3: streaming hls4ml regression and standalone Vitis HLS synthesis."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

import r3_hls4ml_20261024 as r32


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
DEFAULT_OUTPUT = ROOT / "project/_tmp" / "r3" / "r3_hls_synth_rf576_p40"
DEFAULT_REPORT = ROOT / "project/analysis" / "r3" / "r3_hls_synth_20261025.json"
RESOURCE_LIMITS = {"LUT": 40.0, "DSP": 60.0, "BRAM_18K": 50.0}


def write_build_options(output_dir: Path, *, csim: bool, synth: bool) -> None:
    (output_dir / "build_opt.tcl").write_text(
        f"""array set opt {{
    reset      1
    csim       {int(csim)}
    synth      {int(synth)}
    cosim      0
    validation 0
    export     0
    vsynth     0
    fifo_opt   0
}}
""",
        encoding="utf-8",
    )


def run_vitis(output_dir: Path, vitis_hls: Path, log_path: Path) -> tuple[int, float]:
    started = time.time()
    command = ["cmd.exe", "/c", str(vitis_hls), "-f", "build_prj.tcl"]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        completed = subprocess.run(
            command,
            cwd=output_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
        seconds = time.time() - started
        log.write(f"\nR3_RETURN_CODE={completed.returncode}\nR3_SECONDS={seconds:.3f}\n")
    return completed.returncode, seconds


def fixed_codes(values: np.ndarray, precision: str) -> np.ndarray:
    width, integer = r32.precision_shape(precision)
    return np.rint(values * (1 << (width - integer))).astype(np.int64)


def percentage(report: dict[str, str], resource: str) -> float | None:
    used = report.get(resource)
    available = report.get("Available" + resource)
    if used is None or available in (None, "0"):
        return None
    return 100.0 * float(used) / float(available)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--conv-reuse-factor", type=int, default=576)
    parser.add_argument("--dense-reuse-factor", type=int, default=128)
    parser.add_argument("--bn-scale-precision", default="ap_fixed<40,16>")
    parser.add_argument("--bn-bias-precision", default="ap_fixed<40,16>")
    parser.add_argument("--bn-result-precision", default="ap_fixed<44,24>")
    parser.add_argument("--fifo-depth", type=int, default=2)
    parser.add_argument("--model", type=Path, default=r32.DEFAULT_CACHE / "r3_model_quant.keras")
    parser.add_argument("--tensors", type=Path, default=r32.DEFAULT_CACHE / "tensors.npz")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--vitis-hls",
        type=Path,
        default=Path(r"F:\APP\Xilinx\Vitis_HLS\2024.1\bin\vitis_hls.bat"),
    )
    parser.add_argument(
        "--gxx",
        type=Path,
        default=Path(r"F:\APP\Xilinx\Vitis_HLS\2024.1\tps\mingw\10.0.0\win64.o\nt\bin\g++.exe"),
    )
    parser.add_argument("--samples", type=int, default=0, help="0 means all holdout samples")
    parser.add_argument("--skip-csim", action="store_true")
    parser.add_argument("--skip-synth", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    report_path = args.report.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    data = np.load(args.tensors.resolve(), allow_pickle=False)
    indices = r32.test_indices(data["y"])
    if args.samples > 0:
        indices = indices[: args.samples]
    inputs = data["X"][indices].astype(np.float32) / 255.0

    model = r32.load_qmodel(args.model.resolve(), compile=False)
    keras_output = model.predict(inputs, verbose=0).astype(np.float64)
    input_npy = output_dir / "r3_input.npy"
    output_npy = output_dir / "r3_keras_output.npy"
    np.save(input_npy, inputs)
    np.save(output_npy, keras_output)

    config = r32.hls4ml.utils.config_from_keras_model(
        model,
        granularity="name",
        backend="Vitis",
        default_precision="ap_fixed<24,10>",
        default_reuse_factor=1,
    )
    config["Model"]["Strategy"] = "Resource"
    config["LayerName"]["input_1"]["Precision"]["result"] = "ap_fixed<40,2>"
    for layer_name, layer_config in config["LayerName"].items():
        if layer_name.startswith("batch_normalization"):
            layer_config["Precision"]["scale"] = args.bn_scale_precision
            layer_config["Precision"]["bias"] = args.bn_bias_precision
            layer_config["Precision"]["result"] = args.bn_result_precision
        if layer_name in {"conv1", "conv2", "conv3", "conv4"}:
            layer_config["ReuseFactor"] = args.conv_reuse_factor
        if layer_name == "qdense":
            layer_config["ReuseFactor"] = args.dense_reuse_factor

    hls_model = r32.hls4ml.converters.convert_from_keras_model(
        model,
        output_dir=str(output_dir),
        project_name="gesture_cls",
        input_data_tb=str(input_npy),
        output_data_tb=str(output_npy),
        backend="Vitis",
        hls_config=config,
        part=r32.PART,
        clock_period=10,
        io_type="io_stream",
    )
    input_vars = set(hls_model.get_input_variables())
    output_vars = set(hls_model.get_output_variables())
    for variable in hls_model.output_vars.values():
        if variable not in input_vars and variable not in output_vars and variable.pragma:
            variable.pragma = (variable.pragma[0], args.fifo_depth)
    hls_model.write()
    output_precision = str(hls_model.get_output_variables()[0].type.precision)

    result: dict[str, object] = {
        "milestone": "R3.3",
        "backend": "Vitis",
        "hls4ml_version": r32.hls4ml.__version__,
        "part": r32.PART,
        "clock_period_ns": 10.0,
        "io_type": "io_stream",
        "strategy": "Resource",
        "reuse_factors": {
            "conv1": args.conv_reuse_factor,
            "conv2": args.conv_reuse_factor,
            "conv3": args.conv_reuse_factor,
            "conv4": args.conv_reuse_factor,
            "qdense": args.dense_reuse_factor,
        },
        "samples": int(len(inputs)),
        "outputs": int(keras_output.size),
        "output_precision": output_precision,
        "batchnorm_precision": {
            "scale": args.bn_scale_precision,
            "bias": args.bn_bias_precision,
            "result": args.bn_result_precision,
        },
        "internal_fifo_depth": args.fifo_depth,
        "generated_project": str(output_dir.relative_to(ROOT)),
    }

    if not args.skip_csim:
        host_dll = r32.compile_host_reference(args.gxx.resolve(), output_dir)
        host_output = r32.run_host_reference(host_dll, args.gxx.resolve(), inputs)
        np.savetxt(output_dir / "r3_host_output.dat", host_output, fmt="%.12g")

        write_build_options(output_dir, csim=True, synth=False)
        csim_rc, csim_seconds = run_vitis(output_dir, args.vitis_hls.resolve(), output_dir / "r3_csim.log")
        result.update({"csim_return_code": csim_rc, "csim_seconds": round(csim_seconds, 3)})
        if csim_rc:
            report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError(f"Vitis HLS CSim failed; see {output_dir / 'r3_csim.log'}")

        candidates = list(output_dir.rglob("csim_results.log"))
        if not candidates:
            raise FileNotFoundError("Vitis HLS did not produce csim_results.log")
        csim_output = r32.read_matrix(candidates[0])
        pc_reference = r32.quantize_reference(keras_output, output_precision)
        csim_codes = fixed_codes(csim_output, output_precision)
        pc_codes = fixed_codes(pc_reference, output_precision)
        host_codes = fixed_codes(host_output, output_precision)
        pc_delta = csim_codes - pc_codes
        host_delta = csim_codes - host_codes
        result.update(
            {
                "bit_exact_qkeras_vs_csim": bool(np.array_equal(pc_codes, csim_codes)),
                "qkeras_csim_nonzero_count": int(np.count_nonzero(pc_delta)),
                "qkeras_csim_max_lsb_diff": int(np.max(np.abs(pc_delta))),
                "bit_exact_host_vs_csim": bool(np.array_equal(host_codes, csim_codes)),
                "host_csim_nonzero_count": int(np.count_nonzero(host_delta)),
                "host_csim_max_lsb_diff": int(np.max(np.abs(host_delta))),
                "top1_agreement": float(
                    np.mean(np.argmax(csim_output, axis=1) == np.argmax(keras_output, axis=1))
                ),
            }
        )
        if not result["bit_exact_qkeras_vs_csim"] or not result["bit_exact_host_vs_csim"]:
            report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError("Streaming CSim is not bit exact; synthesis intentionally stopped")

    if not args.skip_synth:
        write_build_options(output_dir, csim=False, synth=True)
        synth_rc, synth_seconds = run_vitis(output_dir, args.vitis_hls.resolve(), output_dir / "r3_synth.log")
        result.update({"synth_return_code": synth_rc, "synth_seconds": round(synth_seconds, 3)})
        if synth_rc:
            report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError(f"Vitis HLS synthesis failed; see {output_dir / 'r3_synth.log'}")

        parsed = r32.hls4ml.report.parse_vivado_report(str(output_dir)) or {}
        csynth = parsed.get("CSynthesisReport", {})
        utilization = {
            resource: percentage(csynth, resource) for resource in ("LUT", "FF", "BRAM_18K", "DSP")
        }
        timing_ok = float(csynth["EstimatedClockPeriod"]) <= float(csynth["TargetClockPeriod"])
        latency_ok = int(csynth["WorstLatency"]) <= 10_000_000
        resource_ok = all(
            utilization[name] is not None and utilization[name] <= limit
            for name, limit in RESOURCE_LIMITS.items()
        )
        result.update(
            {
                "csynthesis": csynth,
                "utilization_percent": utilization,
                "limits_percent": RESOURCE_LIMITS,
                "timing_ok": timing_ok,
                "latency_ok": latency_ok,
                "resource_ok": resource_ok,
                "r3_3_pass": bool(timing_ok and latency_ok and resource_ok),
                "estimated_fmax_mhz": 1000.0 / float(csynth["EstimatedClockPeriod"]),
                "estimated_fps": 1.0e9
                / (float(csynth["EstimatedClockPeriod"]) * int(csynth["WorstLatency"])),
                "independent_ip_exported": False,
                "status": (
                    "ready_for_ip_export"
                    if timing_ok and latency_ok and resource_ok
                    else "blocked_by_hls_resource_or_timing"
                ),
            }
        )

    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
