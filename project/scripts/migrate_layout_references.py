"""One-shot mechanical reference migration to the four-module layout."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
root_expr = 'next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())'

def update_python(path):
    text = path.read_text(encoding='utf-8-sig')
    original = text
    # Only relocated entrypoints/tests; model modules intentionally use vision as root.
    if any(path.is_relative_to(ROOT / p) for p in
           ('vision/scripts', 'vision/webapp', 'vision/tests/integration', 'vision/tools/clipping', 'project/scripts/r3')):
        text = re.sub(r'(ROOT|REPO) = Path\(__file__\)\.resolve\(\)\.parents\[\d+\]',
                      lambda m: m[1] + ' = ' + root_expr, text)
        for name in ('src', 'models', 'data', 'scripts', 'video', 'webapp', 'tools'):
            text = re.sub(r'\b(ROOT|REPO) / ([\"\'])' + name + r'(?=[/\"\'])',
                          lambda m: m[1] + ' / ' + m[2] + 'vision/' + name, text)
        text = re.sub(r'\b(ROOT|REPO) / ([\"\'])analysis/r3', r'\1 / \2project/analysis/r3', text)
        text = re.sub(r'\b(ROOT|REPO) / ([\"\'])analysis', r'\1 / \2vision/analysis', text)
        # Chained R3 report paths need the hardware module rather than vision.
        if path.is_relative_to(ROOT / 'project/scripts/r3'):
            text = text.replace('ROOT / "vision/analysis" / "r3"', 'ROOT / "project/analysis" / "r3"')
        text = text.replace('from webapp.', 'from vision.webapp.').replace('import webapp.', 'import vision.webapp.')
        text = text.replace('"webapp.', '"vision.webapp.').replace("'webapp.", "'vision.webapp.")
    if any(path.is_relative_to(ROOT / p) for p in ('ASR', 'vision/scripts', 'project/scripts/r3', 'vision/webapp')):
        text = re.sub(r'\b(ROOT|REPO) / ([\"\'])_tmp', r'\1 / \2project/_tmp', text)
        text = text.replace("ROOT / 'pynq-vision'", "ROOT / 'project'")
        text = re.sub(r'ROOT / ([\"\'])asr(?=[/\"\'])', r'ROOT / \1ASR', text)
    if path.name == 'rebuild_full_frame_dataset.py':
        text = text.replace('Path("data/exports/', 'Path("vision/data/exports/')
        text = text.replace('if [part.casefold() for part in parts[:3]]',
            'if [part.casefold() for part in parts[:4]] == ["vision", "data", "legacy", "material"]:\n'
            '        parts = parts[4:]\n    elif [part.casefold() for part in parts[:3]]')
    if path.name == 'build_manifest.py' and path.parent.name == 'm1':
        text = text.replace('"video/done', '"vision/video/done')
    if path.name == 'build_m1_manifest.py':
        text = text.replace('"video/', '"vision/video/')
    if text != original:
        path.write_text(text, encoding='utf-8', newline='')

for folder in ('ASR', 'vision', 'project/scripts/r3'):
    for path in (ROOT / folder).rglob('*.py'):
        if '__pycache__' not in path.parts:
            update_python(path)

path = ROOT / '.gitignore'
text = path.read_text(encoding='utf-8')
text = text.replace('pynq-vision/', 'project/').replace('tools/portable/', 'vision/tools/portable/')
text = re.sub(r'^video/', 'vision/video/', text, flags=re.M)
text = re.sub(r'^_tmp/', 'project/_tmp/', text, flags=re.M)
text += '\n# Local caches and migration evidence\nproject/_cache/\n'
path.write_text(text, encoding='utf-8')

# Only active project configuration/scripts, never generated build evidence.
for path in (ROOT / 'project/fpga').rglob('*'):
    if not path.is_file() or path.suffix.lower() not in ('.xpr', '.tcl', '.bat', '.bd', '.xci'):
        continue
    if any(p.endswith(('.runs', '.cache', '.gen', '.ip_user_files')) for p in path.parts):
        continue
    text = path.read_text(encoding='utf-8-sig')
    changed = text.replace('Sign-Language-Vision-Recognition/pynq-vision/',
                           'Sign-Language-Vision-Recognition/project/')
    changed = changed.replace('Sign-Language-Vision-Recognition\\pynq-vision\\',
                              'Sign-Language-Vision-Recognition\\project\\')
    changed = changed.replace('cd /d F:\\PLD\\pld-sign-glove\\fpga\\scripts', 'cd /d "%~dp0"')
    if changed != text:
        path.write_text(changed, encoding='utf-8', newline='')
print('Active code/config references migrated')
