# -*- coding: utf-8 -*-
"""按已审定边界表精剪 P8-P10 并逐条核验。

输入：_inspect_frames/P08/boundary_reviewed_all.csv（人工目检审定）
输出：material_candidates_P08-P10_20261022/<词句标签>/<动作编号>_<标签>.mp4
规格：1920x1080 全画幅、24 fps、H.264/yuv420p、无音轨（策略表建议规格）
核验：分辨率 / 帧率 / 无音轨 / 时长 / 完整解码，写入 manifest + validation JSON。
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
RAW_DIR = (ROOT / "vision/video/raw" / "手语配套视频 《中国手语教程》（初级）倪兰"
           / "手语配套视频 《中国手语教程》（初级）倪兰")
LESSON_PREFIX = {"8": "P8-", "9": "P9-", "10": "P10-"}
OUT_ROOT = ROOT / "data" / "exports" / "material_candidates_P08-P10_20261022"
INVALID = str.maketrans({'/': '_', '\\': '_', ':': '_', '*': '_', '?': '_',
                         '"': '_', '<': '_', '>': '_', '|': '_'})


def probe(path: Path):
    out = subprocess.run([str(FFMPEG), "-i", str(path)], capture_output=True,
                         text=True, encoding="utf-8", errors="replace").stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    vid = re.search(r"Video:.*?(\d{3,4})x(\d{3,4}).*?([\d.]+) fps", out)
    return {
        "时长": int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else 0,
        "宽": int(vid.group(1)) if vid else 0,
        "高": int(vid.group(2)) if vid else 0,
        "fps": float(vid.group(3)) if vid else 0,
        "有音轨": "Audio:" in out,
    }


def cut(row, overwrite=False):
    cid = row["动作编号"]
    label = row["词句标签"].translate(INVALID).strip().rstrip(".")
    s, e = float(row["起始秒"]), float(row["结束秒_不含"])
    src = next(RAW_DIR.glob(LESSON_PREFIX[row["课次"]] + "*.mp4"))
    out_dir = OUT_ROOT / label
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{cid}_{label}.mp4"
    if out_path.exists() and not overwrite:
        p = probe(out_path)
        return {**row, "输出路径": str(out_path), "结果": "已存在", **p}
    cmd = [str(FFMPEG), "-y", "-ss", f"{s:.3f}", "-i", str(src),
           "-t", f"{e - s:.3f}", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24", "-an",
           "-movflags", "+faststart", str(out_path)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0 or not out_path.exists():
        return {**row, "输出路径": str(out_path), "结果": "失败", "错误": p.stderr[-200:]}
    info = probe(out_path)
    # 完整解码检查
    d = subprocess.run([str(FFMPEG), "-v", "error", "-i", str(out_path),
                        "-f", "null", "-"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    ok = (info["宽"] == 1920 and info["高"] == 1080 and abs(info["fps"] - 24) < 0.5
          and not info["有音轨"] and abs(info["时长"] - (e - s)) < 0.3 and not d.stderr.strip())
    return {**row, "输出路径": str(out_path),
            "结果": "成功" if ok else "核验异常", **info,
            "解码错误": d.stderr.strip()[:150]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--from", dest="frm", type=int, default=0)
    ap.add_argument("--to", dest="to", type=int, default=10**9)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    with open(args.csv, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))[args.frm:args.to]
    print(f"本批 {len(rows)} 条")
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        results = list(ex.map(lambda r: cut(r, args.overwrite), rows))

    bad = [r for r in results if r["结果"] not in ("成功", "已存在")]
    ok = sum(1 for r in results if r["结果"] in ("成功", "已存在"))
    print(f"成功/已存在 {ok}，异常 {len(bad)}")
    for r in bad:
        print("[异常]", r["动作编号"], r["结果"], r.get("错误", ""),
              f"{r.get('宽')}x{r.get('高')} @{r.get('fps')} 音轨={r.get('有音轨')} "
              f"时长={r.get('时长')} 解码={r.get('解码错误','')}")
    # 汇总写盘（供多批追加合并）
    part = OUT_ROOT / f"manifest_part_{Path(args.csv).stem}_{args.frm:03d}_{args.frm + len(rows):03d}.csv"
    fields = ["动作编号", "候选编号", "课次", "词句标签", "片段类型", "起始秒",
              "结束秒_不含", "输出路径", "结果", "时长", "宽", "高", "fps", "有音轨"]
    with open(part, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(results)
    print(f"清单: {part}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
