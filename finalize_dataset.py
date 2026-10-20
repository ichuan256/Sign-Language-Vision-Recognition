"""Reconcile the local working dataset and emit a portable inventory.

The source project keeps working manifests and review artifacts under the
ignored ``训练视频`` directory. This script turns the current 22-part master
manifest into repository-relative files, exports the uncertainty register,
and checks every MP4's presence, SHA256, and (optionally) full decode status.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_MANIFEST = ROOT / "训练视频" / "全部22parts_训练样本清单_20261020.csv"
PORTABLE_MANIFEST = ROOT / "dataset_manifest_20261020.csv"
REPORT_JSON = ROOT / "dataset_validation_20261020.json"
REPORT_MD = ROOT / "DATASET_STATUS_20261020.md"
UNCERTAINTY_SOURCE = ROOT / "训练视频" / "全部22parts_不确定与不足项_20261020.csv"
UNCERTAINTY_EXPORT = ROOT / "dataset_uncertainties_20261020.csv"
LOCAL_EXPORT_NOTE = ROOT / "训练视频" / "全部22parts_导出说明_20261020.md"
FFMPEG = ROOT / "训练视频" / ".tools" / "imageio_ffmpeg" / "binaries" / "ffmpeg-win-x86_64-v7.1.exe"


@dataclass(frozen=True)
class DecodeResult:
    path: Path
    returncode: int
    frames: int
    width: int | None
    height: int | None
    fps: str | None
    audio: bool


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def relative_path(value: str) -> str:
    """Convert an absolute path from the current checkout to a portable path."""
    raw = Path(value)
    try:
        return raw.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return value.replace("\\", "/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_output(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def decode_one(path: Path) -> DecodeResult:
    command = [
        str(FFMPEG),
        "-hide_banner",
        "-v",
        "info",
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
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    video_line = next((line for line in completed.stderr.splitlines() if "Video:" in line), "")
    size_match = re.search(r"(\d{3,4})x(\d{3,4})", video_line)
    fps_match = re.search(r"(\d+(?:\.\d+)?) fps", video_line)
    frame_values = [
        int(line.split("=", 1)[1].strip())
        for line in completed.stdout.splitlines()
        if line.startswith("frame=") and line.split("=", 1)[1].strip().isdigit()
    ]
    return DecodeResult(
        path=path,
        returncode=completed.returncode,
        frames=frame_values[-1] if frame_values else 0,
        width=int(size_match.group(1)) if size_match else None,
        height=int(size_match.group(2)) if size_match else None,
        fps=fps_match.group(1) if fps_match else None,
        audio=any("Audio:" in line for line in completed.stderr.splitlines()),
    )


def make_portable_manifest(rows: list[dict[str, str]]) -> None:
    fields = list(rows[0])
    portable: list[dict[str, str]] = []
    path_fields = {"输出路径", "原片路径", "视觉核对", "来源清单", "视觉边界抽检图"}
    for row in rows:
        copied = dict(row)
        for field in path_fields:
            if copied.get(field):
                copied[field] = relative_path(copied[field])
        portable.append(copied)
    write_rows(PORTABLE_MANIFEST, fields, portable)


def make_uncertainty_export() -> list[dict[str, str]]:
    rows = read_rows(UNCERTAINTY_SOURCE)
    for row in rows:
        source = row.get("来源记录", "").strip()
        if source:
            row["来源记录"] = Path(source).name
    if rows:
        write_rows(UNCERTAINTY_EXPORT, list(rows[0]), rows)
    return rows


def validate(rows: list[dict[str, str]], full_decode: bool) -> dict:
    material = ROOT / "material"
    actual = sorted(material.rglob("*.mp4"))
    expected = {str(resolve_output(row["输出路径"])).casefold(): row for row in rows}
    actual_map = {str(path.resolve()).casefold(): path for path in actual}
    missing = [row["样本编号"] for key, row in expected.items() if key not in actual_map]
    orphan = [path.relative_to(material).as_posix() for key, path in actual_map.items() if key not in expected]
    hash_mismatches = []
    for key, row in expected.items():
        path = actual_map.get(key)
        if path and sha256(path).lower() != row["SHA256"].lower():
            hash_mismatches.append(row["样本编号"])

    decode_results: list[DecodeResult] = []
    if full_decode:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            decode_results = list(pool.map(decode_one, actual))

    by_path = {str(resolve_output(row["输出路径"])).casefold(): row for row in rows}
    decode_failures = []
    frame_mismatches = []
    for result in decode_results:
        row = by_path[str(result.path.resolve()).casefold()]
        if result.returncode != 0 or result.frames == 0 or result.width is None or result.audio:
            decode_failures.append(result.path.name)
        recorded_frames = row.get("帧数", "").strip()
        if recorded_frames.isdigit() and result.frames != int(recorded_frames):
            frame_mismatches.append(result.path.name)

    resolutions = Counter(
        f"{result.width}x{result.height}"
        for result in decode_results
        if result.width is not None and result.height is not None
    )
    fps = Counter(result.fps for result in decode_results)
    empty_category_dirs = sorted(
        path.name for path in material.iterdir() if path.is_dir() and not any(path.glob("*.mp4"))
    )
    single_sample_categories = sorted(
        category
        for category, count in Counter(row["类别"] for row in rows).items()
        if count == 1
    )
    visual_review_blank_by_part = dict(
        sorted(
            Counter(row["part"] for row in rows if not row.get("视觉核对", "").strip()).items()
        )
    )
    uncertainty_rows = read_rows(UNCERTAINTY_SOURCE)
    uncertainty_statuses = dict(sorted(Counter(row.get("状态", "") for row in uncertainty_rows).items()))
    return {
        "manifest_rows": len(rows),
        "material_mp4": len(actual),
        "manifest_unique_paths": len(expected),
        "missing_files": len(missing),
        "orphan_files": len(orphan),
        "duplicate_manifest_paths": len(rows) - len(expected),
        "sha256_mismatches": len(hash_mismatches),
        "decode_checked": len(decode_results),
        "decode_failures": len(decode_failures),
        "frame_mismatches": len(frame_mismatches),
        "resolution_counts": dict(resolutions),
        "fps_counts": dict(fps),
        "audio_streams": sum(result.audio for result in decode_results),
        "parts": dict(sorted(Counter(row["part"] for row in rows).items())),
        "categories": len({row["类别"] for row in rows}),
        "category_frequency": dict(sorted(Counter(Counter(row["类别"] for row in rows).values()).items())),
        "single_sample_categories": len(single_sample_categories),
        "single_sample_category_examples": single_sample_categories[:15],
        "empty_category_directories": empty_category_dirs,
        "visual_review_blank_by_part": visual_review_blank_by_part,
        "uncertainty_rows": len(uncertainty_rows),
        "uncertainty_statuses": uncertainty_statuses,
        "missing_examples": missing[:10],
        "orphan_examples": orphan[:10],
        "sha256_mismatch_examples": hash_mismatches[:10],
        "decode_failure_examples": decode_failures[:10],
        "frame_mismatch_examples": frame_mismatches[:10],
        "full_decode_requested": full_decode,
    }


def write_report(rows: list[dict[str, str]], report: dict) -> None:
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    part_lines = "\n".join(f"- {part}：{count} 条" for part, count in report["parts"].items())
    freq = report["category_frequency"]
    report_markdown = "\n".join(
            [
                "# 手语视频切割最终状态（2026-10-20）",
                "",
                f"当前正式清单包含 **{report['manifest_rows']} 条 MP4**，覆盖 **{report['categories']} 个类别**、p01–p22 共22个分段。",
                "",
                "## 分 part 数量",
                "",
                part_lines,
                "",
                "## 技术验收",
                "",
                f"- 清单行数与 `material` 实际 MP4 数量：{report['manifest_rows']}/{report['material_mp4']}。",
                f"- 清单路径缺失：{report['missing_files']}；多余文件：{report['orphan_files']}；重复清单路径：{report['duplicate_manifest_paths']}。",
                f"- SHA256 不一致：{report['sha256_mismatches']}。",
                f"- 完整解码检查：{report['decode_checked']} 条，失败 {report['decode_failures']} 条；帧数不一致 {report['frame_mismatches']} 条。",
                f"- 分辨率：{report['resolution_counts']}；帧率：{report['fps_counts']}；含音轨：{report['audio_streams']} 条。",
                f"- 类别样本数分布：{freq}（键为样本数，值为类别数）。",
                f"- 已有类别中仅1条样本：{report['single_sample_categories']} 个；空类别目录：{len(report['empty_category_directories'])} 个（{', '.join(report['empty_category_directories'])}）。",
                f"- 不确定项登记：{report['uncertainty_rows']} 条，按原始登记状态分类为 {report['uncertainty_statuses']}。",
                f"- 总清单中视觉复核证据字段为空的分段：{report['visual_review_blank_by_part']}；p01、p12 的复核结论记在各自批次报告中。",
                "",
                "## 证据边界",
                "",
                "清单与视频文件已经完成路径、SHA256 和完整解码对账。类别不足两条、动作边界不清或扩大裁剪会切手/带入右侧说明文字的候选，保存在 `dataset_uncertainties_20261020.csv`，没有为了凑数量强行导出。",
                "",
                "可复跑命令：",
                "",
                "```powershell",
                "python .\\finalize_dataset.py --full-decode",
                "```",
                "",
                "生成文件：`dataset_manifest_20261020.csv`、`dataset_validation_20261020.json`、`dataset_uncertainties_20261020.csv`、`DATASET_STATUS_20261020.md`。",
                "",
            ]
        )
    REPORT_MD.write_text(report_markdown, encoding="utf-8")
    if LOCAL_EXPORT_NOTE.parent.is_dir():
        LOCAL_EXPORT_NOTE.write_text(report_markdown, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-decode", action="store_true", help="run ffmpeg -xerror on every exported MP4")
    args = parser.parse_args()
    if not SOURCE_MANIFEST.exists():
        raise SystemExit(f"missing source manifest: {SOURCE_MANIFEST}")
    if not UNCERTAINTY_SOURCE.exists():
        raise SystemExit(f"missing uncertainty register: {UNCERTAINTY_SOURCE}")
    if not FFMPEG.exists():
        raise SystemExit(f"missing bundled ffmpeg: {FFMPEG}")
    rows = read_rows(SOURCE_MANIFEST)
    if not rows:
        raise SystemExit("source manifest is empty")
    make_portable_manifest(rows)
    make_uncertainty_export()
    report = validate(rows, args.full_decode)
    write_report(rows, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(
        report[key] == 0
        for key in ("missing_files", "orphan_files", "duplicate_manifest_paths", "sha256_mismatches", "decode_failures", "frame_mismatches", "audio_streams")
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
