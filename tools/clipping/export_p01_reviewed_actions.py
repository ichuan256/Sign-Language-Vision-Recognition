"""Export the reviewed action cycles from the P01 boundary CSV.

The export keeps each original frame range and the full 1920x1080 image.
It writes a new, separately manifested package under material_fullframe_20261021
and refuses to overwrite an existing package.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    from .media_paths import add_source_arguments, find_ffmpeg, resolve_source, print_preflight
except ImportError:
    from media_paths import add_source_arguments, find_ffmpeg, resolve_source, print_preflight

ROOT = Path(__file__).resolve().parents[2]
SOURCE_CSV = Path(__file__).resolve().parent / "中国手语教程_P01对话_已核对动作边界_20261021.csv"
DATASET_ROOT = ROOT / "data" / "exports" / "material_fullframe_20261021"
FINAL_DIR = DATASET_ROOT / "第一课_动作周期_已核对_20261021"
INSPECT_DIR = ROOT / "_tmp" / "inspect"
FFMPEG = None
SOURCE_ROOT = None
EXPECTED_WIDTH = 1920
EXPECTED_HEIGHT = 1080
EXPECTED_FPS = 25


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stderr}"
        )
    return result


def probe(path: Path) -> dict[str, object]:
    result = run([str(FFMPEG), "-hide_banner", "-i", str(path)], check=False)
    text = result.stderr
    video_lines = [line for line in text.splitlines() if "Stream #" in line and "Video:" in line]
    if not video_lines:
        raise RuntimeError(f"No video stream found: {path}\n{text}")
    video_line = video_lines[0]
    # The stream id may contain values such as ``[0x1]`` before the actual
    # picture size. Match the resolution immediately before the SAR/DAR data.
    resolution = re.search(r",\s*(\d{2,5})x(\d{2,5})\s*\[", video_line)
    if not resolution:
        candidates = re.findall(r"(\d{2,5})x(\d{2,5})", video_line)
        if candidates:
            resolution = re.match(r"(\d+)x(\d+)", "x".join(candidates[-1]))
    fps = re.search(r"([\d.]+)\s+fps", video_line)
    duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)", text)
    if not resolution or not fps:
        raise RuntimeError(f"Could not read video metadata: {path}\n{text}")
    width, height = map(int, resolution.groups())
    duration_seconds = None
    if duration:
        hours, minutes, seconds = duration.groups()
        duration_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return {
        "width": width,
        "height": height,
        "fps": float(fps.group(1)),
        "duration_seconds": duration_seconds,
        "audio_streams": sum("Stream #" in line and "Audio:" in line for line in text.splitlines()),
        "video_line": video_line.strip(),
    }


def decoded_frame_count(path: Path) -> int:
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
            "-an",
            "-progress",
            "pipe:1",
            "-nostats",
            "-f",
            "null",
            "-",
        ]
    )
    matches = re.findall(r"^frame=(\d+)\s*$", result.stdout, re.MULTILINE)
    if not matches:
        raise RuntimeError(f"FFmpeg did not report decoded frames: {path}")
    return int(matches[-1])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_context(value: str) -> str:
    value = re.sub(r"[，。！？；：、,.!?;:\s]+", "", value)
    value = re.sub(r'[<>"/\\|?*\x00-\x1f]', "_", value).strip("._ ")
    return value[:48] or "未命名"


def safe_folder(value: str) -> str:
    """Keep the lesson label readable while replacing Windows-invalid characters."""
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return value[:80] or "未命名"


def read_rows() -> tuple[list[dict[str, str]], list[str]]:
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if len(rows) != 31:
        raise ValueError(f"Expected 31 reviewed action cycles; found {len(rows)}")
    if not fields:
        raise ValueError("CSV has no header")
    return rows, fields


def preflight(rows: list[dict[str, str]]) -> tuple[Path, dict[str, object], list[Path]]:
    if not DATASET_ROOT.is_dir():
        raise FileNotFoundError(DATASET_ROOT)
    if FINAL_DIR.exists():
        raise FileExistsError(f"Refusing to overwrite existing package: {FINAL_DIR}")
    source_paths: set[Path] = set()
    seen_ids: set[str] = set()
    old_files = sorted(path for path in DATASET_ROOT.rglob("*.mp4") if path.is_file())
    if len(old_files) != 233:
        raise ValueError(f"Expected 233 existing MP4 files before export; found {len(old_files)}")

    for row in rows:
        action_id = row["动作编号"]
        if action_id in seen_ids:
            raise ValueError(f"Duplicate action id: {action_id}")
        seen_ids.add(action_id)
        if "已核对" not in row["复核状态"]:
            raise ValueError(f"Unreviewed row: {action_id} ({row['复核状态']})")
        source = resolve_source(ROOT, family="NL_tutorial", recorded_path=row["原片路径"], source_root=SOURCE_ROOT)
        if not source.is_file():
            raise FileNotFoundError(source)
        source_paths.add(source)
        start = int(row["起始帧_含"])
        end = int(row["结束帧_不含"])
        fps = int(row["帧率"])
        if fps != EXPECTED_FPS or end <= start:
            raise ValueError(f"Invalid frame range or frame rate: {action_id}")
        if abs(float(row["起始秒"]) - start / fps) > 1e-6:
            raise ValueError(f"Start second does not match start frame: {action_id}")
        if abs(float(row["结束秒_不含"]) - end / fps) > 1e-6:
            raise ValueError(f"Exclusive end second does not match end frame: {action_id}")

    if len(source_paths) != 1:
        raise ValueError(f"Expected one source video for P01, found {len(source_paths)}")
    source = next(iter(source_paths))
    source_metadata = probe(source)
    if (source_metadata["width"], source_metadata["height"]) != (
        EXPECTED_WIDTH,
        EXPECTED_HEIGHT,
    ):
        raise ValueError(f"Unexpected source resolution: {source_metadata}")
    if abs(float(source_metadata["fps"]) - EXPECTED_FPS) > 0.01:
        raise ValueError(f"Unexpected source frame rate: {source_metadata}")
    return source, source_metadata, old_files


def encode_one(source: Path, stage: Path, row: dict[str, str]) -> tuple[Path, int]:
    action_id = row["动作编号"]
    start = int(row["起始帧_含"])
    end = int(row["结束帧_不含"])
    frame_count = end - start
    # Match the existing material layout: one action/phrase category folder,
    # with each reviewed take saved inside it.
    folder = safe_folder(row["词句上下文"])
    relative = Path(folder) / f"{action_id}_{safe_context(row['词句上下文'])}.mp4"
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(target)

    run(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-n",
            "-ss",
            f"{start / EXPECTED_FPS:.6f}",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-an",
            "-vf",
            "setpts=PTS-STARTPTS",
            "-frames:v",
            str(frame_count),
            "-r",
            str(EXPECTED_FPS),
            "-fps_mode",
            "cfr",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-metadata",
            f"title={action_id} {row['词句上下文']}",
            str(target),
        ]
    )
    return target, frame_count


def main() -> None:
    global ROOT, FFMPEG, SOURCE_ROOT, SOURCE_CSV, DATASET_ROOT, FINAL_DIR, INSPECT_DIR
    parser = argparse.ArgumentParser(description=__doc__)
    add_source_arguments(parser)
    parser.add_argument("--source-csv", type=Path)
    parser.add_argument("--dataset-root", type=Path)
    args = parser.parse_args()
    ROOT = args.repo_root.resolve()
    SOURCE_ROOT = args.source_root
    FFMPEG = find_ffmpeg(ROOT, args.ffmpeg)
    SOURCE_CSV = args.source_csv or ROOT / "tools/clipping/中国手语教程_P01对话_已核对动作边界_20261021.csv"
    DATASET_ROOT = args.dataset_root or ROOT / "data/exports/material_fullframe_20261021"
    FINAL_DIR = DATASET_ROOT / "第一课_动作周期_已核对_20261021"
    INSPECT_DIR = ROOT / "_tmp/inspect"
    if args.preflight:
        source_rows, _ = read_rows()
        sources = sorted({resolve_source(ROOT, family="NL_tutorial", recorded_path=r["原片路径"], source_root=SOURCE_ROOT) for r in source_rows})
        print_preflight(sources, FFMPEG, dataset_root=str(DATASET_ROOT), output_root=str(FINAL_DIR))
        return
    rows, source_fields = read_rows()
    source, source_metadata, old_files = preflight(rows)
    INSPECT_DIR.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="p01_material_export_20261021_", dir=INSPECT_DIR))
    staged_rows: list[dict[str, str]] = []
    print(f"Source: {source}", flush=True)
    print(f"Staging: {stage}", flush=True)

    try:
        for index, row in enumerate(rows, start=1):
            target, expected_frames = encode_one(source, stage, row)
            metadata = probe(target)
            actual_frames = decoded_frame_count(target)
            if (metadata["width"], metadata["height"]) != (
                EXPECTED_WIDTH,
                EXPECTED_HEIGHT,
            ):
                raise ValueError(f"Resolution mismatch: {target} {metadata}")
            if abs(float(metadata["fps"]) - EXPECTED_FPS) > 0.01:
                raise ValueError(f"Frame rate mismatch: {target} {metadata}")
            if metadata["audio_streams"] != 0:
                raise ValueError(f"Unexpected audio stream: {target}")
            if actual_frames != expected_frames:
                raise ValueError(
                    f"Frame count mismatch: {target}; expected {expected_frames}, got {actual_frames}"
                )
            expected_duration = expected_frames / EXPECTED_FPS
            if metadata["duration_seconds"] is None or abs(
                float(metadata["duration_seconds"]) - expected_duration
            ) > 0.011:
                raise ValueError(f"Duration mismatch: {target} {metadata}")

            staged = dict(row)
            staged.update(
                {
                    "输出相对路径": target.relative_to(stage).as_posix(),
                    "预期帧数": str(expected_frames),
                    "实际解码帧数": str(actual_frames),
                    "输出分辨率": f"{metadata['width']}x{metadata['height']}",
                    "输出帧率": str(metadata["fps"]),
                    "音轨数": str(metadata["audio_streams"]),
                    "完整解码": "passed",
                    "SHA256": sha256(target),
                }
            )
            staged_rows.append(staged)
            print(f"encoded and verified {index}/{len(rows)}: {row['动作编号']}", flush=True)

        output_fields = source_fields + [
            "输出相对路径",
            "预期帧数",
            "实际解码帧数",
            "输出分辨率",
            "输出帧率",
            "音轨数",
            "完整解码",
            "SHA256",
        ]
        manifest = stage / "第一课动作周期剪辑清单_20261021.csv"
        with manifest.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=output_fields)
            writer.writeheader()
            writer.writerows(staged_rows)

        solo_count = sum("单人" in row["目标人物"] for row in rows)
        dialogue_count = len(rows) - solo_count
        total_frames = sum(int(row["预期帧数"]) for row in staged_rows)
        readme = f"""# 第一课已核对动作周期剪辑（2026-10-21）

