"""Download the exact TensorFlow 2.12.1 CMake pins, without board Internet access."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "deps"
PINS = {
    "abseil-cpp": "https://github.com/abseil/abseil-cpp/archive/273292d1cfc0a94a65082ee350509af1d113344d.tar.gz",
    "cpuinfo": "https://github.com/pytorch/cpuinfo/archive/3dc310302210c1891ffcfb12ae67b11a3ad3a150.tar.gz",
    "eigen": "https://storage.googleapis.com/mirror.tensorflow.org/gitlab.com/libeigen/eigen/-/archive/3460f3558e7b469efb8a225894e21929c8c77629/eigen-3460f3558e7b469efb8a225894e21929c8c77629.tar.gz",
    "farmhash": "https://github.com/google/farmhash/archive/0d859a811870d10f53a594927d0d0b97573ad06d.tar.gz",
    "fft2d": "https://storage.googleapis.com/mirror.tensorflow.org/github.com/petewarden/OouraFFT/archive/v1.0.tar.gz",
    "flatbuffers": "https://github.com/google/flatbuffers/archive/v2.0.6.tar.gz",
    "fp16_headers": "https://github.com/Maratyszcza/FP16/archive/0a92994d729ff76a58f692d3028ca1b64b145d91.tar.gz",
    "gemmlowp": "https://github.com/google/gemmlowp/archive/fda83bdc38b118cc6b56753bd540caa49e570745.tar.gz",
    "ruy": "https://github.com/google/ruy/archive/3286a34cc8de6149ac6844107dfdffac91531e72.tar.gz",
    "xnnpack": "https://github.com/google/XNNPACK/archive/659147817805d17c7be2d60bd7bbca7e780f9c82.tar.gz",
}

def fetch(item):
    name, url = item
    path = OUT / (name + ".tar.gz")
    subprocess.run(["curl.exe", "--ssl-no-revoke", "-L", "--fail", "--retry", "2",
                    "--connect-timeout", "20", "-sS", "-o", str(path), url], check=True)
    if path.stat().st_size < 1000:
        raise RuntimeError(f"Truncated dependency: {name}")
    return {"name": name, "url": url, "file": path.name,
            "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, PINS.items()))
    (OUT / "downloads.json").write_text(json.dumps(records, indent=2) + "\n")
    for record in records:
        print(record["name"], record["bytes"], record["sha256"])
