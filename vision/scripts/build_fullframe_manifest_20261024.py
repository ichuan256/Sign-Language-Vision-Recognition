# -*- coding: utf-8 -*-
"""w2：从 video/done/ 扫描全画幅精剪片段，生成 signrec 兼容清单。

输出列对齐 signrec.dataset.load_manifest 契约：类别 / 输出路径（仓库相对）/ 样本编号 / part（提交人）。
目录约定：<任意层级>/<词句标签>/<文件>.mp4 —— 标签取直接父目录名。
"""
import csv
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
DONE = ROOT / "vision/video" / "done"
OUT = ROOT / "vision/data" / "manifests" / "manifest_fullframe_20261024.csv"


def main():
    rows = []
    for mp4 in sorted(DONE.rglob("*.mp4")):
        rel = mp4.relative_to(ROOT).as_posix()
        person = mp4.relative_to(DONE).parts[0]  # Tomcat / wsy
        label = mp4.parent.name
        rows.append({
            "类别": label,
            "输出路径": rel,
            "样本编号": mp4.stem,
            "part": person,
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["类别", "输出路径", "样本编号", "part"])
        w.writeheader()
        w.writerows(rows)
    classes = {r["类别"] for r in rows}
    print(f"片段 {len(rows)} 条，类别 {len(classes)} 个，清单 {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
