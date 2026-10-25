"""Layer geometry and safe graph fusion contracts; no board or TensorFlow."""
import json
import numpy as np
from project.board.keypoints.hand_layer_runtime import configuration,LayerHardwareBackend,pack_parameters
from project.board.keypoints.hand_runtime import HandGraph

def test_layer_same_padding_stride_and_channel_tail():
    spec=dict(kind='Conv2D',output_shape=[1,2,4,17],dilation=[1,1],strides=[2,2],padding='same')
    config=configuration(np.zeros((1,4,7,3),np.int16),np.zeros((3,3,3,17),np.int16),spec,
        dict(rescale_shift=-3,relu_limit=3072))
    assert config.tolist()==[4,7,3,2,4,17,3,3,2,2,0,1,0,1,-3,3072]

def test_depthwise_is_native_channelwise_not_sparse_gemm():
    spec=dict(kind='DepthwiseConv2D',output_shape=[1,3,3,17],dilation=[1,1],strides=[1,1],padding='same')
    config=configuration(np.zeros((1,3,3,17),np.int16),np.zeros((5,5,17,1),np.int16),spec,None)
    assert config[12]==1 and config[2]==config[5]==17

def test_fusion_never_changes_another_branch_consumer(tmp_path):
    shape=[1,1,1,1]
    graph=[dict(name='input',kind='InputLayer',inputs=[],output='input',output_shape=shape,fraction=0),
        dict(name='conv',kind='Conv2D',inputs=['input'],output='pre',output_shape=shape,fraction=0),
        dict(name='relu',kind='ReLU',inputs=['pre'],output='post',output_shape=shape,fraction=0,rescale_shift=0,relu_limit=6),
        dict(name='branch',kind='Add',inputs=['pre','post'],output='sum',output_shape=shape,fraction=0)]
    (tmp_path/'graph.json').write_text(json.dumps(graph));np.savez(tmp_path/'weights.npz')
    class Backend:
        def layer(self,*args):raise AssertionError('Planning must not execute')
    assert HandGraph(tmp_path,Backend()).fusions=={}
    graph.pop()
    (tmp_path/'graph.json').write_text(json.dumps(graph))
    planned=HandGraph(tmp_path,Backend())
    assert planned.fusions['conv']['name']=='relu'

def test_layer_driver_flushes_only_valid_ranges_and_uses_generated_config_name():
    events=[]
    class Buffer(np.ndarray):
        def __new__(cls,name,n,dtype,address):
            value=np.zeros(n,dtype).view(cls);value.name=name;value.physical_address=address;return value
        def __array_finalize__(self,obj):
            if obj is not None:
                self.name=getattr(obj,'name','');self.physical_address=getattr(obj,'physical_address',0)
        def flush(self):events.append((self.name,'flush',self.nbytes))
        def invalidate(self):events.append((self.name,'invalidate',self.nbytes))
    backend=object.__new__(LayerHardwareBackend)
    for index,(name,dtype) in enumerate([('la',np.int16),('lo',np.int16),('lb',np.int16),
        ('bias',np.int64),('shifts',np.int8),('config',np.int32)]):
        setattr(backend,name,Buffer(name,16 if name=='config' else 64,dtype,4096*(index+1)))
    backend.regs={'mac':{'registers':{}}};backend.mac=object();backend.mac_calls=0
    backend.resident={'conv':dict(kernel=0x12000,bias=0x14000,shift=0x16000)}
    backend.profile=dict(input_copy_flush_s=0.,launch_wait_s=0.,output_invalidate_view_s=0.,cpu_sync_s=0.)
    backend._dirty_outputs=set()
    backend.outputs={'conv':backend.lo[:2]};backend.output_addresses=set()
    backend.traffic=dict(input_bytes_copied=0,resident_input_layers=0)
    calls=[];backend._call=lambda ip,regs,values:calls.append(values)
    backend.lo[:2]=[123,-456]
    spec=dict(name='conv',kind='Conv2D',output_shape=[1,1,1,2],dilation=[1,1],strides=[1,1],padding='valid')
    actual=backend.layer(np.ones((1,1,1,3),np.int16),np.ones((1,1,3,2),np.int16),
        np.zeros(2,np.int64),np.zeros(2,np.int8),spec,None)
    assert actual.reshape(-1).tolist()==[123,-456]
    assert ('la','flush',6) in events
    assert not any(name in ('lb','bias','shifts') for name,op,size in events)
    assert ('lo','invalidate',4) not in events
    backend.sync_for_cpu(actual)
    assert ('lo','invalidate',4) in events
    before=len(events);backend.sync_for_cpu(actual)
    assert len(events)==before
    assert calls[0]['config_r']==backend.config.physical_address
    assert 'config' not in calls[0]
    assert calls[0]['b']==0x12000 and calls[0]['bias']==0x14000 and calls[0]['shift']==0x16000
    events.clear()
    previous=Buffer('previous',3,np.int16,0x22000).reshape(1,1,1,3)
    backend.output_addresses.add(previous.physical_address)
    backend.layer(previous,np.ones((1,1,3,2),np.int16),np.zeros(2,np.int64),np.zeros(2,np.int8),spec,None)
    assert not any(name=='la' for name,op,size in events)
    assert calls[-1]['a']==0x22000 and backend.traffic['resident_input_layers']==1

def test_resident_parameters_preserve_each_layer_layout_and_offsets():
    graph=[dict(name='dw',kind='DepthwiseConv2D'),dict(name='dense',kind='Dense')]
    weights={}
    for name,n in [('dw',6),('dense',3)]:
        for key,dtype in [('kernel',np.int16),('bias',np.int64),('shift',np.int8)]:
            weights[name+'_'+key]=np.arange(n,dtype=dtype)
    packed,offsets=pack_parameters(graph,weights)
    for name,n in [('dw',6),('dense',3)]:
        for key in packed:
            start=offsets[name][key]
            assert np.array_equal(packed[key][start:start+n],weights[name+'_'+key])
    assert offsets['dense']==dict(kernel=6,bias=6,shift=6)

def test_large_vector_batches_respect_selected_hardware_capacity():
    calls=[]
    class Backend:
        vector_capacity=65536
        def vector(self,a,b,count,*args):
            calls.append(count)
            return a.reshape(-1)[:count].copy()
    graph=object.__new__(HandGraph);graph.backend=Backend()
    source=np.arange(70003,dtype=np.int64).astype(np.int16)
    actual=graph._vector(source,None,5,0)
    assert calls==[65536,4467]
    assert np.array_equal(actual,source)
