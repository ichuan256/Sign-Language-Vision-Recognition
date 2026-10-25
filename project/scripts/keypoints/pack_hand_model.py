"""Offline integer model packing; board receives no floating-point weights."""
import argparse
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def pack(source,destination):
    graph = json.loads((source/'graph.json').read_text())
    fractions,arrays = {},{}
    with np.load(source/'weights.npz') as weights:
        for s in graph:
            name,kind = s['name'],s['kind']
            fs = [fractions[k] for k in s['inputs']] if kind!='InputLayer' else []
            if kind in ('Conv2D','DepthwiseConv2D','Dense'):
                arrays[name+'_kernel'] = weights[name+'_kernel'].astype(np.int16)
                fw = np.asarray(s['weight_fraction'])
                bias = np.rint(np.ldexp(weights[name+'_bias_float'].astype(np.float64),fs[0]+fw))
                shift = fs[0]+fw-s['fraction']
                if np.max(np.abs(bias))>=2**47 or shift.min()<-31 or shift.max()>47:
                    raise ValueError('Hardware bias/shift bounds exceeded')
                arrays[name+'_bias'] = bias.astype(np.int64)
                arrays[name+'_shift'] = shift.astype(np.int8)
            elif kind=='Add':
                common = max(fs)
                s.update(align_a=common-fs[0],align_b=common-fs[1],rescale_shift=common-s['fraction'])
            elif kind in ('ReLU','MaxPooling2D','GlobalAveragePooling2D','Flatten'):
                s['rescale_shift'] = fs[0]-s['fraction']
                if kind=='ReLU':
                    s['relu_limit'] = -1 if s['max_value'] is None else min(32767,round(s['max_value']*2**fs[0]))
            elif kind=='Activation':
                s.update(sigmoid_index_shift=fs[0]-6,sigmoid_output_shift=15-s['fraction'])
            if kind!='Concatenate':
                fractions[s['output']] = s['fraction']
    destination.mkdir(parents=True,exist_ok=False)
    (destination/'graph.json').write_text(json.dumps(graph,indent=2)+'\n',encoding='utf-8')
    np.savez_compressed(destination/'weights.npz',**arrays)
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--validation',type=Path,required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output==ROOT or output.exists():
        raise ValueError('Use a new workspace directory')
    graph = pack(args.source,output)
    input_spec = next(s for s in graph if s['kind']=='InputLayer')
    with np.load(args.validation) as data:
        codes = np.clip(np.rint(np.ldexp(data['inputs'].astype(np.float64),input_spec['fraction'])),-32768,32767).astype(np.int16)
        np.savez_compressed(output/'probes.npz',roi_codes=codes,reference=data['integer'])
        np.save(output/'roi0.npy',codes[0])
    print('Packed integer-only graph '+str(output))


if __name__=='__main__':
    main()
