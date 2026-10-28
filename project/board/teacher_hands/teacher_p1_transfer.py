"""Measure PS copies/cache maintenance on real CMA; never start an accelerator."""
import argparse
import json
from pathlib import Path
import time

import numpy as np


def stats(values):
    return dict(count=len(values),mean=float(np.mean(values)),
                p50=float(np.percentile(values,50)),p95=float(np.percentile(values,95)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():
        raise ValueError('New output required')
    a.output.mkdir()
    report=dict(completed=False,scope='CMA_host_copy_and_cache_only_no_PL_AXImaster_transfer',
                iterations=100,activation_bytes_each=87808,allocated_buffers=0,requested_buffers=2,
                bitstream_loaded=False,register_access=False,accelerator_started=False,
                limitations=['Not a measured AXI/PL transfer or complete offload time',
                             'No delegate partition/scheduling cost; no weight or scratch AXI traffic',
                             'PYNQ Python calls measured; final C++ driver may differ'])
    buffers=[]
    try:
        from pynq import allocate
        from pynq.pl_server import Device
        device=Device.active_device
        memory_info=json.loads(device.device_info.memory)
        report['xrt_memory_info']=memory_info
        def memory_lists(value):
            if isinstance(value,dict):
                for key,item in value.items():
                    if key=='memories' and isinstance(item,list):
                        yield item
                    else:
                        yield from memory_lists(item)
            elif isinstance(value,list):
                for item in value:
                    yield from memory_lists(item)
        candidates=[]
        for memories in memory_lists(memory_info):
            for index,bank in enumerate(memories):
                if 'DDR' not in str(bank.get('type','')).upper():
                    continue
                if str(bank.get('enabled','')).lower() not in ('true','1'):
                    continue
                base=int(str(bank['base_address']),0)
                size=int(str(bank.get('range_bytes',bank.get('size_bytes','0'))),0)
                if base==0 and bank.get('tag')=='PSDDR' and size>=2*87808:
                    candidates.append(dict(idx=index,size=size,base_address=base,tag=bank.get('tag')))
        if len(candidates)!=1:
            raise RuntimeError('Cannot identify one enabled PS DDR bank from XRT memory topology')
        report['memory_target']=candidates[0]
        # Explicit XRT-reported bank: no Overlay construction, global-state
        # update, guessed physical pointer, bitstream load or MMIO access.
        target=device.get_memory(candidates[0])
        report['cacheable_requested']=True
        shape=(1,14,14,112)
        src=np.arange(np.prod(shape),dtype=np.float32).reshape(shape)
        dst=np.empty_like(src)
        for _ in range(2):
            buffers.append(allocate(shape=shape,dtype=np.float32,target=target,cacheable=True))
            report['allocated_buffers']=len(buffers)
        incoming,outgoing=buffers
        report['coherent']=[bool(b.coherent) for b in buffers]
        # Simulated output data is established once by PS. No PL writer exists.
        np.copyto(outgoing,src); outgoing.flush()
        rows=[]
        for iteration in range(105):
            t0=time.perf_counter_ns(); np.copyto(incoming,src)
            t1=time.perf_counter_ns(); incoming.flush()
            t2=time.perf_counter_ns(); outgoing.invalidate()
            t3=time.perf_counter_ns(); np.copyto(dst,outgoing)
            t4=time.perf_counter_ns()
            if not np.array_equal(dst,src) or not np.array_equal(incoming,src):
                raise RuntimeError('CMA copy roundtrip changed FP32 values')
            if iteration>=5:
                rows.append(dict(copy_in_ms=(t1-t0)/1e6,flush_ms=(t2-t1)/1e6,
                                 invalidate_ms=(t3-t2)/1e6,copy_out_ms=(t4-t3)/1e6,
                                 total_host_ms=(t4-t0)/1e6))
        report['timing']={k:stats([r[k] for r in rows]) for k in rows[0]}
        report['samples']=rows
        report['completed']=True
    except Exception as error:
        report['error']=str(error)
        raise
    finally:
        # No accelerator has been started or given these addresses.
        for buffer in reversed(buffers):
            buffer.freebuffer()
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CMA_COPY_COMPLETE',json.dumps(report['timing']),flush=True)


if __name__=='__main__':
    main()
