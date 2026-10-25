"""Check that every staged deletion is represented at its relocated path."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
mapping = [('analysis/r3/', 'project/analysis/r3/'), ('scripts/r3/', 'project/scripts/r3/'),
           ('pynq-vision/', 'project/'), ('asr/', 'ASR/'),
           *[(p+'/', 'vision/'+p+'/') for p in ('analysis','scripts','src','data','tools','models','webapp','video')],
           ('tests/', 'vision/tests/integration/')]

def main():
    deleted = subprocess.check_output(['git','diff','--cached','--diff-filter=D','--name-only','-z'],cwd=ROOT).decode().split('\0')
    indexed = set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
    missing = []
    for old in filter(None, deleted):
        new = next((b+old[len(a):] for a,b in mapping if old.startswith(a)), None)
        if new not in indexed:
            missing.append((old,new, bool(new and (ROOT/new).exists())))
    print('Unmatched staged deletions:', len(missing))
    for row in missing:
        print(row)
    return missing

if __name__ == '__main__':
    main()