来源清单：`tools/clipping/中国手语教程_P01对话_已核对动作边界_20261021.csv`  
原片：`{Path(rows[0]['原片路径']).as_posix()}`

- 共 {len(rows)} 段：双人对话 {dialogue_count} 段，单人示范 {solo_count} 段。
- 每段严格按清单的 `起始帧_含` 至 `结束帧_不含` 导出；帧数等于结束帧减起始帧。
- 保留原片全画幅 1920×1080、25 fps，不做画面裁切；输出为 H.264、yuv420p、无音轨。
- 视频经过 CRF 18 转码；清单附有逐段预期/实际帧数、完整解码结果和 SHA-256。
- 按旧素材的整理方式，依据 `词句上下文` 建立 {len(set(r['词句上下文'] for r in rows))} 个动作文件夹；同一上下文的各次候选/周期视频集中在对应文件夹中，文件名保留动作编号。
- 文件夹名直接采用清单上下文，不为拆分周期另行赋予词义；目标人物和周期信息见剪辑清单。
- 若原清单的动作周期在原片时间上相邻或重叠，仍按各自经核对的帧边界原样保留。
- 原素材库原有 233 条视频及其主清单未改动；本包有独立清单。

验证汇总见 `validation_P01_actions_20261021.json`。
"""
        (stage / "README.md").write_text(readme, encoding="utf-8")
        validation = {
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "source_csv": SOURCE_CSV.relative_to(ROOT).as_posix(),
            "source_video": source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT) else str(source),
            "source_metadata": source_metadata,
            "output_directory": FINAL_DIR.relative_to(ROOT).as_posix(),
            "output_clips": len(staged_rows),
            "counts_by_folder": dict(Counter(r["词句上下文"] for r in rows)),
            "counts_by_target_person": dict(Counter(r["目标人物"] for r in rows)),
            "total_frames": total_frames,
            "output_profile": {
                "width": EXPECTED_WIDTH,
                "height": EXPECTED_HEIGHT,
                "fps": EXPECTED_FPS,
                "video_codec": "H.264 / libx264 CRF 18",
                "pixel_format": "yuv420p",
                "audio_streams": 0,
                "frame_ranges": "start inclusive, end exclusive",
            },
            "existing_mp4_count_before_export": len(old_files),
            "checks": {
                "missing_outputs": 0,
                "frame_count_mismatches": 0,
                "resolution_mismatches": 0,
                "fps_mismatches": 0,
                "audio_streams": 0,
                "duration_mismatches": 0,
                "full_decode_failures": 0,
            },
        }
        (stage / "validation_P01_actions_20261021.json").write_text(
            json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if FINAL_DIR.exists():
            raise FileExistsError(f"Refusing to overwrite existing package: {FINAL_DIR}")
        stage.rename(FINAL_DIR)
        after_old = sorted(
            path
            for path in DATASET_ROOT.rglob("*.mp4")
            if path.is_file() and not path.is_relative_to(FINAL_DIR)
        )
        if len(after_old) != len(old_files) or [p.relative_to(DATASET_ROOT) for p in after_old] != [
            p.relative_to(DATASET_ROOT) for p in old_files
        ]:
            raise RuntimeError("Existing material MP4 file list changed during export")
        print(f"Package: {FINAL_DIR}", flush=True)
        print(f"Manifest: {FINAL_DIR / manifest.name}", flush=True)
        print(f"Existing material clips preserved: {len(after_old)}", flush=True)
    except Exception:
        print(f"Export failed; diagnostic staging files remain at: {stage}", flush=True)
        raise


if __name__ == "__main__":
    main()
