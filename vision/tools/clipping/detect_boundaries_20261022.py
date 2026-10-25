# -*- coding: utf-8 -*-
"""P8-P10 候选动作边界自动检测 + 核验图生成（逐候选窗口 + 双阈值）。

方法（依据 P8 原片实测能量曲线标定）：
- 静息（准备位）能量 <=0.7；示范中保持/缓动 1.0~2.2；主动作 >=2.5。
- 在候选检索窗 ±MARGIN 内以 12 fps 抽灰度小图算帧间运动能量。
- 高活性核心段（>core_thr，合并 <=0.35s 短间隔）向两端吸收保持帧
  （能量>REST_THR），遇到持续 0.33s 静息截断 -> 完整「起手->示范->回落」段。
- 按画面证据时刻匹配最近示范段；检索窗内多段完整示范各导出一条（C1/C2）。
- 边界 = 段起 - 0.2s / 段止 + 0.2s，并用相邻段夹紧，不跨入相邻动作。
- 每条生成起点/终点邻域核验图（各 5 帧）供人工目检。

用法：python detect_boundaries_20261022.py --lesson 8 --from 0 --to 6
"""
import argparse
import csv
import io
import subprocess
from pathlib import Path



try:
    from .media_paths import add_source_arguments, find_ffmpeg, resolve_source, print_preflight
except ImportError:
    from media_paths import add_source_arguments, find_ffmpeg, resolve_source, print_preflight

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
FFMPEG = None
SOURCE_ROOT = None
STRATEGY_CSV = Path(__file__).resolve().parent / "中国手语教程_10课_逐词句剪裁策略_20261021.csv"

INSPECT = ROOT / "project/_tmp" / "inspect_frames"
LESSON_PREFIX = {8: "P8-", 9: "P9-", 10: "P10-"}

FPS = 12
W, H = 320, 180
MARGIN = 1.0
PAD = 0.2
REST_THR = 1.0      # 静息能量上限（P8 实测静息 0.3~0.7）
CORE_RATIO = 0.30   # 核心阈值 = max(2.5, 窗内峰值 * 本比例)
MERGE_GAP = 0.35    # 核心段合并间隔（秒）
REST_RUN = 6        # 连续静息帧数达到即截断（约 0.5s，覆盖手势静止保持）
MIN_DEMO = 0.4      # 短于该时长的段视为词卡弹入等噪声（秒）
TRANS_AREA = 0.15   # 帧差像素占比超过此值视为转场淡变（实测：手语 <=0.10，淡变 0.19~0.25）
AREA_DIFF = 20      # 判定“变化像素”的灰度差阈值


