"""Export source-backed prerequisites, not a trained-model golden reference."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import re
import struct
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())

@dataclass(frozen=True)
class Fixed:
    width: int
    integer: int
    signed: bool = True
    rounding: str = 'AP_TRN'
    overflow: str = 'AP_WRAP'

    def __post_init__(self):
        if self.width <= 0 or not 0 <= self.integer <= self.width:
            raise ValueError('Only 0 <= integer <= width is supported')
        if self.rounding not in ('AP_TRN', 'AP_RND_CONV'):
            raise ValueError('Unsupported rounding')
        if self.overflow not in ('AP_WRAP', 'AP_SAT'):
            raise ValueError('Unsupported overflow')

    @property
    def fractional(self):
        return self.width - self.integer

    def encode(self, value):
        scaled = Fraction(value) * (1 << self.fractional)
        low, rem = divmod(scaled.numerator, scaled.denominator)
        raw = low
        if self.rounding == 'AP_RND_CONV':
            twice = 2 * rem
            raw += int(twice > scaled.denominator or
                       (twice == scaled.denominator and low % 2 != 0))
        lo = -(1 << (self.width - 1)) if self.signed else 0
        hi = (1 << (self.width - int(self.signed))) - 1
        if self.overflow == 'AP_SAT':
            return min(hi, max(lo, raw))
        return (raw - lo) % (1 << self.width) + lo

    def decode(self, raw):
        return Fraction(raw, 1 << self.fractional)

    def describe(self):
        return dict(asdict(self), fractional=self.fractional,
                    lsb=f'2^-{self.fractional}',
                    note='Integer width includes sign bit for signed formats')

def parse_fixed(text):
    m = re.fullmatch(r'(?:ap_)?(u?fixed)<([^>]+)>', text.replace(' ', ''))
    if not m:
        raise ValueError(f'Unsupported type: {text}')
    args = m[2].split(',')
    if len(args) not in (2, 3, 4, 5):
        raise ValueError('Unsupported fixed type arity')
    if len(args) == 5 and args[4] != '0':
        raise ValueError('Nonzero saturation bits unsupported')
    mode = lambda x: x if x.startswith('AP_') else 'AP_' + x
    return Fixed(int(args[0]), int(args[1]), m[1] == 'fixed',
                 mode(args[2]) if len(args) > 2 else 'AP_TRN',
                 mode(args[3]) if len(args) > 3 else 'AP_WRAP')

def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]

def input_map(fmt):
    rows = []
    for pixel in range(256):
        value = f32(pixel / 255.0)
        raw = fmt.encode(Fraction.from_float(value))
        rational = fmt.encode(Fraction(pixel, 255))
        rows.append(dict(pixel=pixel, float32=value, raw_code=raw,
                         rational_raw_code=rational, delta=raw-rational))
    return rows

def architecture(source):
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'make_model')
    rows = []
    for n in fn.body:
        if not isinstance(n, ast.Assign) or not isinstance(n.value, ast.Call):
            continue
        c = n.value.func if isinstance(n.value.func, ast.Call) else n.value
        name = ast.unparse(c.func)
        if name in {'Input', 'Conv', 'BatchNormalization', 'Act',
                    'MaxPooling2D', 'GlobalAveragePooling2D'}:
            rows.append(dict(order=len(rows), operation=name, source_line=n.lineno,
                             expression=ast.unparse(n.value),
                             hls_input_type=None, hls_output_type=None,
                             hls_accumulator_type=None, cast_sites=None,
                             status='source_configuration_only'))
    dense = next(n for n in ast.walk(fn) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'QDense')
    rows.append(dict(order=len(rows), operation='QDense', source_line=dense.lineno,
                     expression=ast.unparse(dense), hls_input_type=None,
                     hls_output_type=None, hls_accumulator_type=None,
                     cast_sites=None, status='source_configuration_only'))
    return rows

def export(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError('Choose a new output directory; evidence is not overwritten')
    relative = ['project/scripts/r3/r3_baseline_20261024.py',
                'project/scripts/r3/r3_hls_synth_20261025.py',
                'project/scripts/r3/r3_hls4ml_20261024.py',
                'project/analysis/r3/r3_hls_synth_20261025.json']
    sources = {p: (root / p).read_text(encoding='utf-8-sig') for p in relative}
    report = json.loads(sources[relative[3]])
    synth_tree = ast.parse(sources[relative[1]])
    defaults = {}
    for node in ast.walk(synth_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_argument' and node.args:
            default = next((k.value for k in node.keywords if k.arg == 'default'), None)
            if isinstance(default, ast.Constant):
                defaults[ast.literal_eval(node.args[0])] = default.value
    for role, recorded in report['batchnorm_precision'].items():
        if defaults.get('--bn-' + role + '-precision') != recorded:
            raise ValueError('Historical BN precision differs from current source default')
    assignments = [n for n in ast.walk(synth_tree) if isinstance(n, ast.Assign)]
    normalization = next(ast.unparse(n.value) for n in assignments
                         if ast.unparse(n.targets[0]) == 'inputs')
    if normalization != "data['X'][indices].astype(np.float32) / 255.0":
        raise ValueError('Normalization changed; review input mapping before exporting')
    precision = next(ast.literal_eval(n.value) for n in ast.walk(synth_tree)
                     if isinstance(n, ast.Assign)
                     and ast.unparse(n.targets[0]) == "config['LayerName']['input_1']['Precision']['result']")
    formats = {'input': parse_fixed(precision), 'output': parse_fixed(report['output_precision'])}
    formats.update({'bn_' + k: parse_fixed(v) for k, v in report['batchnorm_precision'].items()})
    layers = architecture(sources[relative[0]])
    artifacts = ['project/_tmp/r3/r3_model_quant.keras', 'project/_tmp/r3/tensors.npz',
                 'project/_tmp/r3/r3_hls_synth_rf576_p40/firmware/defines.h',
                 'project/_tmp/r3/r3_hls_synth_rf576_p40/firmware/parameters.h',
                 'project/_tmp/r3/r3_hls_synth_rf576_p40/firmware/gesture_cls.cpp']
    hashes = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in relative}
    hashes['project/scripts/r3/export_rtl_numeric_contract.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    mappings = input_map(formats['input'])
    contract = dict(schema_version=1, status='partial_source_contract',
        model_golden_ready=False, rtl_numeric_contract_ready=False,
        trained_weights_exported=False, full_network_reference_implemented=False,
        sources_sha256=hashes, expected_artifacts={p: (root / p).is_file() for p in artifacts},
        formats={k: v.describe() for k, v in formats.items()},
        provenance={'input': 'conversion script setting, not recovered generated type',
                    'bn_and_output': 'historical R3.3 report, not new tool execution'},
        layers=layers,
        source_quantizers=[dict(expression=ast.unparse(n), source_line=n.lineno)
                           for n in ast.walk(ast.parse(sources[relative[0]]))
                           if isinstance(n, ast.Constant) and isinstance(n.value, str)
                           and n.value.startswith(('quantized_bits(', 'quantized_relu('))],
        normalization_expression=normalization,
        input_mapping=dict(count=256, differing_from_exact_rational=sum(r['delta'] != 0 for r in mappings),
                           max_abs_raw_delta=max(abs(r['delta']) for r in mappings),
                           validation='binary32 software model; no original NumPy or Vitis replay'),
        unknowns=['trained quantized weights and convolution/Dense biases',
                  'BN moving mean, variance, gamma, beta, epsilon and transformed scale/bias',
                  'generated product/accumulator types, rounding and assignment/cast sites',
                  'generated activation, pooling and GAP intermediate semantics',
                  'generated weight layout, layer ordering/fusions and expression promotion',
                  'original tensors, label order, holdout indices and per-layer golden tensors'])
    output.mkdir(parents=True)
    (output/'contract.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding='utf-8')
    with (output/'input_uint8_to_fixed40.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(mappings[0]))
        writer.writeheader(); writer.writerows(mappings)
    vectors = []
    for name, fmt in formats.items():
        step = Fraction(1, 1 << fmt.fractional)
        low = -(1 << (fmt.width - 1)) if fmt.signed else 0
        high = (1 << (fmt.width - int(fmt.signed))) - 1
        for value in [Fraction(0), -step/2, step/2, fmt.decode(low), fmt.decode(high),
                      fmt.decode(low)-step, fmt.decode(high)+step]:
            vectors.append(dict(format=name, input=str(value), raw=fmt.encode(value)))
    (output/'conversion_vectors.json').write_text(json.dumps(dict(kind='synthetic_assignment_boundaries_not_layer_golden', vectors=vectors), indent=2), encoding='utf-8')
    lines = ['# RTL 第一步：定点基础与缺失产物', '',
             '状态：部分完成。不是完整逐层契约，不可作为旧模型RTL等价验收依据。', '',
             '## 已核实格式（脚本或历史报告，非恢复的生成头文件）', '',
             '| 项 | W | I（含符号） | F | 舍入 | 溢出 |', '|---|---:|---:|---:|---|---|']
    for name, fmt in formats.items():
        lines.append(f'| {name} | {fmt.width} | {fmt.integer} | {fmt.fractional} | {fmt.rounding} | {fmt.overflow} |')
    lines += ['', 'AP_TRN向负无穷取整；AP_WRAP模回绕。规则作用于赋值边界，不代表表达式内部精度。',
              '', '## 输入映射', '',
              f'256个uint8值经binary32归一化再转40位定点，直接用有理数p/255替代时有{contract["input_mapping"]["differing_from_exact_rational"]}项不同，最大差{contract["input_mapping"]["max_abs_raw_delta"]}个输入LSB。',
              '此表是软件建模结果，未经原NumPy或Vitis交叉验收，不是原网络golden。',
              '', '## 逐层来源索引', '', '|序号|操作|基线脚本行|生成类型/累加/截断|', '|---|---|---:|---|']
    lines += [f'| {r["order"]} | {r["operation"]} | {r["source_line"]} | 未知，见contract.json |' for r in layers]
    lines += ['', '## 缺口', ''] + ['- '+s for s in contract['unknowns']]
    lines += ['', '必须恢复原.keras、tensors.npz与HLS工程；若遗失，需另建新模型基线，重新训练/评测/导出，不能冒称恢复原权重。',
              '', '仅需Python标准库；输出目录必须不存在。conversion_vectors.json为人工边界输入赋值参考，不是网络golden。',
              '未运行RTL、Vitis CSim、综合或上板。历史196个logit一致不证明逐层参考已经存在。',
              '来源与导出器SHA-256已记录在contract.json。',
              'AMD UG1399: https://docs.amd.com/r/2024.1-English/ug1399-vitis-hls/Overview-of-Arbitrary-Precision-Fixed-Point-Data-Types']
    (output/'README.md').write_text(chr(10).join(lines)+chr(10), encoding='utf-8')
    return contract

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = export(args.root, args.output)
    print(json.dumps({k: result[k] for k in ('status', 'rtl_numeric_contract_ready', 'input_mapping')}, ensure_ascii=False))
