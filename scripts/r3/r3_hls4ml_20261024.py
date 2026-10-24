# -*- coding: utf-8 -*-
"""R3.2: convert the R3.1 QKeras model and run Vitis HLS C simulation.

The script intentionally keeps generated HLS sources under ``_tmp/r3``.  The
durable evidence is the JSON report written under ``analysis/r3/``.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np

# hls4ml 1.3.0 still calls the NumPy 1.x alias removed in NumPy 2.x.
if not hasattr(np, "product"):
    np.product = np.prod  # type: ignore[attr-defined]

import tf_keras

# The saved R3.1 model is a tf-keras/Keras-2 model.  hls4ml otherwise sees the
# separately installed Keras 3 package and selects the incompatible v3 parser.
sys.modules["keras"] = tf_keras

import hls4ml
from qkeras.utils import load_qmodel


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / "_tmp" / "r3"
DEFAULT_HLS_DIR = DEFAULT_CACHE / "r3_hls4ml_vitis"
DEFAULT_REPORT = ROOT / "analysis" / "r3" / "r3_hls4ml_20261024.json"
PART = "xc7z020clg400-1"


def test_indices(y: np.ndarray) -> np.ndarray:
    """Reproduce the exact stratified holdout used by R3.1."""
    rng = np.random.default_rng(20261024)
    selected: list[int] = []
    for cls in np.unique(y):
        idx = np.where(y == cls)[0]
        rng.shuffle(idx)
        selected.extend(idx[: max(1, len(idx) // 4)])
    return np.asarray(selected, dtype=np.int64)


def read_matrix(path: Path) -> np.ndarray:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append([float(value) for value in line.split()])
    return np.asarray(rows, dtype=np.float64)


def precision_shape(precision: str) -> tuple[int, int]:
    match = re.search(r"(?:ap_)?(?:u)?fixed<(\d+),(\d+)", precision)
    if not match:
        raise ValueError(f"Unsupported output precision: {precision}")
    return int(match.group(1)), int(match.group(2))


def quantize_reference(values: np.ndarray, precision: str) -> np.ndarray:
    """Apply the default ap_fixed AP_TRN/AP_WRAP conversion used at the port."""
    width, integer = precision_shape(precision)
    fractional = width - integer
    scale = float(1 << fractional)
    raw = np.floor(values * scale).astype(np.int64)
    modulus = 1 << width
    raw = ((raw + (1 << (width - 1))) % modulus) - (1 << (width - 1))
    return raw.astype(np.float64) / scale


def run_vitis_csim(vitis_hls: Path, output_dir: Path, log_path: Path) -> int:
    command = [
        "cmd.exe",
        "/c",
        str(vitis_hls),
        "-f",
        "build_prj.tcl",
    ]
    started = time.time()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        completed = subprocess.run(
            command,
            cwd=output_dir,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
        log.write(f"\nR3_CSIM_SECONDS={time.time() - started:.3f}\n")
        log.write(f"R3_CSIM_RETURN_CODE={completed.returncode}\n")
    return completed.returncode


def compile_host_reference(gxx: Path, output_dir: Path) -> Path:
    """Build the generated fixed-point C++ with an independent host compiler."""
    dll = output_dir / "firmware" / "gesture_cls_host.dll"
    source = (output_dir / "firmware" / "gesture_cls.cpp").read_text(encoding="utf-8")
    # The io_parallel network has several MiB of intermediate arrays.  Vitis
    # CSim enlarges its process stack, while a DLL called from Python does not.
    # Static storage changes lifetime only, not the fixed-point operations.
    source = re.sub(
        r"^    ([A-Za-z_]\w*) (layer\d+_out\[[^\r\n;]+;)$",
        r"    static \1 \2",
        source,
        flags=re.MULTILINE,
    )
    host_source = output_dir / "firmware" / "gesture_cls_host.cpp"
    host_source.write_text(source, encoding="utf-8")
    # GCC 9.5 bundled with Vitis HLS crashes while optimizing this very large
    # template translation unit; -O0 is slower at runtime but deterministic.
    common = ["-O0", "-std=c++11", "-Ifirmware/ap_types"]
    commands = [
        [str(gxx), *common, "-c", "firmware/gesture_cls_host.cpp", "-o", "gesture_cls.o"],
        [str(gxx), *common, "-c", "gesture_cls_bridge.cpp", "-o", "gesture_cls_bridge.o"],
        [str(gxx), "-shared", "gesture_cls.o", "gesture_cls_bridge.o", "-o", str(dll)],
    ]
    log_path = output_dir / "r3_host_compile.log"
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        for command in commands:
            log.write("COMMAND: " + subprocess.list2cmdline(command) + "\n")
            log.flush()
            completed = subprocess.run(command, cwd=output_dir, stdout=log, stderr=subprocess.STDOUT, check=False)
            log.write(f"RETURN_CODE: {completed.returncode}\n")
            log.flush()
            if completed.returncode:
                raise RuntimeError(f"Host C++ reference build failed; see {log_path}")
    return dll


def run_host_reference(dll_path: Path, gxx: Path, inputs: np.ndarray) -> np.ndarray:
    dll_dirs = []
    if hasattr(os, "add_dll_directory"):
        dll_dirs.append(os.add_dll_directory(str(gxx.parent)))
    try:
        library = ctypes.CDLL(str(dll_path))
        infer = library.gesture_cls_float
        pointer = ctypes.POINTER(ctypes.c_float)
        infer.argtypes = [pointer, pointer]
        infer.restype = None
        outputs = np.empty((len(inputs), 14), dtype=np.float32)
        previous_cwd = Path.cwd()
        os.chdir(dll_path.parent)
        try:
            for sample, output in zip(np.ascontiguousarray(inputs, dtype=np.float32), outputs):
                infer(sample.ctypes.data_as(pointer), output.ctypes.data_as(pointer))
        finally:
            os.chdir(previous_cwd)
        return outputs.astype(np.float64)
    finally:
        for handle in dll_dirs:
            handle.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=DEFAULT_CACHE / "r3_model_quant.keras")
    parser.add_argument("--tensors", type=Path, default=DEFAULT_CACHE / "tensors.npz")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_HLS_DIR)
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
    parser.add_argument("--samples", type=int, default=0, help="0 means all 14 holdout samples")
    parser.add_argument("--trace", action="store_true", help="dump selected intermediate activations")
    parser.add_argument("--skip-csim", action="store_true")
    args = parser.parse_args()

    model_path = args.model.resolve()
    tensors_path = args.tensors.resolve()
    output_dir = args.output_dir.resolve()
    report_path = args.report.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    data = np.load(tensors_path, allow_pickle=False)
    idx = test_indices(data["y"])
    if args.samples > 0:
        idx = idx[: args.samples]
    inputs = data["X"][idx].astype(np.float32) / 255.0

    model = load_qmodel(model_path, compile=False)
    keras_output = model.predict(inputs, verbose=0).astype(np.float64)

    input_npy = output_dir / "r3_csim_input.npy"
    keras_npy = output_dir / "r3_keras_output.npy"
    np.save(input_npy, inputs)
    np.save(keras_npy, keras_output)

    config = hls4ml.utils.config_from_keras_model(
        model,
        granularity="name",
        backend="Vitis",
        default_precision="ap_fixed<24,10>",
        default_reuse_factor=1,
    )
    config["Model"]["Strategy"] = "Latency"
    config["Model"]["TraceOutput"] = args.trace
    # uint8/255 preprocessing produces exact float32 values that need more
    # fractional bits than the model-wide arithmetic default.  Preserve the
    # PC input before the first explicit QActivation boundary.
    config["LayerName"]["input_1"]["Precision"]["result"] = "ap_fixed<40,2>"
    # Batch-normalization parameters are float32 in the trained model.  The
    # hls4ml default inherited from Model precision (24,10) moves some QReLU
    # thresholds enough to change output bits.  Preserve them through the
    # following explicit 6-bit QActivation; the wide values do not propagate
    # beyond that quantizer.
    for layer_name, layer_config in config["LayerName"].items():
        if layer_name.startswith("batch_normalization"):
            layer_config["Precision"]["scale"] = "ap_fixed<48,16>"
            layer_config["Precision"]["bias"] = "ap_fixed<48,16>"
        if args.trace and layer_name in {"act1", "act2", "act3", "act4", "global_average_pooling2d", "qdense"}:
            layer_config["Trace"] = True

    hls_model = hls4ml.converters.convert_from_keras_model(
        model,
        output_dir=str(output_dir),
        project_name="gesture_cls",
        input_data_tb=str(input_npy),
        output_data_tb=str(keras_npy),
        backend="Vitis",
        hls_config=config,
        part=PART,
        clock_period=10,
        io_type="io_parallel",
    )
    hls_model.write()
    # hls4ml 1.3 uses this sourced file rather than Tcl command-line options.
    # Keep R3.2 strictly at C simulation; synthesis belongs to R3.3.
    (output_dir / "build_opt.tcl").write_text(
        """array set opt {
    reset      1
    csim       1
    synth      0
    cosim      0
    validation 0
    export     0
    vsynth     0
    fifo_opt   0
}
""",
        encoding="utf-8",
    )
    output_precision = str(hls_model.get_output_variables()[0].type.precision)
    host_dll = compile_host_reference(args.gxx.resolve(), output_dir)
    host_output = run_host_reference(host_dll, args.gxx.resolve(), inputs)
    np.savetxt(output_dir / "r3_host_fixed_output.dat", host_output, fmt="%.12g")

    csim_log = output_dir / "r3_vitis_csim.log"
    return_code = None
    if not args.skip_csim:
        return_code = run_vitis_csim(args.vitis_hls.resolve(), output_dir, csim_log)
        if return_code != 0:
            raise RuntimeError(f"Vitis HLS C simulation failed; see {csim_log}")

    csim_candidates = list(output_dir.rglob("csim_results.log"))
    csim_results = csim_candidates[0] if csim_candidates else output_dir / "tb_data" / "csim_results.log"
    report: dict[str, object] = {
        "milestone": "R3.2",
        "hls4ml_version": hls4ml.__version__,
        "backend": "Vitis",
        "part": PART,
        "clock_period_ns": 10,
        "model": str(model_path.relative_to(ROOT)),
        "samples": int(len(inputs)),
        "holdout_indices": idx.tolist(),
        "output_precision": output_precision,
        "vitis_csim_return_code": return_code,
        "host_reference_compiler": str(args.gxx.resolve()),
        "generated_project": str(output_dir.relative_to(ROOT)),
    }

    if csim_results.is_file():
        csim_output = read_matrix(csim_results)
        port_reference = quantize_reference(keras_output, output_precision)
        delta = csim_output - port_reference
        keras_delta = csim_output - keras_output
        width, integer = precision_shape(output_precision)
        output_scale = 1 << (width - integer)
        host_codes = np.rint(host_output * output_scale).astype(np.int64)
        csim_codes = np.rint(csim_output * output_scale).astype(np.int64)
        port_codes = np.rint(port_reference * output_scale).astype(np.int64)
        code_delta = csim_codes - host_codes
        pc_code_delta = csim_codes - port_codes
        report.update(
            {
                "outputs": int(csim_output.size),
                "bit_exact_host_vs_vitis_csim": bool(np.array_equal(host_codes, csim_codes)),
                "host_vitis_nonzero_bit_count": int(np.count_nonzero(code_delta)),
                "host_vitis_max_lsb_diff": int(np.max(np.abs(code_delta))),
                "bit_exact_qkeras_port_vs_vitis_csim": bool(np.array_equal(port_codes, csim_codes)),
                "qkeras_vitis_nonzero_bit_count": int(np.count_nonzero(pc_code_delta)),
                "qkeras_vitis_max_lsb_diff": int(np.max(np.abs(pc_code_delta))),
                "decimal_log_max_abs_diff": float(np.max(np.abs(delta))),
                "keras_decimal_log_max_abs_diff": float(np.max(np.abs(keras_delta))),
                "keras_top1_agreement": float(
                    np.mean(np.argmax(csim_output, axis=1) == np.argmax(keras_output, axis=1))
                ),
            }
        )
        np.savetxt(output_dir / "r3_pc_port_reference.dat", port_reference, fmt="%.12g")
        np.savetxt(output_dir / "r3_csim_minus_pc.dat", delta, fmt="%.12g")

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
