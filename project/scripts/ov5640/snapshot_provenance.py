"""Bind snapshot build inputs before preparation, then seal generated artifacts.

Integrity against accidental drift, not a cryptographic signature against a
malicious party able to rewrite both files and manifests. All paths stay in repo.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PATTERNS = (
    'project/fpga/rtl/ov5640_snapshot/*.v',
    'project/fpga/rtl/ov5640_stereo/*.v',
    'project/fpga/scripts/ov5640_snapshot*.tcl',
    'project/fpga/scripts/load_ov5640_pins.tcl',
    'project/fpga/xdc/ov5640_stereo_pins.xdc',
    'project/scripts/ov5640/*.py',
    'project/board/ov5640_snapshot/capture.py',
    'project/board/ov5640_snapshot/continuous_capture.py',
    'project/board/ov5640_snapshot/hdmi_preview.py',
    'project/scripts/ov5640/run_snapshot_build.bat',
    'project/analysis/ov5640_snapshot_20261027/ps_config.tcl',
    'project/fpga/constraints/ov5640_snapshot*.json',
    'project/fpga/scripts/w6_hdmi_bd.tcl',
    'project/fpga/scripts/w6_timing_ip_constraints.tcl',
    'project/fpga/xdc/hdmi_w6.xdc',
    'project/fpga/xdc/ov5640_snapshot_hdmi.xdc',
    # Bind the actual packaged HDL/XML/constraints, not only HLS C++ sources.
    'project/fpga/ip_repo/rgb2dvi_v1_2/component.xml',
    'project/fpga/ip_repo/rgb2dvi_v1_2/src/*',
    'project/fpga/ip_repo/rgb2dvi_v1_2/xgui/*.tcl',
    'project/fpga/ip_repo/axi_dynclk_v1_0/component.xml',
    'project/fpga/ip_repo/axi_dynclk_v1_0/src/*',
    'project/fpga/ip_repo/axi_dynclk_v1_0/xgui/*.tcl',
    'project/fpga/ip_repo/color_swap_1.1/component.xml',
    'project/fpga/ip_repo/color_swap_1.1/*.v',
    'project/fpga/ip_repo/color_swap_1.1/xgui/*.tcl',
    'project/fpga/ip_repo/if/tmds_v1_0/*.xml',
    'project/algo/video_hls/pixel_unpack/pixel_unpack/solution1/impl/ip/component.xml',
    'project/algo/video_hls/pixel_unpack/pixel_unpack/solution1/impl/ip/hdl/**/*',
    'project/algo/video_hls/pixel_unpack/pixel_unpack/solution1/impl/ip/constraints/*.xdc',
    'project/algo/video_hls/pixel_unpack/pixel_unpack/solution1/impl/ip/xgui/*.tcl',
    'project/algo/video_hls/color_convert/color_convert/solution1/impl/ip/component.xml',
    'project/algo/video_hls/color_convert/color_convert/solution1/impl/ip/hdl/**/*',
    'project/algo/video_hls/color_convert/color_convert/solution1/impl/ip/constraints/*.xdc',
    'project/algo/video_hls/color_convert/color_convert/solution1/impl/ip/xgui/*.tcl',
)
ARTIFACTS = ('ov5640_snapshot.bit', 'ov5640_snapshot.hwh', 'routed.dcp',
             'build_result.tcl', 'sccb_structure.txt', 'timing_routed.rpt',
             'drc.rpt', 'methodology.rpt', 'cdc.rpt', 'route_status.rpt',
             'bus_skew.rpt', 'external_io_status.json')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inside(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or Path(relative).is_absolute():
        raise ValueError(f'Path escapes root: {relative}')
    return path

def record(paths, root):
    root = Path(root).resolve()
    result = {}
    for path in sorted(set(Path(p).resolve() for p in paths)):
        if not path.is_relative_to(root):
            raise ValueError(f'Input outside repo: {path}')
        result[path.relative_to(root).as_posix()] = digest(path)
    if not result:
        raise ValueError('Empty input set')
    return result

def inputs(root):
    return record((p for pattern in PATTERNS for p in Path(root).glob(pattern) if p.is_file()), root)

def save_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)

def check_files(root, hashes):
    if not hashes:
        raise ValueError('Empty hashes')
    for name, expected in hashes.items():
        if digest(inside(root, name)) != expected:
            raise ValueError(f'File changed: {name}')

def begin(root, project_dir):
    project_dir = Path(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    save_new(project_dir / 'build_inputs.json',
             dict(schema_version=1, sources=inputs(root)))

def bind_project(root, project_dir, paths):
    project_dir = Path(project_dir)
    check_inputs(root, project_dir, require_project=False)
    save_new(project_dir / 'project_inputs.json',
             dict(schema_version=1, sources=record(paths, root)))

def check_inputs(root, project_dir, require_project=True):
    project_dir = Path(project_dir)
    source = json.loads((project_dir / 'build_inputs.json').read_text(encoding='utf-8'))
    check_files(root, source['sources'])
    if inputs(root) != source['sources']:
        raise ValueError('Build input set changed; prepare a new project')
    if require_project:
        project = json.loads((project_dir / 'project_inputs.json').read_text(encoding='utf-8'))
        check_files(root, project['sources'])
    return source

def seal(root, project_dir, build):
    build = Path(build)
    source = check_inputs(root, project_dir)
    project = json.loads((Path(project_dir) / 'project_inputs.json').read_text(encoding='utf-8'))
    result = (build / 'build_result.tcl').read_text()
    for marker in ('set snapshot_build_complete 1', 'set snapshot_sccb_structure_pass 1'):
        if marker not in result:
            raise ValueError(f'Missing gate: {marker}')
    save_new(build / 'build_provenance.json', dict(
        schema_version=1, sources=source['sources'], project_sources=project['sources'],
        artifacts={name: digest(build / name) for name in ARTIFACTS}))

def verify(root, build):
    build = Path(build)
    data = json.loads((build / 'build_provenance.json').read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or set(data['artifacts']) != set(ARTIFACTS):
        raise ValueError('Invalid provenance schema or incomplete artifact set')
    check_files(root, data['sources'])
    if inputs(root) != data['sources']:
        raise ValueError('Source set drift after build')
    check_files(root, data['project_sources'])
    check_files(build, data['artifacts'])
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('begin', 'project', 'check', 'seal', 'verify'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--project', type=Path)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--file-list', type=Path)
    args = parser.parse_args()
    if args.action == 'begin': begin(args.root, args.project)
    elif args.action == 'project':
        bind_project(args.root, args.project, args.file_list.read_text(encoding='utf-8-sig').splitlines())
    elif args.action == 'check': check_inputs(args.root, args.project)
    elif args.action == 'seal': seal(args.root, args.project, args.build)
    else: verify(args.root, args.build)
    print(f'PROVENANCE_{args.action.upper()}_PASS')

if __name__ == '__main__': main()