def load_candidates(lesson):
    rows = []
    with open(STRATEGY_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if int(r["课次"]) != lesson:
                continue
            try:
                r["_start"] = float(r["候选检索起始秒"])
                r["_end"] = float(r["候选检索结束秒"])
                # 部分行为「108 / 112」双证据时刻，取第一个用于段匹配
                r["_evidence"] = float(str(r["画面证据时刻秒"]).split("/")[0].strip())
            except ValueError:
                continue
            rows.append(r)
    return rows


def motion_energy(src, t0, t1):
    """返回 (times, energy, area)：energy=帧差均值，area=变化像素占比。"""
    cmd = [str(FFMPEG), "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(src),
           "-vf", f"fps={FPS},scale={W}:{H},format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (W * H)
    frames = np.frombuffer(raw[: n * W * H], np.uint8).reshape(n, H, W).astype(np.float32)
    if n < 3:
        return np.array([]), np.array([]), np.array([])
    d = np.abs(np.diff(frames, axis=0))
    energy = np.convolve(d.mean(axis=(1, 2)), np.ones(3) / 3, mode="same")
    area = (d > AREA_DIFF).mean(axis=(1, 2))
    times = t0 + (np.arange(len(energy)) + 1) / FPS
    return times, energy, area


def segment_demos(times, energy, area):
    """双阈值分段，返回 [(rise_t, fall_t)]，已去重合并。
    转场帧（整帧淡变）不参与峰值定标，并作为硬边界切断分段。"""
    if len(times) == 0 or energy.max() <= 0:
        return []
    trans = area > TRANS_AREA
    # 硬切/淡变的影响帧向两侧各扩 1 帧（能量中值滤波会把尖峰摊到相邻帧）
    trans = np.convolve(trans.astype(np.int8), [1, 1, 1], mode="same") > 0
    sign_e = energy[~trans]
    local_max = float(sign_e.max()) if len(sign_e) else float(energy.max())
    core_thr = max(2.5, local_max * CORE_RATIO)
    idx = np.where((energy > core_thr) & ~trans)[0]
    if len(idx) == 0:
        return []
    cores, s = [], idx[0]
    for a, b in zip(idx, idx[1:]):
        if (times[b] - times[a]) > MERGE_GAP:
            cores.append([s, a])
            s = b
    cores.append([s, idx[-1]])
    spans = []
    for a, b in cores:
        run, i = 0, a - 1
        while i >= 0 and run < REST_RUN and not trans[i]:
            run = run + 1 if energy[i] <= REST_THR else 0
            i -= 1
        a2 = i + 1 + run
        run, j = 0, b + 1
        while j < len(times) and run < REST_RUN and not trans[j]:
            run = run + 1 if energy[j] <= REST_THR else 0
            j += 1
        b2 = j - 1 - run
        spans.append([a2, b2])
    # 合并扩展后相互重叠的段
    merged = []
    for sp in sorted(spans):
        if merged and sp[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], sp[1])
        else:
            merged.append(sp)
    return [(times[a], times[b]) for a, b in merged
            if times[b] - times[a] >= MIN_DEMO]


def match_demos(demos, cand):
    ev, ws, we = cand["_evidence"], cand["_start"], cand["_end"]
    inside = [d for d in demos if d[0] <= ev <= d[1]]
    if inside:
        return inside[:1]
    # 完整落在本词检索窗内、且段中心位于窗中段的示范段：>=2 段才视为
    # 重复示范（相邻词检索窗虽有重叠，但其示范段中心落在本词窗边缘）
    TOL = 0.3
    mid_lo, mid_hi = ws + 0.25 * (we - ws), we - 0.25 * (we - ws)
    full_mid = [d for d in demos
                if d[0] >= ws - TOL and d[1] <= we + TOL
                and mid_lo <= (d[0] + d[1]) / 2 <= mid_hi]
    if len(full_mid) >= 2:
        return full_mid
    overlap = [d for d in demos if d[1] >= ws and d[0] <= we]
    pool = overlap or list(demos)
    if not pool:
        return []
    return [min(pool, key=lambda d: min(abs(ev - d[0]), abs(ev - d[1])))]


def clamp_bounds(start, end, demos, chosen):
    for d in demos:
        if d == chosen:
            continue
        if d[1] <= chosen[0]:
            start = max(start, d[1] + 0.05)
        elif d[0] >= chosen[1]:
            end = min(end, d[0] - 0.05)
    return max(0.0, start), end


def make_strip(src, name, start, end, out_path):
    cells = []
    for tag, t in (("S", start), ("E", end)):
        for dt in (-0.25, -0.125, 0.0, 0.125, 0.25):
            ts = max(0.0, t + dt)
            cmd = [str(FFMPEG), "-ss", f"{ts:.3f}", "-i", str(src),
                   "-frames:v", "1", "-vf", "scale=560:315",
                   "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
            buf = subprocess.run(cmd, capture_output=True).stdout
            img = Image.open(io.BytesIO(buf)).convert("RGB")
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, 150, 22], fill=(0, 0, 0))
            d.text((4, 4), f"{tag} {ts:.3f}s", fill=(255, 255, 0))
            cells.append(img)
    sheet = Image.new("RGB", (560 * 5, 315 * 2))
    for i, c in enumerate(cells):
        sheet.paste(c, (560 * (i % 5), 315 * (i // 5)))
    sheet.save(out_path, quality=85)


def main():
    global ROOT, FFMPEG, SOURCE_ROOT, INSPECT, Image, ImageDraw, np, STRATEGY_CSV
    ap = argparse.ArgumentParser()
    add_source_arguments(ap)
    ap.add_argument("--lesson", type=int, required=True, choices=[8, 9, 10])
    ap.add_argument("--from", dest="frm", type=int, default=0)
    ap.add_argument("--to", dest="to", type=int, default=10**9)
    args = ap.parse_args()
    ROOT = args.repo_root.resolve()
    SOURCE_ROOT = args.source_root
    FFMPEG = find_ffmpeg(ROOT, args.ffmpeg)
    INSPECT = ROOT / "project/_tmp/inspect_frames"
    STRATEGY_CSV = ROOT / "vision/tools/clipping/中国手语教程_10课_逐词句剪裁策略_20261021.csv"

    src = resolve_source(ROOT, family="NL_tutorial", lesson=args.lesson, source_root=SOURCE_ROOT)
    if args.preflight:
        print_preflight([src], FFMPEG, inspection_root=str(INSPECT))
        return
    from PIL import Image, ImageDraw
    import numpy as np
    cands = load_candidates(args.lesson)[args.frm:args.to]
    out_dir = INSPECT / f"P{args.lesson:02d}"
    strip_dir = out_dir / "strips"
    strip_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"boundary_proposals_{args.frm:03d}_{args.frm + len(cands):03d}.csv"

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["候选编号", "导出头", "词句标签", "片段类型", "检索起始", "检索结束",
                    "建议起始秒", "建议结束秒", "检测状态", "核验图"])
        for r in cands:
            cid = r["候选编号"]
            times, energy, area = motion_energy(src, r["_start"] - MARGIN, r["_end"] + MARGIN)
            demos = segment_demos(times, energy, area)
            chosen_list = match_demos(demos, r)
            if not chosen_list:
                w.writerow([cid, "", r["词句标签"], r["片段类型"], r["_start"], r["_end"],
                            "", "", "检测失败", ""])
                print(f"[失败] {cid}")
                continue
            for k, seg in enumerate(chosen_list, 1):
                s, e = clamp_bounds(seg[0] - PAD, seg[1] + PAD, demos, seg)
                suffix = f"_C{k}" if len(chosen_list) > 1 else ""
                name = f"{cid}{suffix}"
                strip = strip_dir / f"{name}.jpg"
                make_strip(src, name, s, e, strip)
                w.writerow([cid, suffix.lstrip("_") or "C1", r["词句标签"], r["片段类型"],
                            r["_start"], r["_end"], f"{s:.3f}", f"{e:.3f}",
                            "待目检", strip.name])
                print(f"[完成] {name} {r['词句标签']}: {s:.3f} - {e:.3f}")
    print(f"建议表: {csv_path}")


if __name__ == "__main__":
    main()
