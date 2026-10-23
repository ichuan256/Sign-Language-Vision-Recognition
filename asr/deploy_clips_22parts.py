# deploy_clips_22parts.py - push adapted clips to the board and verify hashes
# Usage: python deploy_clips_22parts.py   (board must be reachable at 192.168.2.99)
import json, subprocess, sys
from pathlib import Path

ROOT = Path(r"F:\PLD\pld-sign-glove")
VIDEO = ROOT / "video"
SD = VIDEO / "phrases_sd.json"
BOARD = "xilinx@192.168.2.99"
BOARD_ROOT = "/home/xilinx/video"

def main():
    data = json.loads(SD.read_text(encoding="utf-8"))
    files = [c["file"] for c in data["clips"] if c["file"].startswith("clips_22parts/")]
    print("clips to deploy:", len(files))
    # ensure dirs exist on board
    dirs = sorted({str(Path(f).parent).replace("\\", "/") for f in files})
    for d in dirs:
        subprocess.run(["ssh", BOARD, "mkdir", "-p", "%s/%s" % (BOARD_ROOT, d)],
                       check=True, timeout=20)
    # scp per phrase folder (batch by folder to keep call count low)
    for d in dirs:
        local_dir = VIDEO / d
        files_here = [str(p) for p in local_dir.glob("*.mp4")]
        subprocess.run(["scp", *files_here, "%s:%s/%s/" % (BOARD, BOARD_ROOT, d)],
                       check=True, timeout=300)
        print("deployed", d, len(files_here), "files")
    # verify sha256 on board against manifest
    entries = {c["file"]: c["sha256"] for c in data["clips"]}
    remote = subprocess.run(["ssh", BOARD,
                             "cd %s && sha256sum clips/*.mp4 clips_22parts/*/*.mp4" % BOARD_ROOT],
                            capture_output=True, text=True, timeout=120)
    remote_map = {}
    for line in remote.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            remote_map[parts[1]] = parts[0]
    bad = 0
    for rel, sha in entries.items():
        got = remote_map.get(rel)
        if got != sha:
            print("MISMATCH", rel, got); bad += 1
    print("board verification: %d/%d ok" % (len(entries) - bad, len(entries)))
    if bad:
        sys.exit(1)

if __name__ == "__main__":
    main()
