"""Graph packing/AXI control tests without PYNQ, TensorFlow, board or camera."""
import numpy as np
import pytest

from project.board.keypoints.hand_runtime import HardwareBackend,_patches
from project.scripts.keypoints.make_register_map import parse


def test_patch_lowering_same_stride_and_padding():
    x=np.arange(1*3*3*2,dtype=np.int16).reshape(1,3,3,2)
    patches=_patches(x,2,2,[2,2],'same',[2,2],fill=-32768)
    assert patches.shape==(4,4,2)
    assert np.array_equal(patches[0],x[0,:2,:2].reshape(4,2))
    assert np.array_equal(patches[-1,0],x[0,2,2])
    assert np.all(patches[-1,1:]==-32768)


def test_patch_bounds_rejects_unsafe_strides():
    with pytest.raises(ValueError):
        _patches(np.zeros((1,2,2,1),np.int16),3,3,[1,1],'valid',[2,2])


def test_axi_signed_register_and_64bit_pointer():
    class IP:
        def __init__(self):self.writes=[]
        def write(self,offset,value):self.writes.append((offset,value))
        def read(self,offset):return 2 if offset==0 else 0
    ip=IP()
    backend=object.__new__(HardwareBackend)
    backend.timeout=1
    registers={'a':{'offset':24,'bits':64},'shift':{'offset':76,'bits':32},
               'ap_return':{'offset':16,'bits':32}}
    backend._call(ip,registers,dict(a=0x123456789,shift=-2))
    assert ip.writes==[(24,0x23456789),(28,1),(76,0xfffffffe),(0,1)]


def test_axi_stall_raises_no_cpu_fallback(monkeypatch):
    import project.board.keypoints.hand_runtime as runtime
    class IP:
        def write(self,*args):pass
        def read(self,*args):return 0
    clock=iter([0,2])
    monkeypatch.setattr(runtime.time,'monotonic',lambda:next(clock))
    backend=object.__new__(HardwareBackend)
    backend.timeout=1
    with pytest.raises(TimeoutError,match='no software fallback'):
        backend._call(IP(),{'ap_return':{'offset':16,'bits':32}},{})


def test_parse_generated_register_header(tmp_path):
    path=tmp_path/'hw.h'
    path.write_text('#define XTEST_CONTROL_ADDR_AP_RETURN 0x10\n'
                    '#define XTEST_CONTROL_BITS_AP_RETURN 32\n'
                    '#define XTEST_CONTROL_ADDR_A_DATA 0x18\n'
                    '#define XTEST_CONTROL_BITS_A_DATA 64\n')
    result=parse(path,'XTEST')
    assert result['a']==dict(offset=24,bits=64)
