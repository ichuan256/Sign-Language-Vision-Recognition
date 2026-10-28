"""Bounded, strictly checked single-initialization sensor experiments; no download."""
import argparse,hashlib,json,math,sys,time
from pathlib import Path
BASE=Path('/home/xilinx/jupyter_notebooks/ov5640_snapshot')
sys.path.insert(0,str(BASE))
import capture as c
READ_REGS=[0x300a,0x300b,*range(0x3017,0x301f),0x3034,0x3035,0x3036,0x3037,0x3108,0x3808,0x3809,0x380a,0x380b,0x380c,0x380d,0x380e,0x380f,0x3824,0x4300,0x501f,0x4740,0x4741,0x4745,0x503d]
ALLOWED={0x3017,0x3018,0x301a,0x301b,0x301d,0x301e,0x3035,0x3108,0x3824,0x4300,0x501f,0x4740,0x4741,0x4745,0x503d}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--boot',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--frames',type=int,default=3);p.add_argument('--seconds',type=float,default=0)
    p.add_argument('--flags',type=lambda v:int(v,0),default=0x200)
    p.add_argument('--set',action='append',default=[]);p.add_argument('--no-maintenance',action='store_true')
    a=p.parse_args()
    if a.frames<1 or not math.isfinite(a.seconds) or a.seconds<0 or a.flags not in (0,0x100,0x200,0x300):raise ValueError('Invalid limits/flags')
    edits=[]
    for spec in a.set:
        reg,value=(int(v,16) for v in spec.split('='))
        if reg not in ALLOWED or not 0<=value<=255:raise ValueError('Unsupported controlled register edit')
        edits.append((reg,value))
    if a.no_maintenance and edits:raise ValueError('Edits require maintenance')
    for f in ['/proc/sys/kernel/random/boot_id','/run/ov5640_snapshot_download_attempted']:
        if Path(f).read_text().strip()!=a.boot:raise RuntimeError('Boot/load marker mismatch')
    manifest,files=c.verify_manifest(BASE/'release/release_manifest.json')
    if not a.no_maintenance and manifest['design'].get('post_init_sccb_version')!=1:raise RuntimeError('Post-init maintenance firmware required')
    from pynq import Overlay,MMIO,Clocks,allocate
    ol=Overlay(str(files['bit']),download=False);c.verify_overlay(ol)
    if abs(Clocks.fclk0_mhz-100)>1:raise RuntimeError('FCLK mismatch')
    a.output.mkdir(parents=True,exist_ok=False)
    result=dict(boot_id=a.boot,firmware=manifest['files'],flags=hex(a.flags),initializations=0,recoveries=0,attempts=0,valid_frames=0,errors=0,passed=False,downloaded=False)
    ctrl=MMIO(c.CONTROL_BASE,65536);dma=MMIO(c.DMA_BASE,65536)
    buf=None;owned=False;arm=0;begin=time.monotonic();start_capture=None;last=None;middle=False
    def wait(fn,t,label):c.wait_until(fn,t,label,time.monotonic,time.sleep)
    def save(raw,label):
        (a.output/(label+'.raw')).write_bytes(raw)
        (a.output/(label+'.png')).write_bytes(c.png_bytes(raw))
    def snapshot():
        return dict(camera_status=hex(ctrl.read(8)),control=hex(ctrl.read(0)),dma={hex(o):hex(dma.read(o)) for o in [c.CR,c.SR,c.ADDR,c.ADDR_MSB,c.LENGTH]},dvp=c.read_frame_diagnostics(ctrl))
    try:
        ctrl.write(4,0);ctrl.write(12,0xffffffff);ctrl.write(0,0);time.sleep(.002)
        c.quiesce_dma(dma,2,time.monotonic,time.sleep)
        ctrl.write(0,1|a.flags);time.sleep(.002);ctrl.write(0,3|a.flags);time.sleep(.001);ctrl.write(0,1|a.flags)
        result['initializations']+=1
        def initialized():
            s=ctrl.read(8)
            if s&4:raise c.CaptureError('Initialization failed '+hex(s),c.read_diagnostics(ctrl))
            return s&2 and not s&1
        wait(initialized,30,'initialization')
        result['initialization_seconds']=time.monotonic()-begin
        if not a.no_maintenance:
            ctrl.write(0,0x3b);time.sleep(.003);toggle=0
            def transfer(reg,value=None):
                nonlocal toggle
                toggle^=1
                ctrl.write(0,(reg<<16)|((value or 0)<<8)|((value is None)<<7)|(toggle<<6)|0x3b)
                time.sleep(.001)
                def done():
                    s=ctrl.read(8)
                    if s>>16!=0xd167:raise RuntimeError('Maintenance signature')
                    return s&0x200 and not s&0x100
                wait(done,.2,'SCCB transaction')
                return ctrl.read(8)&255
            result['registers_before']={hex(r):hex(transfer(r)) for r in READ_REGS}
            result['edits']=[]
            for reg,value in edits:
                before=transfer(reg);transfer(reg,value);actual=transfer(reg)
                result['edits'].append(dict(address=hex(reg),before=hex(before),written=hex(value),actual=hex(actual)))
                if actual!=value:raise RuntimeError('Controlled edit readback mismatch')
            result['registers_after']={hex(r):hex(transfer(r)) for r in READ_REGS}
            ctrl.write(0,1|a.flags);time.sleep(.01)
            s=ctrl.read(8)
            if not s&2 or s&5:raise RuntimeError('Initialization lost after maintenance '+hex(s))
        initial=ctrl.read(8);wait(lambda:(ctrl.read(8)^initial)&0x10000,1,'PCLK heartbeat');time.sleep(.5)
        buf=allocate(shape=(c.FRAME_BYTES,),dtype='u1');address=int(buf.physical_address)
        if address%8 or address<0x100000 or address+c.FRAME_BYTES>0x20000000:raise RuntimeError('Unsafe buffer')
        result['physical_address']=address;start_capture=time.monotonic()
        with (a.output/'attempts.jsonl').open('x') as log:
            while result['valid_frames']<a.frames or time.monotonic()-start_capture<a.seconds:
                n=result['attempts'];result['attempts']+=1;t=time.monotonic();row=dict(index=n,elapsed=t-start_capture,valid=False)
                try:
                    buf.flush();dma.write(c.SR,0x7000);dma.write(c.CR,1)
                    wait(lambda:not dma.read(c.SR)&1,2,'DMA running')
                    dma.write(c.ADDR,address);dma.write(c.ADDR_MSB,0);owned=True;dma.write(c.LENGTH,c.FRAME_BYTES)
                    arm^=4;ctrl.write(0,1|a.flags|arm);seen=False
                    def complete():
                        nonlocal seen
                        s=ctrl.read(8);d=dma.read(c.SR)
                        if s&0x64 or d&0x770:
                            time.sleep(.002)
                            raise c.CaptureError('Capture/DMA error '+hex(s)+' '+hex(d),snapshot())
                        seen|=bool(s&8)
                        return seen and s&16 and d&2 and d&0x1000
                    wait(complete,5,'strict frame and DMA completion')
                    row.update(camera_status=hex(ctrl.read(8)),dma_status=hex(dma.read(c.SR)),received_bytes=dma.read(c.LENGTH))
                    if row['received_bytes']!=c.FRAME_BYTES:raise RuntimeError('Wrong byte count')
                    c.quiesce_dma(dma,2,time.monotonic,time.sleep);owned=False;buf.invalidate();raw=memoryview(buf).tobytes()
                    if len(raw)!=c.FRAME_BYTES:raise RuntimeError('Wrong buffer length')
                    row.update(valid=True,sha256=hashlib.sha256(raw).hexdigest(),seconds=time.monotonic()-t)
                    result['valid_frames']+=1;last=raw
                    if n==0:save(raw,'start')
                    if not middle and a.seconds and time.monotonic()-start_capture>=a.seconds/2:save(raw,'middle');middle=True
                    if not a.seconds and a.frames<=10:save(raw,'frame_%03d'%n)
                    if n%100==0:print(json.dumps(row),flush=True)
                except BaseException as exc:
                    result['errors']+=1;row.update(error=str(exc),diagnostics=getattr(exc,'diagnostics',None));raise
                finally:
                    log.write(json.dumps(row)+'\n');log.flush()
        result['capture_seconds']=time.monotonic()-start_capture
        result['passed']=result['errors']==0 and result['valid_frames']>=a.frames and result['capture_seconds']>=a.seconds
        save(last,'end')
    except BaseException as exc:
        result.update(error=str(exc),diagnostics=getattr(exc,'diagnostics',None))
        if result['errors']==0:result['errors']+=1
        try:result['failure_snapshot']=snapshot()
        except Exception as e:result['snapshot_error']=str(e)
    finally:
        if owned:
            try:c.quiesce_dma(dma,2,time.monotonic,time.sleep);owned=False
            except BaseException as exc:result['cleanup_error']=str(exc)
        result['dma_shutdown_confirmed']=not owned
        if not owned:
            if buf is not None:buf.freebuffer()
            ctrl.write(0,0);result['camera_reset_after_probe']=True
        result['seconds']=time.monotonic()-begin
        result['capture_fps']=result['valid_frames']/result['capture_seconds'] if result.get('capture_seconds') else None
        (a.output/'results.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2),flush=True)
        if owned:
            print('DMA shutdown unconfirmed: retaining buffer and process',flush=True)
            while True:time.sleep(1)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
