"""按既有时间清单，从原片生成原尺寸手语视频。

本脚本只做“时间截取”，不做画面矩形裁剪：
- 时间边界来自 material_fullframe_20261021/全部22parts_训练样本清单_20261020.csv；
- 输出统一为原片 352x288、20 fps、无音轨；
- 输出写入独立目录，不覆盖旧数据集。

用法（在项目根目录执行）：
    python tools/clipping/export_fullframe_dataset.py
    python tools/clipping/export_fullframe_dataset.py --skip-encode
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parent
ROOT = METHOD_DIR.parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "exports" / "material_fullframe_20261021"
SOURCE_RECORDS = ROOT / "data" / "manifests" / "全22课_fullframe"
SOURCE_MANIFEST = SOURCE_RECORDS / "全部22parts_训练样本清单_20261020.csv"
SOURCE_UNCERTAINTIES = SOURCE_RECORDS / "全部22parts_不确定与不足项_20261020.csv"
SOURCE_DESCRIPTION = SOURCE_RECORDS / "全部22parts_导出说明_20261020.md"
FFMPEG = next((ROOT / "训练视频" / ".tools" / "imageio_ffmpeg" / "binaries").glob("ffmpeg*.exe"))
EXPECTED_WIDTH = 352
EXPECTED_HEIGHT = 288
EXPECTED_FPS = 20.0

# 旧版固定裁剪误判的候选。它们有时间窗，且原片全画幅可见完整手部。
# 仅用于首次重建；不依据模糊范围新增样本。
RECOVERABLE = [
    ("p15_005", "百货", "p15", 146.0, 150.0),
    ("p16_004", "个", "p16", 96.0, 100.0),
    ("p16_006", "大", "p16", 134.0, 138.0),
    ("p16_008", "中国", "p16", 226.0, 230.0),
    ("p17_004", "烤鸭", "p17", 132.0, 136.0),
    ("p18_009", "交往", "p18", 514.0, 518.0),
    ("p18_011", "他们", "p18", 564.0, 568.0),
    ("p21_003", "旅游", "p21", 100.0, 104.0),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {result.stderr}")
    return result


def source_path(part: str) -> Path:
    return ROOT / "video" / f"BV1Hs411E7aP_{part}.mp4"


def source_duration(path: Path) -> float:
    result = subprocess.run(
        [str(FFMPEG), "-hide_banner", "-i", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"duration not found: {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def read_source_rows() -> list[dict[str, str]]:
    with SOURCE_MANIFEST.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def make_row(
    category: str,
    sample: str,
    part: str,
    start: float,
    end: float,
    basis: str,
    confidence: str,
    source: Path,
) -> dict[str, str]:
    return {
        "类别": category,
        "样本编号": sample,
        "part": part,
        "原片起始秒": f"{start:.2f}",
        "原片结束秒": f"{end:.2f}",
        "输出路径": "",
        "原片路径": str(source),
        "标注依据": basis,
        "置信度": confidence,
        "裁剪": "full-frame",
        "分辨率": f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}",
        "帧率": "20",
        "音轨": "0",
        "连续原片区间": "True",
        "完整解码": "",
        "视觉核对": "",
        "帧数": "",
        "SHA256": "",
        "来源清单": str(SOURCE_MANIFEST),
    }


def build_rows() -> list[dict[str, str]]:
    rows = []
    for source_row in read_source_rows():
        part = source_row["part"]
        rows.append(
            make_row(
                source_row["类别"],
                source_row["样本编号"],
                part,
                float(source_row["原片起始秒"]),
                float(source_row["原片结束秒"]),
                source_row["标注依据"],
                source_row["置信度"],
                source_path(part),
            )
        )
    for sample, category, part, start, end in RECOVERABLE:
        rows.append(
            make_row(
                category,
                sample,
                part,
                start,
                end,
                "固定裁剪误判候选；全画幅保留完整手势",
                "中高",
                source_path(part),
            )
        )
    return rows


def output_path(output_dir: Path, row: dict[str, str]) -> Path:
    suffix = "_全画幅" if row["样本编号"] in {r[0] for r in RECOVERABLE} else ""
    return output_dir / row["类别"] / f"{row['样本编号']}_{row['类别']}{suffix}.mp4"


def encode(row: dict[str, str], target: Path, overwrite: bool) -> None:
    source = Path(row["原片路径"])
    if not source.exists():
        raise FileNotFoundError(source)
    start = float(row["原片起始秒"])
    end = float(row["原片结束秒"])
    duration = round(end - start, 2)
    if duration <= 0:
        raise ValueError(f"bad range: {row}")
    if source_duration(source) + 1e-6 < end:
        raise ValueError(f"range exceeds source duration: {row}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        raise FileExistsError(target)
    flags = ["-y"] if overwrite else ["-n"]
    run(
        [
            str(FFMPEG),
            "-hide_banner",
            "-nostdin",
            *flags,
            "-ss",
            f"{start:.3f}",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-an",
            "-vf",
            "setpts=PTS-STARTPTS,fps=20:start_time=0",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-metadata",
            f"title={row['类别']} ({row['样本编号']})",
            str(target),
        ]
    )


def probe(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [str(FFMPEG), "-hide_banner", "-i", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = result.stderr
    video = re.search(r"Video: .*?, (\d+)x(\d+).*?, ([\d.]+) fps", text)
    audio = re.search(r"Stream #.*: Audio:", text)
    duration = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if not video:
        raise RuntimeError(f"video metadata missing: {path}")
    width, height, fps = video.groups()
    return {
        "width": int(width),
        "height": int(height),
        "fps": float(fps),
        "audio": bool(audio),
        "duration": (
            int(duration.group(1)) * 3600
            + int(duration.group(2)) * 60
            + float(duration.group(3))
            if duration
            else None
        ),
    }


def full_decode(path: Path) -> int:
    result = run(
        [
            str(FFMPEG),
            "-hide_banner",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-progress",
            "pipe:1",
            "-nostats",
            "-f",
            "null",
            "-",
        ]
    )
    fields = dict(re.findall(r"^(\w+)=(.*)$", result.stdout, re.M))
    return int(fields["frame"])


def main() -> None:
    parser = argparse.ArgumentParser(description="按既有时间清单生成原尺寸全画幅视频")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖输出文件")
    parser.add_argument("--skip-encode", action="store_true", help="只核验已有输出")
    args = parser.parse_args()
    args.out_dir = args.out_dir.resolve()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    for row in rows:
        target = output_path(args.out_dir, row)
        row["输出路径"] = str(target)
        if not args.skip_encode:
            encode(row, target, args.overwrite)
            print(f"encoded {row['样本编号']} {row['类别']}", flush=True)

    for row in rows:
        target = Path(row["输出路径"])
        if not target.exists():
            raise FileNotFoundError(target)
        metadata = probe(target)
        if (metadata["width"], metadata["height"]) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
            raise ValueError(f"resolution mismatch: {target} {metadata}")
        if abs(metadata["fps"] - EXPECTED_FPS) > 0.01:
            raise ValueError(f"fps mismatch: {target} {metadata}")
        if metadata["audio"]:
            raise ValueError(f"unexpected audio stream: {target}")
        expected_duration = round(float(row["原片结束秒"]) - float(row["原片起始秒"]), 2)
        if metadata["duration"] is None or abs(metadata["duration"] - expected_duration) > 0.051:
            raise ValueError(f"duration mismatch: {target} {metadata} expected {expected_duration}")
        row["帧数"] = str(full_decode(target))
        row["完整解码"] = "passed"
        row["SHA256"] = sha256(target)

    output_manifest = args.out_dir / "dataset_manifest_fullframe_20261021.csv"
    with output_manifest.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_manifest": str(SOURCE_MANIFEST),
        "source_uncertainties": str(SOURCE_UNCERTAINTIES),
        "output_manifest": str(output_manifest),
        "expected": {"width": EXPECTED_WIDTH, "height": EXPECTED_HEIGHT, "fps": EXPECTED_FPS},
        "counts": {
            "source_clips": len(read_source_rows()),
            "recovered_candidates": len(RECOVERABLE),
            "output_clips": len(rows),
            "categories": len({r["类别"] for r in rows}),
        },
        "parts": dict(sorted(Counter(r["part"] for r in rows).items())),
        "recovered": sorted(r[0] for r in RECOVERABLE),
        "checks": {
            "missing_output": 0,
            "resolution_mismatches": 0,
            "fps_mismatches": 0,
            "audio_streams": 0,
            "duration_mismatches": 0,
            "decode_failures": 0,
        },
        "limitations": [
            "This release changes only the picture extent: no picture crop is used.",
            "Uncertainty rows without exact export ranges remain unexported.",
        ],
    }
    (args.out_dir / "validation_fullframe_20261021.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(output_manifest)


if __name__ == "__main__":
    main()
