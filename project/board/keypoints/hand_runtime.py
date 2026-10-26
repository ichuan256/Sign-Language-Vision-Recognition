"""Integer hand graph scheduler. Hardware mode has no CPU neural fallback.

PS performs indexing/packing, launches PL kernels, and decodes output scales.
The NumPy and DLL backends are explicitly named host-validation backends only.
"""
import ctypes
import json
import os
from pathlib import Path
import time
from collections import Counter

import numpy as np

ADD,RELU,MAX,MEAN49,SIGMOID,SCALE = range(6)


def _patches(x, kh, kw, strides, padding, output_hw, fill=0):
    if x.shape[0]!=1:
        raise ValueError('Only one ROI per call')
    image = np.ascontiguousarray(x[0],dtype=np.int16)
    h,w,c = image.shape
    oh,ow = output_hw
    sy,sx = strides
    if padding=='same':
        py,px = max(0,(oh-1)*sy+kh-h),max(0,(ow-1)*sx+kw-w)
        image = np.pad(image,((py//2,py-py//2),(px//2,px-px//2),(0,0)),constant_values=fill)
    elif padding!='valid':
        raise ValueError('Unknown padding')
    if (oh-1)*sy+kh>image.shape[0] or (ow-1)*sx+kw>image.shape[1]:
        raise ValueError('Patch exceeds padded input')
    s0,s1,s2 = image.strides
    return np.lib.stride_tricks.as_strided(image,shape=(oh,ow,kh,kw,c),
        strides=(s0*sy,s1*sx,s0,s1,s2),writeable=False).reshape(oh*ow,kh*kw,c)


class DLLBackend:
    name = 'host_compiled_HLS_C_not_PL'
    def __init__(self,path,dependency_dir=None):
        self._dll_directory = os.add_dll_directory(str(dependency_dir)) if dependency_dir is not None and os.name=='nt' else None
        self.dll = ctypes.CDLL(str(Path(path).resolve()))
        p16 = np.ctypeslib.ndpointer(dtype=np.int16,flags='C_CONTIGUOUS')
        p64 = np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS')
        p8 = np.ctypeslib.ndpointer(dtype=np.int8,flags='C_CONTIGUOUS')
        self.dll.kp_gemm_host.argtypes = [p16,p16,p64,p8,p16,*([ctypes.c_int]*3)]
        self.dll.kp_vector_host.argtypes = [p16,p16,p16,*([ctypes.c_int]*7)]
        self.mac_calls = self.vector_calls = 0

    def gemm(self,a,b,bias,shift,columns):
        a,b = np.ascontiguousarray(a,dtype=np.int16),np.ascontiguousarray(b,dtype=np.int16)
        out = np.empty((a.shape[0],columns),np.int16)
        status = self.dll.kp_gemm_host(a,b,np.ascontiguousarray(bias,dtype=np.int64),
            np.ascontiguousarray(shift,dtype=np.int8),out,a.shape[0],columns,a.shape[1])
        if status:
            raise RuntimeError('HLS MAC status '+str(status))
        self.mac_calls += 1
        return out

    def vector(self,a,b,count,op,shift,alpha=0,beta=0,limit=-1,kernel=1):
        a = np.ascontiguousarray(a,dtype=np.int16).reshape(-1)
        b = np.zeros(count,np.int16) if b is None else np.ascontiguousarray(b,dtype=np.int16).reshape(-1)
        out = np.empty(count,np.int16)
        status = self.dll.kp_vector_host(a,b,out,count,op,shift,alpha,beta,limit,kernel)
        if status:
            raise RuntimeError('HLS vector status '+str(status))
        self.vector_calls += 1
        return out


class HardwareBackend:
    name = 'PL_gemm_and_vector_PS_schedule_no_CPU_neural_fallback'
    def __init__(self, bit, register_map, timeout=10):
        from pynq import Overlay,allocate
        self.overlay = Overlay(str(bit),download=False)
        self.regs = json.loads(Path(register_map).read_text())
        self.mac = getattr(self.overlay,self.regs['mac']['instance'])
        self.vec = getattr(self.overlay,self.regs['vector']['instance'])
        self.timeout = timeout
        self.buffers = []
        def alloc(n,dtype):
            result = allocate(shape=(n,),dtype=dtype)
            self.buffers.append(result)
            return result
        self.ma,self.mb = alloc(65536,np.int16),alloc(16384,np.int16)
        self.bias,self.shifts,self.mo = alloc(16,np.int64),alloc(16,np.int8),alloc(1024,np.int16)
        self.va,self.vb,self.vo = alloc(262144,np.int16),alloc(4096,np.int16),alloc(4096,np.int16)
        self.mac_calls = self.vector_calls = 0
        self._last_weights = None

    def _call(self,ip,regs,values):
        for name,value in values.items():
            info = regs[name]
            value = int(value)
            if value<0:
                value &= (1<<info['bits'])-1
            for word in range((info['bits']+31)//32):
                ip.write(info['offset']+word*4,(value>>(32*word))&0xffffffff)
        ip.write(0,1)
        start = time.monotonic()
        while not (ip.read(0)&2):
            if time.monotonic()-start>self.timeout:
                raise TimeoutError('PL kernel stalled; no software fallback')
        status = ip.read(regs['ap_return']['offset'])
        if status:
            raise RuntimeError('PL kernel status '+str(status))

    def gemm(self,a,b,bias,shift,columns):
        rows,depth = a.shape
        if not 1<=rows<=64 or not 1<=depth<=1024 or not 1<=columns<=16:
            raise ValueError('MAC tile exceeds hardware bounds')
        self.ma[:a.size] = a.reshape(-1)
        self.ma.flush()
        previous = self._last_weights
        if previous is None or not all(x is y for x,y in zip(previous,(b,bias,shift))):
            self.mb[:b.size] = b.reshape(-1)
            self.bias[:] = bias
            self.shifts[:] = shift
            self.mb.flush(); self.bias.flush(); self.shifts.flush()
            self._last_weights = (b,bias,shift)
        self._call(self.mac,self.regs['mac']['registers'],dict(
            a=self.ma.physical_address,b=self.mb.physical_address,bias=self.bias.physical_address,
            shift=self.shifts.physical_address,out_r=self.mo.physical_address,
            rows=rows,columns=columns,depth=depth))
        self.mo.invalidate()
        self.mac_calls += 1
        return np.array(self.mo[:rows*columns]).reshape(rows,columns)

    def vector(self,a,b,count,op,shift,alpha=0,beta=0,limit=-1,kernel=1):
        a = np.asarray(a,dtype=np.int16).reshape(-1)
        if count>getattr(self,'vector_capacity',4096) or a.size>262144:
            raise ValueError('Vector tile exceeds hardware bounds')
        self.va[:a.size] = a
        self.va[:a.size].flush()
        if b is not None:
            b = np.asarray(b,dtype=np.int16).reshape(-1)
            self.vb[:b.size] = b
            self.vb[:b.size].flush()
        self._call(self.vec,self.regs['vector']['registers'],dict(
            a=self.va.physical_address,b=self.vb.physical_address,out_r=self.vo.physical_address,
            count=count,operation=op,shift=shift,alpha=alpha,beta=beta,limit=limit,kernel=kernel))
        self.vo[:count].invalidate()
        self.vector_calls += 1
        return np.array(self.vo[:count])

    def close(self):
        for buffer in self.buffers:
            buffer.freebuffer()


class HandGraph:
    def __init__(self,directory,backend):
        directory = Path(directory)
        self.graph = json.loads((directory/'graph.json').read_text())
        with np.load(directory/'weights.npz',allow_pickle=False) as data:
            self.weights = {k:data[k] for k in data.files}
        self.backend = backend
        self.fusions = {}
        if hasattr(backend,'layer'):
            consumers=Counter(k for spec in self.graph for k in spec['inputs'])
            for first,second in zip(self.graph,self.graph[1:]):
                if (first['kind'] in ('Conv2D','DepthwiseConv2D','Dense') and
                    second['kind']=='ReLU' and second['inputs']==[first['output']] and
                    consumers[first['output']]==1):
                    self.fusions[first['name']]=second
        self.fused_names={s['name'] for s in self.fusions.values()}
        if hasattr(backend,'prepare'):
            backend.prepare(self.graph,self.weights)

    def _gemm(self,a,kernel,bias,shifts):
        rows,depth = a.shape
        columns = kernel.shape[1]
        result = np.empty((rows,columns),np.int16)
        for c in range(0,columns,16):
            n = min(16,columns-c)
            b = np.zeros((depth,16),np.int16)
            b[:,:n] = kernel[:,c:c+n]
            bp,sp = np.zeros(16,np.int64),np.zeros(16,np.int8)
            bp[:n],sp[:n] = bias[c:c+n],shifts[c:c+n]
            for r in range(0,rows,64):
                result[r:r+64,c:c+n] = self.backend.gemm(a[r:r+64],b,bp,sp,n)
        return result

    def _vector(self,a,b,op,shift,alpha=0,beta=0,limit=-1,kernel=1):
        a = np.asarray(a,dtype=np.int16).reshape(-1,kernel)
        b = None if b is None else np.asarray(b,dtype=np.int16).reshape(-1)
        output = np.empty(len(a),np.int16)
        capacity=getattr(self.backend,'vector_capacity',4096)
        for start in range(0,len(a),capacity):
            n = min(capacity,len(a)-start)
            output[start:start+n] = self.backend.vector(a[start:start+n],
                None if b is None else b[start:start+n],n,op,shift,alpha,beta,limit,kernel)
        return output

    def run(self,roi_codes,verbose=True):
        values,fractions = {},{}
        start = time.perf_counter()
        trace = []
        for s in self.graph:
            name,kind = s['name'],s['kind']
            tick = time.perf_counter()
            if kind=='InputLayer':
                y = np.asarray(roi_codes,dtype=np.int16).reshape(s['output_shape'])
            elif kind=='Concatenate':
                if hasattr(self.backend,'sync_for_cpu'):
                    for key in s['inputs']:self.backend.sync_for_cpu(values[key])
                result = np.concatenate([np.ldexp(values[k].astype(np.float64),-fractions[k]) for k in s['inputs']],axis=-1)[0]
                return result,dict(elapsed_s=time.perf_counter()-start,backend=self.backend.name,
                    mac_calls=self.backend.mac_calls,vector_calls=self.backend.vector_calls,trace=trace)
            else:
                xs = [values[k] for k in s['inputs']]
                x = xs[0]
                if (hasattr(self.backend,'sync_for_cpu') and
                    kind not in ('Conv2D','DepthwiseConv2D','Dense') and name not in self.fused_names):
                    for array in xs:self.backend.sync_for_cpu(array)
                if kind in ('Conv2D','DepthwiseConv2D','Dense'):
                    w,bias,shift = (self.weights[name+suffix] for suffix in ('_kernel','_bias','_shift'))
                    if hasattr(self.backend,'layer'):
                        y=self.backend.layer(x,w,bias,shift,s,self.fusions.get(name)).reshape(s['output_shape'])
                    elif kind=='Dense':
                        y = self._gemm(x.reshape(1,-1),w,bias,shift)
                    else:
                        if s['dilation']!=[1,1]:
                            raise NotImplementedError('Dilation')
                        kh,kw = w.shape[:2]
                        patches = _patches(x,kh,kw,s['strides'],s['padding'],s['output_shape'][1:3])
                        if kind=='Conv2D':
                            y = self._gemm(patches.reshape(len(patches),-1),w.reshape(-1,w.shape[-1]),bias,shift)
                        else:
                            if w.shape[-1]!=1:
                                raise NotImplementedError('Depthwise multiplier != 1')
                            channels = x.shape[-1]
                            y = np.empty((len(patches),channels),np.int16)
                            for c in range(0,channels,16):
                                n = min(16,channels-c)
                                a = patches[:,:,c:c+n].reshape(len(patches),kh*kw*n)
                                sparse = np.zeros((kh*kw*n,n),np.int16)
                                for j in range(n):
                                    sparse[j::n,j] = w[:,:,c+j,0].reshape(-1)
                                y[:,c:c+n] = self._gemm(a,sparse,bias[c:c+n],shift[c:c+n])
                        y = y.reshape(s['output_shape'])
                elif kind=='Add':
                    y = self._vector(x,xs[1],ADD,s['rescale_shift'],s['align_a'],s['align_b']).reshape(s['output_shape'])
                elif kind=='ReLU':
                    y = x if name in self.fused_names else self._vector(x,None,RELU,s['rescale_shift'],limit=s['relu_limit']).reshape(s['output_shape'])
                elif kind=='MaxPooling2D':
                    kh,kw = s['pool_size']
                    p = _patches(x,kh,kw,s['strides'],s['padding'],s['output_shape'][1:3],fill=-32768)
                    y = self._vector(p.transpose(0,2,1),None,MAX,s['rescale_shift'],kernel=kh*kw).reshape(s['output_shape'])
                elif kind=='GlobalAveragePooling2D':
                    if x.shape[1:3]!=(7,7):
                        raise ValueError('Only model mean49 was validated')
                    p = x[0].transpose(2,0,1).reshape(x.shape[-1],49)
                    y = self._vector(p,None,MEAN49,s['rescale_shift'],kernel=49).reshape(s['output_shape'])
                elif kind=='Flatten':
                    y = self._vector(x,None,SCALE,s['rescale_shift']).reshape(s['output_shape'])
                elif kind=='Activation':
                    y = self._vector(x,None,SIGMOID,s['sigmoid_index_shift'],alpha=s['sigmoid_output_shift']).reshape(s['output_shape'])
                else:
                    raise NotImplementedError(kind)
            values[s['output']] = y
            fractions[s['output']] = s['fraction']
            trace.append(dict(name=name,kind=kind,seconds=time.perf_counter()-tick,
                              mac_calls=self.backend.mac_calls,vector_calls=self.backend.vector_calls))
            if verbose:
                print(f'LAYER {name} {kind} {trace[-1]["seconds"]:.3f}s',flush=True)
        raise RuntimeError('No coordinate output')
