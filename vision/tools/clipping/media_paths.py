"""Standard-library-only source/tool discovery shared by clipping scripts."""
from __future__ import annotations
import json
from pathlib import Path, PureWindowsPath
import re
import shutil

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
FAMILIES = ('BV1Hs411E7aP', 'NL_tutorial')
LEGACY_NL = '手语配套视频 《中国手语教程》（初级）倪兰'


def resolve_source(repo_root=REPO_ROOT, *, family, lesson=None, recorded_path=None, source_root=None):
    """Prefer raw/<family>, retain legacy fallback, fail ambiguous matches.

    source_root may be a family directory, a raw directory, or a repository root.
    Historical absolute paths supply a filename only, never arbitrary file access.
    """
    if family not in FAMILIES:
        raise ValueError(f'Unknown source family: {family}')
    root = Path(repo_root).resolve()
    directories = []
    if source_root is not None:
        explicit = Path(source_root).resolve()
        directories.extend([explicit / family, explicit / 'vision' / 'video' / 'raw' / family, explicit / 'video' / 'raw' / family, explicit])
    directories.extend([root / 'vision/video/raw' / family, root / 'vision/video',
                        root / 'video/raw' / family, root / 'video'])
    if family == 'NL_tutorial':
        directories.extend([root / 'vision/video/raw' / LEGACY_NL / LEGACY_NL,
                            root / 'vision/video/raw' / LEGACY_NL,
                            root / 'raw' / LEGACY_NL / LEGACY_NL, root / 'raw' / LEGACY_NL])
    filename = PureWindowsPath(str(recorded_path)).name if recorded_path else None
    if filename and family == 'BV1Hs411E7aP' and not filename.startswith('BV1Hs411E7aP_'):
        raise ValueError('BV source filename must retain its BV identifier')
    if filename and family == 'NL_tutorial' and not re.match(r'P\d+-', filename):
        raise ValueError('NL source filename must retain its P<lesson>- prefix')
    if filename:
        pattern = filename
    elif family == 'BV1Hs411E7aP':
        match = re.fullmatch(r'p?(\d+)', str(lesson).lower())
        if not match:
            raise ValueError(f'Invalid BV part: {lesson}')
        pattern = f'BV1Hs411E7aP_p{int(match.group(1)):02d}.mp4'
    else:
        if not re.fullmatch(r'\d+', str(lesson)):
            raise ValueError(f'Invalid NL lesson: {lesson}')
        pattern = f'P{int(lesson)}-*.mp4'
    for directory in dict.fromkeys(directories):
        if not directory.is_dir():
            continue
        matches = ([directory / filename] if filename and (directory / filename).is_file()
                   else [] if filename else sorted(p for p in directory.glob(pattern) if p.is_file()))
        if len(matches) > 1:
            raise ValueError(f'Ambiguous {family} source for {pattern}: {matches}')
        if matches:
            resolved = matches[0].resolve()
            if not resolved.is_relative_to(directory.resolve()):
                raise ValueError(f'Source link escapes source directory: {matches[0]}')
            return resolved
    raise FileNotFoundError(f'{family} source {pattern!r} not found; searched {[str(d) for d in directories]}')


def find_ffmpeg(repo_root=REPO_ROOT, explicit=None):
    root = Path(repo_root).resolve()
    if explicit:
        executable = Path(explicit).resolve()
        if not executable.is_file():
            raise FileNotFoundError(executable)
        return executable
    candidates = [root / 'vision/tools/portable/losslesscut/resources/ffmpeg.exe',
                  root / 'tools/portable/losslesscut/resources/ffmpeg.exe',
                  root / '工具/losslesscut/resources/ffmpeg.exe', root.parent / '_tools/ffmpeg.exe']
    for work in [root / 'vision/video/archive/work_batches_20261020',
                 root / 'video/archive/work_batches_20261020', root / '训练视频']:
        candidates.extend(sorted((work / '.tools/imageio_ffmpeg/binaries').glob('ffmpeg*.exe')))
    found = next((path for path in candidates if path.is_file()), None)
    if found:
        return found.resolve()
    system = shutil.which('ffmpeg')
    if system:
        return Path(system).resolve()
    raise FileNotFoundError('ffmpeg not found; install separately or supply --ffmpeg')


def add_source_arguments(parser):
    parser.add_argument('--repo-root', type=Path, default=REPO_ROOT)
    parser.add_argument('--source-root', type=Path, help='Optional source-family/raw/repository root')
    parser.add_argument('--ffmpeg', type=Path, help='Existing ffmpeg executable')
    parser.add_argument('--preflight', action='store_true', help='Print paths only; no decode/export or optional image packages')


def print_preflight(sources, ffmpeg, **extra):
    print(json.dumps({'sources': [str(p) for p in sources], 'ffmpeg': str(ffmpeg), **extra}, ensure_ascii=False, indent=2))
