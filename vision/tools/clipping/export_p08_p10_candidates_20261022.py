# -*- coding: utf-8 -*-
"""按《中国手语教程_10课_逐词句剪裁策略_20261021.csv》导出第 8/9/10 课候选剪辑。

边界口径（策略表「起点规则 / 终点规则」）：
- 起点 = 候选检索起始秒 - 0.2（保留起手和准备位，不小于 0）
- 终点 = 候选检索结束秒 + 0.2（保留末动作回落，不超过原片时长）
- 精确剪裁起止列在策略表中留空，本脚本产物为「候选剪辑」，未逐帧复核，
  不写入 material_fullframe_20261021 数据集（遵守剪裁方法 README 第 6 条）。

输出规格（策略表「建议输出规格 / 音轨处理 / 画面策略」）：
- 1920x1080 全画幅（不裁剪）、24 fps、H.264/yuv420p、无音轨。

目录结构：material_candidates_P08-P10_20261022/<词句标签>/<候选编号>_<词句标签>.mp4
"""
import argparse
import csv
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = ROOT.parent / "_tools" / "ffmpeg.exe"
STRATEGY_CSV = Path(__file__).resolve().parent / "中国手语教程_10课_逐词句剪裁策略_20261021.csv"
RAW_DIR = (ROOT / "vision/video/raw" / "手语配套视频 《中国手语教程》（初级）倪兰"
           / "手语配套视频 《中国手语教程》（初级）倪兰")
OUT_ROOT = ROOT / "data" / "exports" / "material_candidates_P08-P10_20261022"

LESSON_FILE_PREFIX = {8: "P8-", 9: "P9-", 10: "P10-"}
PAD = 0.2  # 起点/终点规则：前后各留约 0.2 秒

INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize(name: str) -> str:
    return INVALID_CHARS.sub("_", name).strip().rstrip(".")


def load_candidates(lessons):
    rows = []
    with open(STRATEGY_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if int(r["课次"]) not in lessons:
                continue
            try:
                start = float(r["候选检索起始秒"])
                end = float(r["候选检索结束秒"])
            except ValueError:
                print(f"[跳过] {r['候选编号']} 检索窗无法解析: "
                      f"{r['候选检索起始秒']!r}-{r['候选检索结束秒']!r}")
                continue
            if end <= start:
                print(f"[跳过] {r['候选编号']} 检索窗无效: {start}-{end}")
                continue
            rows.append({**r, "_start": start, "_end": end})
    return rows


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        [str(FFMPEG), "-i", str(path)], capture_output=True, text=True,
        encoding="utf-8", errors="replace").stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def cut_one(row, src: Path, src_duration: float, overwrite: bool):
    cid = row["候选编号"]
    label = sanitize(row["词句标签"])
    start = max(0.0, row["_start"] - PAD)
    end = min(src_duration, row["_end"] + PAD)
    dur = round(end - start, 3)
    out_dir = OUT_ROOT / label
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{cid}_{label}.mp4"
    if out_path.exists() and not overwrite:
        return {**_manifest_row(row, start, end, dur, out_path), "结果": "已存在跳过"}
    cmd = [str(FFMPEG), "-y", "-ss", f"{start:.3f}", "-i", str(src),
           "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24", "-an",
           "-movflags", "+faststart", str(out_path)]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0 or not out_path.exists():
        return {**_manifest_row(row, start, end, dur, out_path),
                "结果": "失败", "错误": p.stderr[-300:]}
    return {**_manifest_row(row, start, end, dur, out_path), "结果": "成功"}


def _manifest_row(row, start, end, dur, out_path):
    return {
        "候选编号": row["候选编号"], "课次": row["课次"], "课程": row["课程"],
        "词句标签": row["词句标签"], "片段类型": row["片段类型"],
        "示范信息": row["示范信息"],
        "剪裁起始秒": f"{start:.3f}", "剪裁结束秒": f"{end:.3f}",
        "时长秒": f"{dur:.3f}", "输出路径": str(out_path),
        "边界口径": "候选检索窗±0.2s，未逐帧复核",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", type=int, required=True, choices=[8, 9, 10])
    ap.add_argument("--from", dest="frm", type=int, default=0)
    ap.add_argument("--to", dest="to", type=int, default=10**9)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    src = next(RAW_DIR.glob(LESSON_FILE_PREFIX[args.lesson] + "*.mp4"))
    src_dur = probe_duration(src)
    cands = load_candidates({args.lesson})
    chunk = cands[args.frm:args.to]
    print(f"第{args.lesson}课 原片 {src.name} 时长 {src_dur:.2f}s；"
          f"候选共 {len(cands)} 条，本批 [{args.frm}:{args.to}] = {len(chunk)} 条")

    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        results = list(ex.map(
            lambda r: cut_one(r, src, src_dur, args.overwrite), chunk))

    OUT_ROOT.mkdir(exist_ok=True)
    part = OUT_ROOT / f"manifest_P{args.lesson:02d}_{args.frm:03d}_{args.to:03d}.csv"
    fields = ["候选编号", "课次", "课程", "词句标签", "片段类型", "示范信息",
              "剪裁起始秒", "剪裁结束秒", "时长秒", "输出路径", "边界口径", "结果"]
    with open(part, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    ok = sum(1 for r in results if r["结果"] == "成功")
    skip = sum(1 for r in results if r["结果"] == "已存在跳过")
    fail = [r for r in results if r["结果"] == "失败"]
    print(f"成功 {ok}，跳过 {skip}，失败 {len(fail)}；清单 {part.name}")
    for r in fail:
        print(f"[失败] {r['候选编号']} {r.get('错误','')[:200]}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
