"""Read-only landmark-model deployment preflight. Does not synthesize or program hardware."""
import argparse
import ast
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]


def enum_names(enum):
    return {value: key for key, value in vars(enum).items() if key.isupper() and isinstance(value, int)}


def inspect_model(path, schema):
    data = path.read_bytes()
    model = schema.Model.GetRootAsModel(data, 0)
    ops = enum_names(schema.BuiltinOperator)
    types = enum_names(schema.TensorType)
    graph = model.Subgraphs(0)
    def tensor(index):
        value = graph.Tensors(index)
        return dict(shape=[int(value.Shape(i)) for i in range(value.ShapeLength())],
                    dtype=types.get(value.Type(), str(value.Type())))
    counts = Counter()
    for i in range(graph.OperatorsLength()):
        code = model.OperatorCodes(graph.Operators(i).OpcodeIndex())
        builtin = max(code.BuiltinCode(), code.DeprecatedBuiltinCode())
        name = ops.get(builtin, str(builtin))
        if code.CustomCode():
            name += ':'+code.CustomCode().decode()
        counts[name] += 1
    return dict(file=path.as_posix().split('/modules/')[-1], bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                inputs=[tensor(graph.Inputs(i)) for i in range(graph.InputsLength())],
                outputs=[tensor(graph.Outputs(i)) for i in range(graph.OutputsLength())],
                operators=dict(sorted(counts.items())),
                stored_tensor_types=dict(Counter(types.get(graph.Tensors(i).Type(), '?') for i in range(graph.TensorsLength()))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mediapipe-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output == ROOT or output.exists():
        raise ValueError('Use a new dedicated workspace output directory')
    from tensorflow.lite.python import schema_py_generated as schema
    candidates = [
        'pose_detection/pose_detection.tflite',
        'pose_landmark/pose_landmark_full.tflite',
        'holistic_landmark/hand_recrop.tflite',
        'hand_landmark/hand_landmark_full.tflite',
        'hand_landmark/hand_landmark_lite.tflite',
    ]
    models = [inspect_model(args.mediapipe_root/'modules'/name, schema) for name in candidates]
    distribution = importlib.metadata.distribution('hls4ml')
    converter = Path(distribution.locate_file('hls4ml/converters/__init__.py'))
    functions = sorted(n.name for n in ast.parse(converter.read_text(encoding='utf-8')).body
                       if isinstance(n, ast.FunctionDef) and n.name.startswith('convert_from_'))
    rpt = ROOT/'project/fpga/project/glove/w6_hdmi_utilization.rpt'
    text = rpt.read_text(encoding='utf-8')
    resources = {}
    for name in ('Slice LUTs','Block RAM Tile','DSPs'):
        match = re.search(r'\| '+re.escape(name)+r'\s+\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)', text)
        if match is None:
            raise ValueError('Resource report field missing: '+name)
        used, total = map(int, match.groups())
        resources[name] = dict(used=used, total=total, arithmetic_headroom=total-used)
    report = dict(status='not_deployable_yet', target='xc7z020clg400-1',
        scope='body_and_both_hands_landmarks_not_word_classification',
        route='inspect_only', models=models,
        hls4ml=dict(version=distribution.version, converters=functions,
                   direct_tflite_frontend_found='convert_from_tflite_model' in functions),
        existing_routed_resources=resources,
        resource_evidence=rpt.relative_to(ROOT).as_posix(),
        resource_caveat='Historical W6 routed report; headroom is not a new accelerator utilization estimate or fit guarantee.',
        blockers=[
            'No validated fixed-point landmark graph or HLS/RTL landmark accelerator exists in this repository.',
            'Installed hls4ml has no direct TFLite converter; a validated intermediate model conversion or new backend is required.',
            'ROI generation/crop/resize, detector scheduling, tracking and landmark postprocessing must be partitioned and implemented.',
            'No landmark CSim, RTL co-simulation, resource/timing signoff, AXI integration or matching bit/hwh exists.',
            'Existing R3 gesture CNN predicts word classes, not coordinates; its results/resources cannot stand in for landmark deployment.',
        ],
        actions_not_performed=['model_replacement','training','synthesis','bitstream_generation','bitstream_download','board_reboot'],
        next_choice='Approve staged hand-landmark-first PL development, or require full pose+both-hands deployment as the initial scope.')
    output.mkdir(parents=True)
    (output/'preflight.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
