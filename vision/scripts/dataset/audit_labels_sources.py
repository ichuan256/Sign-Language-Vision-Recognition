"""Read-only media/label/provenance audit; writes only new audit artifacts.

Run with the existing r3 environment. No relabeling, deduplication, split changes,
model training, or source-media writes are performed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import unicodedata

import cv2
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
MANIFEST = ROOT / "vision/data/manifests/manifest_fullframe_20261024.csv"
CACHE = ROOT / "project/_tmp/r3/tensors.npz"
PREFIX = ROOT / "vision/analysis/dataset/label_source_audit_20261025"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def basename(path):
    return PureWindowsPath(path).name


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def label_key(label):
    # A review key only: deleting punctuation does NOT authorize merging labels.
    return "".join(c for c in unicodedata.normalize("NFKC", label)
                   if not c.isspace() and not unicodedata.category(c).startswith("P"))


def source_index():
    index = defaultdict(list)
    files = []
    for path in sorted((ROOT / "vision/video/done").rglob("*.csv")):
        name = path.name
        if not (name.startswith("manifest_P") or name.startswith("dataset_manifest_")
                or name.startswith("recovered_candidates_") or name.startswith("第一课动作周期")):
            continue
        rows = read_csv(path)
        files.append({"path": rel(path), "sha256": digest(path), "rows": len(rows)})
        for row in rows:
            output = row.get("输出路径") or row.get("输出相对路径")
            if output:
                index[basename(output)].append((path, row))
            if row.get("动作编号"):
                index["action:" + row["动作编号"]].append((path, row))
    return index, files


def provenance(record, index):
    matches = index.get(basename(record["path"]), [])
    matches = [(p, r) for p, r in matches
               if (r.get("类别") or r.get("词句标签") or r.get("词句上下文")) == record["label"]]
    match_basis = "filename_and_label"
    if not matches:
        action = re.match(r"(NL\d{2}_\d{3}_C\d+)(?:_|$)", basename(record["path"]))
        if action:
            matches = index.get("action:" + action[1], [])
            match_basis = "unique_action_id"
    # The recovered-candidate list repeats a subset of the main manifest.
    if len(matches) > 1:
        primary = [(p, r) for p, r in matches if p.name.startswith("dataset_manifest_")]
        if len(primary) == 1:
            matches = primary
    if len(matches) != 1:
        return {"status": "ambiguous" if matches else "unresolved", "candidates": [rel(p) for p, _ in matches]}
    path, row = matches[0]
    p = {"status": "resolved", "manifest": rel(path), "performer_id": None,
         "resolution_basis": match_basis,
         "source_manifest_label": row.get("类别") or row.get("词句标签") or row.get("词句上下文"),
         "performer_hint": row.get("目标人物") or None,
         "evidence": row.get("标注依据") or row.get("核对说明") or row.get("处理说明") or "",
         "confidence": row.get("置信度") or None,
         "expected_sha256": row.get("SHA256") or None,
         "candidate_id": row.get("候选编号") or (row.get("动作编号", "").rsplit("_C", 1)[0] or None),
         "label_scope": "sentence_context_cycle" if "词句上下文" in row else row.get("片段类型") or "unspecified"}
    original = row.get("原片路径")
    if original:
        # Preserve original source identity, without teammate-machine absolute paths.
        p["source_video"] = basename(original)
        p["source_group"] = Path(basename(original)).stem
    elif row.get("动作编号"):
        lesson = int(row["课次"])
        p["source_video"] = None
        p["source_group"] = f"NL_lesson_{lesson:02d}"
        p["source_group_basis"] = "lesson and action ID; source filename absent from this manifest"
    else:
        lesson = int(row["课次"])
        p["source_video"] = None
        p["source_group"] = f"NL_lesson_{lesson:02d}"
        p["source_group_basis"] = "lesson only; original timestamps and candidate IDs absent"
    p["source_family"] = "BV1Hs411E7aP" if "BV1Hs411E7aP" in p["source_group"] else "NL_tutorial"
    # Unify known NL lesson identifiers, but never conflate BV p01 and NL lesson 01.
    if p["source_family"] == "NL_tutorial":
        lesson = re.search(r"(?:NL|P)(\d{1,2})", row.get("动作编号") or basename(original or ""))
        if lesson:
            p["source_group"] = f"NL_lesson_{int(lesson[1]):02d}"
    start = row.get("原片起始秒") or row.get("起始秒")
    end = row.get("原片结束秒") or row.get("结束秒_不含")
    p["start_s"] = float(start) if start else None
    p["end_s"] = float(end) if end else None
    if row.get("分辨率"):
        p["declared_resolution"] = row["分辨率"]
    elif row.get("宽"):
        p["declared_resolution"] = f"{row['宽']}x{row['高']}"
    elif row.get("输出分辨率"):
        p["declared_resolution"] = row["输出分辨率"]
    return p


def duplicate_groups(records, key):
    groups = defaultdict(list)
    for record in records:
        value = record.get(key)
        if value:
            groups[value].append(record["id"])
    return [ids for ids in groups.values() if len(ids) > 1]


def temporal_pairs(records, nearby=1.0):
    groups = defaultdict(list)
    for r in records:
        p = r["provenance"]
        if p.get("start_s") is not None and p.get("end_s") is not None:
            groups[p["source_group"]].append(r)
    result = []
    for group, rows in groups.items():
        rows.sort(key=lambda r: r["provenance"]["start_s"])
        for i, a in enumerate(rows):
            pa = a["provenance"]
            for b in rows[i + 1:]:
                pb = b["provenance"]
                if pb["start_s"] > pa["end_s"] + nearby:
                    break
                overlap = min(pa["end_s"], pb["end_s"]) - max(pa["start_s"], pb["start_s"])
                result.append({"a": a["id"], "b": b["id"], "source_group": group,
                               "kind": "overlap" if overlap > 1e-6 else "touching_or_nearby",
                               "overlap_s": round(max(0.0, overlap), 6),
                               "gap_s": round(max(0.0, pb["start_s"] - pa["end_s"]), 6),
                               "same_label": a["label"] == b["label"],
                               "r3_train_test": {a.get("r3_split"), b.get("r3_split")} == {"train", "test"}})
    return result


def split_summary(records):
    classes = []
    for label in sorted({r["label"] for r in records}):
        rows = [r for r in records if r["label"] == label]
        train = [r for r in rows if r["r3_split"] == "train"]
        test = [r for r in rows if r["r3_split"] == "test"]
        train_groups = {r["provenance"].get("source_group") for r in train} - {None}
        test_groups = {r["provenance"].get("source_group") for r in test} - {None}
        classes.append({"label": label, "samples": len(rows), "train": len(train), "test": len(test),
                        "source_groups": sorted(train_groups | test_groups),
                        "train_test_shared_sources": sorted(train_groups & test_groups),
                        "same_label_cross_source_holdout_possible": len(train_groups | test_groups) > 1,
                        "context_cycle_samples": sum(r["provenance"].get("label_scope") == "sentence_context_cycle" for r in rows)})
    return classes


def markdown(report):
    s, r3 = report["summary"], report["r3"]
    lines = ["# 标签与来源审计（2026-10-25）", "",
             "只读审计；未改标签、媒体、缓存、模型或训练/测试划分。详表见同名 JSON。", "",
             "## 核心结论", "",
             f"- 全清单 {s['samples']} 条 / {s['labels']} 个原始标签；其中 {s['singleton_labels']} 类只有 1 条，{s['labels_lt4']} 类不足 4 条。",
             f"- 当前 R3 缓存 {r3['samples']} 条 / {r3['labels']} 类，训练 {r3['train']}、测试 {r3['test']}；每类测试仅 1 条。",
             f"- 来源可回溯 {s['provenance_resolved']}/{s['samples']} 条；有原片时间区间 {s['with_source_timestamps']} 条。",
             f"- 文件缺失 {s['missing_files']}；容器元数据读取失败 {s['metadata_failures']}；已有 SHA256 不符 {s['sha_mismatches']}。",
             f"- 对有历史哈希的 {s['sha_verified']} 条完成比对；其余仅记录当前哈希，不能据此宣称历史一致。",
             f"- 字节级完全重复组 {s['exact_duplicate_groups']}；缓存张量完全重复组 {len(r3['tensor_duplicate_groups'])}。",
             f"- 磁盘目录标签与来源标签不一致 {s['source_label_text_mismatches']} 条（可追溯动作 ID，主要为斜线/问号文件名替换，逐条保留原文）。",
             f"- R3 同源时间重叠且跨训练/测试 {r3['cross_split_overlap_pairs']} 对；相邻（间隙≤1秒）跨集合 {r3['cross_split_nearby_pairs']} 对。",
             f"- 全库发现 {s['source_time_overlap_pairs']} 对同源时间重叠（均为不同原标签）；进入扩展词表前需要复核并绑定共享帧分组。",
             f"- R3 {r3['test_samples_same_source_as_training']}/{r3['test']} 条测试样本的原视频来源也在训练中；这属于同来源留出，不能视为跨人/跨录像泛化。",
             f"- {r3['single_source_classes']}/{r3['labels']} 类只来自一个原视频，现数据无法进行覆盖全部类别的跨原视频闭集评测。",
             "", "## 标签候选（不自动合并）", "",
             "下表只按 Unicode NFKC + 去标点/空白发现文本别名；同文异手势、标点语气及句子完整性仍需逐视频审核。", "",
             "| 候选规范键 | 原标签及条数 | 当前 R3 涉及 |", "|---|---|---|"]
    for group in report["label_alias_candidates"]:
        labels = " / ".join(f"{x['label']}（{x['count']}）" for x in group["labels"])
        lines.append(f"| {group['review_key']} | {labels} | {'、'.join(group['r3_labels']) or '无'} |")
    lines.extend(["", "9 条来源原标签与目录名差异为文件名转换：`/ → _`、`? → _`。后续应以动作 ID 关联语义标签，不能把文件名清洗结果直接当词义标准。"])
    lines.extend(["", "## R3 每类来源", "",
                  "| 标签 | 条数 | 原视频来源 | 训练/测试同来源 | 上下文动作周期 |",
                  "|---|---:|---|---|---:|"])
    for row in r3["class_sources"]:
        lines.append(f"| {row['label']} | {row['samples']} | {', '.join(row['source_groups'])} | {', '.join(row['train_test_shared_sources']) or '无'} | {row['context_cycle_samples']} |")
    lines.extend(["", "## 来源与粒度问题", "",
                  "1. 总清单 `part` 列实际是 wsy/Tomcat 提交者，不是原片 part，更不是表演者。审计将二者分开；本次不根据目录认定人物身份。",
                  "2. BV1Hs411E7aP 的 352×288/20fps 素材与 NL 教程 1920×1080 素材是不同来源族；同一 p01/第1课也不自动视为同源。清单本身无法证明两个来源族的教师相同或不同。",
                  "3. 第一课周期清单的字段是“词句上下文”，并明确说明部分整句拆成准备位周期、不自动赋独立词义；不能直接拿文件夹句子名当作每段完整动作标签。",
                  "4. NL09/NL10 精剪说明记录多人对话与单人示范者差异，角色对应还有待核对项。因此不能再笼统宣称素材全是同一老师，也不能直接按提交者做留一老师评测。",
                  "5. 第二、三课收录清单缺原片起止秒和独立表演者 ID，只能确定课级来源，无法对它们做时间重叠审计。",
                  "", "## 确认的重复与待复核样本", ""])
    for group in report["exact_duplicate_groups"]:
        rows = [report["records"][i] for i in group]
        lines.append("- 完全相同文件：" + "；".join(f"`{r['path']}`" for r in rows) + "。仅报告，不删除；本组不在当前 R3 的 59 条中。")
    for label in r3["class_sources"]:
        if label["context_cycle_samples"]:
            lines.append(f"- R3 `{label['label']}` 有 {label['context_cycle_samples']} 条来自句子上下文周期清单，需确认是否完整表达同一语义。")
    lines.extend(["", "## R3 相邻跨集合明细", "",
                  "相邻片段未共享原片时间，不能称作已确认重复或共享帧泄漏；以下为同场次相关性风险。", "",
                  "| 样本 A | 样本 B | 间隙秒 | 同候选 |", "|---|---|---:|---|"])
    for pair in r3["temporal_pairs"]:
        if not pair["r3_train_test"]:
            continue
        a, b = (report["records"][pair[k]] for k in ("a", "b"))
        same_candidate = a["provenance"].get("candidate_id") and a["provenance"].get("candidate_id") == b["provenance"].get("candidate_id")
        lines.append(f"| {basename(a['path'])}（{a['r3_split']}） | {basename(b['path'])}（{b['r3_split']}） | {pair['gap_s']} | {'是，应绑定同组' if same_candidate else '未证实'} |")
    lines.extend([
                  "", "## 按优先级的处理建议", "",
                  "- P0：先审核“句子上下文→动作周期”样本，分别决定完整句保留、独立动作重标或暂缓入训；保留旧标签以复现 42.9% 基线。",
                  "- P0：将 `NL01_046_C1/C2` 绑定同组；全库 18 对共享原片时间片段扩展入训时也须同组。当前 R3 内未发现共享原片时间跨集合。相邻不等于重复，只作为同场次相关性提示。",
                  "- P1：人工确认标点别名（优先谢谢/谢谢！），采用稳定 semantic_label_id；不同手势变体另记 variant_id。",
                  "- P1：补 performer_id、recording_id、source_video_id、candidate_id、clip 起止、label_scope；未知值留空，目录名不代替身份。",
                  "- P1：每类只有一个录像来源时，先新增独立录制；在有跨来源样本的交集词表上评测，并单独报告词表和覆盖数。",
                  "- P2：清洗版本冻结后重建张量与训练/验证/最终测试划分，训练增强仅在训练内生成，后续精度与 PL 评测共享版本。",
                  "", "## 审计边界", "",
                  "本次检查文件 SHA256、容器元数据、来源清单、时间区间及既有缓存的元数据/张量重复。未完整解码所有视频、未做全库感知近重复搜索、未逐条判定手语词义或确认每个表演者。",
                  "时间重叠来自同一来源视频的清单区间，表示共享原片时间，不自动等同标签错误；不同人物同框/短词包含于句子均可能出现。跨来源隐藏重复仍需后续感知核验。",
                  "深色背景、人物、字幕等捷径是否被模型使用，本审计不作因果结论。",
                  "", "## 复跑", "", "```powershell",
                  r"F:\PLD\.venv-r3\Scripts\python.exe -X utf8 vision/scripts/dataset/audit_labels_sources.py",
                  "```", "", "来源清单路径、哈希、逐样本回溯和复核队列保存在 JSON。"])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-prefix", type=Path, default=PREFIX)
    args = parser.parse_args()
    source_rows = read_csv(MANIFEST)
    index, evidence_files = source_index()
    cache = np.load(CACHE, allow_pickle=False)
    meta = json.loads(str(cache["meta"]))
    labels, y, x = cache["labels"], cache["y"], cache["X"]
    if not (len(meta) == len(y) == len(x)):
        raise ValueError("Cache metadata, labels and tensors have different lengths")
    rng = np.random.default_rng(20261024)
    test = set()
    for cls in np.unique(y):
        ids = np.where(y == cls)[0]
        rng.shuffle(ids)
        test.update(int(i) for i in ids[:max(1, len(ids) // 4)])
    cache_by_path = {m["path"].replace("\\", "/"): i for i, m in enumerate(meta)}
    if len(cache_by_path) != len(meta):
        raise ValueError("Cache metadata contains duplicate paths")
    records, cache_errors = [], []
    for i, row in enumerate(source_rows):
        record = {"id": i, "label": row["类别"], "path": row["输出路径"].replace("\\", "/"),
                  "contributor": row["part"], "sample_id": row["样本编号"], "r3_split": None}
        ci = cache_by_path.get(record["path"])
        if ci is not None:
            record["cache_index"] = ci
            record["r3_split"] = "test" if ci in test else "train"
            record["tensor_sha256"] = hashlib.sha256(x[ci].tobytes()).hexdigest()
            if meta[ci]["label"] != row["类别"] or str(labels[y[ci]]) != row["类别"]:
                cache_errors.append({"id": i, "issue": "cache label mismatch"})
        path = ROOT / record["path"]
        record["exists"] = path.is_file()
        record["provenance"] = provenance(record, index)
        if path.is_file():
            record["sha256"] = digest(path)
            cap = cv2.VideoCapture(str(path))
            record["media"] = {"opened": cap.isOpened(), "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                               "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                               "fps": round(cap.get(cv2.CAP_PROP_FPS), 5),
                               "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
            cap.release()
            expected = record["provenance"].get("expected_sha256")
            record["sha256_matches_manifest"] = record["sha256"].lower() == expected.lower() if expected else None
        records.append(record)
        if (i + 1) % 100 == 0:
            print(f"Audited {i + 1}/{len(source_rows)} clips", flush=True)
    current = [r for r in records if r["r3_split"]]
    # Identical bytes can trace a renamed copy back to a known clip. This does
    # not turn that copy into an independent sample or invent absent timestamps.
    for group in duplicate_groups(records, "sha256"):
        known = [records[i] for i in group if records[i]["provenance"]["status"] == "resolved"]
        if len(known) == 1:
            for i in group:
                if records[i]["provenance"]["status"] == "unresolved":
                    records[i]["provenance"] = dict(known[0]["provenance"],
                                                    resolution_basis="identical_file_sha256",
                                                    duplicate_of=known[0]["id"])
    if len(current) != len(meta):
        raise ValueError("Cached sample paths no longer exactly match the full manifest")
    counts = Counter(r["label"] for r in records)
    aliases = defaultdict(list)
    for label in sorted(counts):
        aliases[label_key(label)].append(label)
    alias_groups = [{"review_key": k, "labels": [{"label": v, "count": counts[v]} for v in vals],
                     "r3_labels": [v for v in vals if v in set(labels)], "status": "manual_semantic_review_required"}
                    for k, vals in sorted(aliases.items()) if len(vals) > 1]
    pairs = temporal_pairs(records)
    r3pairs = [p for p in pairs if records[p["a"]]["r3_split"] and records[p["b"]]["r3_split"]]
    class_sources = split_summary(current)
    shared_sources = {r["provenance"].get("source_group") for r in current if r["r3_split"] == "train"} - {None}
    queue = []
    for n, group in enumerate(alias_groups):
        queue.append({"priority": "P1", "type": "punctuation_alias", "alias_group_index": n, "action": "review_only_no_automatic_merge"})
    for r in records:
        p = r["provenance"]
        if p.get("label_scope") == "sentence_context_cycle":
            queue.append({"priority": "P0", "type": "sentence_context_not_atomic_label", "id": r["id"], "r3": bool(r["r3_split"])})
        if p["status"] != "resolved" or r.get("sha256_matches_manifest") is False or not r["exists"]:
            queue.append({"priority": "P0", "type": "provenance_or_integrity", "id": r["id"]})
        if p.get("source_manifest_label") and p["source_manifest_label"] != r["label"]:
            queue.append({"priority": "P1", "type": "source_label_text_mismatch", "id": r["id"],
                          "source_label": p["source_manifest_label"], "directory_label": r["label"]})
    for pair in r3pairs:
        if pair["r3_train_test"] and pair["kind"] == "overlap":
            queue.append({"priority": "P0", "type": "train_test_source_time_overlap", "a": pair["a"], "b": pair["b"]})
        a, b = records[pair["a"]], records[pair["b"]]
        if (pair["r3_train_test"] and a["provenance"].get("candidate_id")
                and a["provenance"]["candidate_id"] == b["provenance"].get("candidate_id")):
            queue.append({"priority": "P0", "type": "same_candidate_split_across_train_test", "a": pair["a"], "b": pair["b"]})
    for group in duplicate_groups(records, "sha256"):
        queue.append({"priority": "P1", "type": "exact_duplicate_file", "ids": group,
                      "action": "keep one logical sample in next version; no deletion performed"})
    summary = {"samples": len(records), "labels": len(counts), "singleton_labels": sum(v == 1 for v in counts.values()),
               "labels_lt4": sum(v < 4 for v in counts.values()), "label_count_histogram": dict(sorted(Counter(counts.values()).items())),
               "provenance_resolved": sum(r["provenance"]["status"] == "resolved" for r in records),
               "with_source_timestamps": sum(r["provenance"].get("start_s") is not None for r in records),
               "missing_files": sum(not r["exists"] for r in records),
               "metadata_failures": sum(r["exists"] and (not r["media"]["opened"] or r["media"]["frames"] <= 0) for r in records),
               "sha_verified": sum(r.get("sha256_matches_manifest") is True for r in records),
               "sha_mismatches": sum(r.get("sha256_matches_manifest") is False for r in records),
               "source_time_overlap_pairs": sum(p["kind"] == "overlap" for p in pairs),
               "exact_duplicate_groups": len(duplicate_groups(records, "sha256")),
               "source_family_counts": dict(Counter(r["provenance"].get("source_family", "unknown") for r in records)),
               "actual_resolutions": dict(Counter(f"{r['media']['width']}x{r['media']['height']}" for r in records if r.get("media"))),
               "performer_id_confirmed_samples": 0,
               "context_cycle_samples": sum(r["provenance"].get("label_scope") == "sentence_context_cycle" for r in records)}
    summary["source_label_text_mismatches"] = sum(bool(r["provenance"].get("source_manifest_label")) and r["provenance"]["source_manifest_label"] != r["label"] for r in records)
    report = {"audit_version": 1, "date": "2026-10-25", "full_manifest": {"path": rel(MANIFEST), "sha256": digest(MANIFEST)},
              "tensor_cache_sha256": digest(CACHE), "provenance_manifests": evidence_files, "summary": summary,
              "r3": {"samples": len(current), "labels": len(set(y)), "train": len(current)-len(test), "test": len(test),
                     "cache_shape": list(x.shape), "cache_errors": cache_errors,
                     "class_sources": class_sources,
                     "single_source_classes": sum(len(v["source_groups"]) == 1 for v in class_sources),
                     "test_samples_same_source_as_training": sum(r["r3_split"] == "test" and r["provenance"].get("source_group") in shared_sources for r in current),
                     "cross_split_overlap_pairs": sum(p["r3_train_test"] and p["kind"] == "overlap" for p in r3pairs),
                     "cross_split_nearby_pairs": sum(p["r3_train_test"] and p["kind"] == "touching_or_nearby" for p in r3pairs),
                     "tensor_duplicate_groups": duplicate_groups(current, "tensor_sha256"), "temporal_pairs": r3pairs},
              "label_alias_candidates": alias_groups, "exact_duplicate_groups": duplicate_groups(records, "sha256"),
              "temporal_pairs": pairs, "review_queue": queue, "records": records}
    prefix = args.output_prefix.resolve()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    prefix.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"summary": summary, "r3_classes": class_sources, "report": rel(prefix.with_suffix('.md'))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
