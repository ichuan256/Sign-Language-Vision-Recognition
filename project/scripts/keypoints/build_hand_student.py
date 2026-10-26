"""Instantiate untrained student proposals; verify shapes/MACs, never train or deploy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
os.environ.setdefault('TF_USE_LEGACY_KERAS','1')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
try:
    from .plan_realtime_hand import student_layers,ROOT
except ImportError:
    from plan_realtime_hand import student_layers,ROOT


def build(spec,size):
    import tf_keras as keras
    x=inputs=keras.Input((size,size,spec['input_channels']),name='roi_rgb')
    for layer in student_layers(spec,size):
        name=layer['name'];kind=layer['kind']
        if kind=='Dense':
            x=keras.layers.Flatten(name='spatial_flatten')(x)
            x=keras.layers.Dense(sum(spec['outputs'].values()),name=name)(x)
        else:
            block_index=int(name.split('_')[1]) if name.startswith(('dw_','pw_')) else None
            params=spec['stem'] if name=='stem' else spec['separable_blocks'][block_index]
            stride=params['stride'] if kind=='DepthwiseConv2D' or name=='stem' else 1
            kernel=params['kernel'] if kind=='DepthwiseConv2D' or name=='stem' else 1
            if kind=='DepthwiseConv2D':
                x=keras.layers.DepthwiseConv2D(kernel,strides=stride,padding='same',use_bias=False,name=name)(x)
            else:
                x=keras.layers.Conv2D(layer['output_shape'][-1],kernel,strides=stride,padding='same',use_bias=False,name=name)(x)
            x=keras.layers.BatchNormalization(name=name+'_bn')(x)
            x=keras.layers.ReLU(name=name+'_relu')(x)
    return keras.Model(inputs,x,name=spec['name']+'_'+str(size))


def main():
    import numpy as np
    import tf_keras as keras
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--student',type=Path,default=ROOT/'project/algo/keypoints/hand_student_v1.json')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp output required')
    spec=json.loads(a.student.read_text());out.mkdir(parents=True)
    reports=[]
    for size in spec['input_sizes']:
        keras.utils.set_random_seed(20261026)
        model=build(spec,size);layers=student_layers(spec,size);actual_kernel_values=0
        for expected in layers:
            actual=model.get_layer(expected['name'])
            if list(actual.output_shape[1:])!=expected['output_shape']:raise RuntimeError('Shape mismatch')
            count=actual.get_weights()[0].size
            if count!=expected['kernel_values']:raise RuntimeError('Kernel count mismatch')
            actual_kernel_values+=count
        outputs=model(np.zeros((2,size,size,3),np.float32),training=False).numpy()
        if outputs.shape!=(2,sum(spec['outputs'].values())) or not np.isfinite(outputs).all():
            raise RuntimeError('Untrained shape smoke failed')
        path=out/(model.name+'_UNTRAINED.keras');model.save(path)
        with (out/(model.name+'_summary.txt')).open('w') as stream:model.summary(print_fn=lambda s:stream.write(s+'\n'))
        reports.append(dict(input_size=size,kernel_values=actual_kernel_values,parameters_with_BN=model.count_params(),
            shape_smoke_passed=True,model_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    report=dict(status='untrained_architecture_shape_verified',trained=False,accuracy_validated=False,
        quantized=False,HLS_validated=False,board_deployed=False,models=reports,
        source_sha256=hashlib.sha256(a.student.read_bytes()).hexdigest())
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
