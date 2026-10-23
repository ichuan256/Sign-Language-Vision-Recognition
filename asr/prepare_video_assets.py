"""Offline, resumable source inventory and timestamped teaching-audio transcript.

Only stable published source files are inventoried. Does not modify the live lexicon.
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np

from audio_loop import create_recognizer


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def inventory(video_root, output):
    listed = json.loads((video_root / "sources.json").read_text(encoding="utf-8"))
    files = [(video_root / s["file"], s) for s in listed]
    for directory in sorted(video_root.glob("BV*")):
        if directory.is_dir():
            for path in sorted(directory.rglob("*.mp4")):
                metadata = path.with_suffix(".info.json")
                info = json.loads(metadata.read_text(encoding="utf-8")) if metadata.exists() else {}
                files.append((path, {"title": info.get("title", path.stem)}))
    entries, hashes = [], set()
    for path, metadata in files:
        sha = digest(path)
        if metadata.get("sha256") and metadata["sha256"] != sha:
            raise ValueError("source hash changed: " + str(path))
        if sha in hashes:
            continue
        hashes.add(sha)
        entries.append({"id": path.stem, "file": str(path.resolve()),
                        "title": metadata["title"], "sha256": sha, "bytes": path.stat().st_size})
    save(output / "inventory.json", {"sources": entries,
         "scope": "sources.json plus complete mp4 files in BV-named subdirectories; clips/caches excluded",
         "empty_course_directories": [str(p) for p in video_root.glob("BV*")
                                      if p.is_dir() and not list(p.rglob("*.mp4"))]})
    return entries


def transcribe(source, recognizer):
    path = Path(source["file"])
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(path),
                          "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "pipe:1"],
                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    audio = np.frombuffer(raw, "<i2").astype(np.float32) / 32768
    segments = []
    stream = recognizer.create_stream()
    origin = 0.0
    started = time.perf_counter()

    def emit(endpoint):
        result = recognizer.get_result_all(stream)
        if result.text.strip():
            times = [round(origin + float(t), 3) for t in result.timestamps]
            segments.append({"text": result.text.strip(), "tokens": list(result.tokens),
                             "token_times_s": times, "start_s": times[0] if times else origin,
                             "last_token_s": times[-1] if times else endpoint,
                             "endpoint_s": round(endpoint, 3)})

    for pos in range(0, len(audio), 1600):
        block = audio[pos:pos + 1600]
        stream.accept_waveform(16000, block)
        while recognizer.is_ready(stream):
            recognizer.decode_stream(stream)
        if recognizer.is_endpoint(stream):
            endpoint = (pos + len(block)) / 16000
            emit(endpoint)
            stream = recognizer.create_stream()
            origin = endpoint
    stream.accept_waveform(16000, np.zeros(16000, np.float32))
    stream.input_finished()
    while recognizer.is_ready(stream):
        recognizer.decode_stream(stream)
    emit(len(audio) / 16000)
    if digest(path) != source["sha256"]:
        raise ValueError("source changed while processing")
    return {"source": source, "duration_s": len(audio) / 16000,
            "annotation_status": "automatic_teaching_speech_not_sign_boundary_annotation",
            "elapsed_s": round(time.perf_counter() - started, 2), "segments": segments}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-root", type=Path, default=Path("video"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sources = inventory(args.video_root, args.output)
    recognizer = None
    for index, source in enumerate(sources, 1):
        output = args.output / (source["id"] + ".asr.json")
        if output.exists():
            old = json.loads(output.read_text(encoding="utf-8"))
            if old["source"]["sha256"] == source["sha256"]:
                print(f"SKIP {index}/{len(sources)} {source['id']}", flush=True)
                continue
            raise ValueError("existing transcript belongs to changed source")
        if recognizer is None:
            recognizer = create_recognizer(args.model)
        result = transcribe(source, recognizer)
        save(output, result)
        print(f"DONE {index}/{len(sources)} {source['id']} audio={result['duration_s']:.1f}s "
              f"segments={len(result['segments'])} compute={result['elapsed_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
