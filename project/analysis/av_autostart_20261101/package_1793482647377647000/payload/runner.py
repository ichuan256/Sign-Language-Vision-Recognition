"""Load only the fixed root-owned audio service, ignoring user Python paths."""
import os,runpy,sys
from pathlib import Path
ROOT=Path('/usr/local/lib/sign-av/runtime')
if len(sys.argv)<2 or sys.argv[1]!='board_audio_stream.py':raise SystemExit('Unsupported program')
sys.path.insert(0,str(ROOT));os.chdir(ROOT)
sys.argv=[str(ROOT/sys.argv[1]),*sys.argv[2:]]
runpy.run_path(sys.argv[0],run_name='__main__')
