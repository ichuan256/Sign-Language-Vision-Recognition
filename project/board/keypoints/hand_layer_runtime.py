"""Whole-layer PL scheduler. Same model/scales, fused two-stage requantization."""
import ctypes
import json
from pathlib import Path
import time
import numpy as np
try:
    from .hand_runtime import DLLBackend,HardwareBackend
except ImportError:
    from hand_runtime import DLLBackend,HardwareBackend

def configuration(x,w,spec,relu):
    if spec['kind']=='Dense':
        ih,iw,ci=1,1,x.shape[-1];oh,ow,co=1,1,w.shape[-1];kh=kw=sy=sx=1;py=px=0
    else:
        if spec['dilation']!=[1,1]:raise ValueError('Dilation unsupported')
        if spec['kind']=='DepthwiseConv2D' and w.shape[-1]!=1:
            raise ValueError('Only depthwise multiplier 1 supported')
        ih,iw,ci=x.shape[1:];oh,ow,co=spec['output_shape'][1:]
        kh,kw=w.shape[:2];sy,sx=spec['strides'];py=px=0
        if spec['padding']=='same':
            py=max(0,(oh-1)*sy+kh-ih)//2;px=max(0,(ow-1)*sx+kw-iw)//2
        elif spec['padding']!='valid':raise ValueError('Unknown padding')
    return np.array([ih,iw,ci,oh,ow,co,kh,kw,sy,sx,py,px,
        int(spec['kind']=='DepthwiseConv2D'),int(relu is not None),
        relu['rescale_shift'] if relu else 0,relu['relu_limit'] if relu else -1],np.int32)

class LayerDLLBackend(DLLBackend):
    name='host_compiled_HLS_layer_C_not_PL'
    def __init__(self,path,dependency_dir=None):
        super().__init__(path,dependency_dir)
        pointer=lambda dtype:np.ctypeslib.ndpointer(dtype=dtype,flags='C_CONTIGUOUS')
        self.dll.kp_layer_host.argtypes=[pointer(t) for t in (np.int16,np.int16,np.int64,np.int8,np.int16,np.int32)]
    def layer(self,x,w,bias,shift,spec,relu):
        cfg=configuration(x,w,spec,relu)
        output=np.empty(spec['output_shape'],np.int16)
        status=self.dll.kp_layer_host(np.ascontiguousarray(x,dtype=np.int16),
            np.ascontiguousarray(w,dtype=np.int16),np.ascontiguousarray(bias,dtype=np.int64),
            np.ascontiguousarray(shift,dtype=np.int8),output,cfg)
        if status:raise RuntimeError('Layer C status '+str(status))
        self.mac_calls+=1
        return output

def pack_parameters(graph,weights):
    arrays={key:[] for key in ('kernel','bias','shift')};offsets={};sizes=dict.fromkeys(arrays,0)
    for spec in graph:
        if spec['kind'] not in ('Conv2D','DepthwiseConv2D','Dense'):continue
        name=spec['name']
        if name in offsets:raise ValueError('Duplicate layer name')
        offsets[name]={}
        for key in arrays:
            value=weights[name+'_'+key].reshape(-1)
            offsets[name][key]=sizes[key];sizes[key]+=value.size;arrays[key].append(value)
    if not offsets:raise ValueError('No layer parameters')
    return {key:np.ascontiguousarray(np.concatenate(parts)) for key,parts in arrays.items()},offsets

class LayerHardwareBackend(HardwareBackend):
    name='PL_whole_layer_fused_PS_schedule_no_CPU_neural_fallback'
    def __init__(self,bit,register_map,timeout=30):
        from pynq import Overlay,allocate
        self.overlay=Overlay(str(bit),download=False)
        self.regs=json.loads(Path(register_map).read_text())
        if self.regs.get('architecture')!='whole_layer_v2':raise ValueError('Wrong layer ABI')
        self.mac=getattr(self.overlay,self.regs['mac']['instance'])
        self.vec=getattr(self.overlay,self.regs['vector']['instance'])
        self.timeout=timeout;self.buffers=[]
        def alloc(n,dtype):
            result=allocate(shape=(n,),dtype=dtype);self.buffers.append(result);return result
        self._alloc=alloc
        self.la=alloc(802816,np.int16)
        self.config=alloc(16,np.int32)
        self.va,self.vb,self.vo=alloc(262144,np.int16),alloc(4096,np.int16),alloc(4096,np.int16)
        self.mac_calls=self.vector_calls=0
        self.profile=dict(input_copy_flush_s=0.,launch_wait_s=0.,output_invalidate_view_s=0.,vector_wall_s=0.)
        self.traffic=dict(input_bytes_copied=0,resident_input_layers=0)
    def prepare(self,graph,weights):
        if hasattr(self,'resident'):raise RuntimeError('Parameters are immutable; create a new backend to replace them')
        packed,offsets=pack_parameters(graph,weights)
        pools={}
        for key,data in packed.items():
            pool=self._alloc(data.size,data.dtype);pool[:]=data;pool.flush();pools[key]=pool
        self.resident={name:{key:int(pools[key].physical_address)+offset*packed[key].dtype.itemsize
            for key,offset in fields.items()} for name,fields in offsets.items()}
        self.outputs={spec['name']:self._alloc(int(np.prod(spec['output_shape'])),np.int16)
            for spec in graph if spec['kind'] in ('Conv2D','DepthwiseConv2D','Dense')}
        self.output_addresses={int(buffer.physical_address) for buffer in self.outputs.values()}
    def layer(self,x,w,bias,shift,spec,relu):
        cfg=configuration(x,w,spec,relu)
        destination=self.outputs[spec['name']]
        if x.size>self.la.size or np.prod(spec['output_shape'])>destination.size:
            raise ValueError('Layer exceeds hardware buffers')
        pointers=self.resident[spec['name']]
        tick=time.perf_counter()
        source_address=getattr(x,'physical_address',None)
        if source_address in self.output_addresses and x.flags.c_contiguous:
            self.traffic['resident_input_layers']+=1
        else:
            self.la[:x.size]=x.reshape(-1);self.la[:x.size].flush()
            source_address=self.la.physical_address;self.traffic['input_bytes_copied']+=x.nbytes
        self.config[:]=cfg;self.config.flush()
        self.profile['input_copy_flush_s']+=time.perf_counter()-tick
        tick=time.perf_counter()
        self._call(self.mac,self.regs['mac']['registers'],dict(a=source_address,
            b=pointers['kernel'],bias=pointers['bias'],shift=pointers['shift'],
            out_r=destination.physical_address,config_r=self.config.physical_address))
        self.profile['launch_wait_s']+=time.perf_counter()-tick
        tick=time.perf_counter();destination.invalidate()
        # Dedicated output per layer preserves residual branches and repeatability.
        result=destination.reshape(spec['output_shape'])
        self.profile['output_invalidate_view_s']+=time.perf_counter()-tick
        self.mac_calls+=1
        return result
    def vector(self,*args,**kwargs):
        tick=time.perf_counter()
        result=super().vector(*args,**kwargs)
        self.profile['vector_wall_s']+=time.perf_counter()-tick
        return result
