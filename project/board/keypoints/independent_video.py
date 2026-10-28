"""SD replay, board PS hand localization, actual PL pose and local HDMI.

No network input, cached landmarks, training, or FPGA reconfiguration. The PS
full teacher supplies canonical crops; the existing lite PL graph supplies the
displayed pose. This is not the proposed full-teacher subgraph migration.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

EDGES=[(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),
       (9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),
       (13,17),(0,17),(17,18),(18,19),(19,20)]


class MixedDraw:
    """DroidSansFallback contains CJK but not Latin/digits on this image."""
    def __init__(self,image):
        self.draw=ImageDraw.Draw(image);self.latin={}

    def text(self,xy,text,font,fill):
        size=font.size
        if size not in self.latin:
            self.latin[size]=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
        x,y=xy
        text=text.replace('→',' / ')
        # Separate fonts at character boundaries; font advances retain spacing.
        for char in text:
            selected=self.latin[size] if ord(char)<256 else font
            self.draw.text((x,y),char,font=selected,fill=fill)
            x+=selected.getlength(char) if hasattr(selected,'getlength') else selected.getsize(char)[0]


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--pl-work',type=Path,required=True)
    p.add_argument('--teacher-work',type=Path,required=True)
    p.add_argument('--owner-pid',type=int,required=True)
    a=p.parse_args();stage=a.stage
    sys.path[:0]=[str(stage),str(a.pl_work),str(a.teacher_work)]
    import run_teacher
    from teacher_geometry_fast import decode_palms
    from prepare_hand_rois import canonical_roi
    from hand_runtime import HandGraph
    from hand_layer_runtime import LayerHardwareBackend
    from pynq import MMIO
    run_teacher.decode_palms=decode_palms
    release=json.loads((a.pl_work/'manifest.json').read_text())
    for suffix in ('bit','hwh'):
        if digest('/home/xilinx/kws_hdmi.'+suffix)!=release['artifacts'][suffix]['sha256']:
            raise RuntimeError('Firmware pair mismatch; no MMIO allowed')
    if Path('/proc/sys/kernel/random/boot_id').read_text().strip()==release['board_boot_id_before_deployment']:
        raise RuntimeError('Cold initialization missing')
    expected=json.loads((stage/'teacher_hashes.json').read_text())
    for name,sha in expected.items():
        if digest(a.teacher_work/name)!=sha:raise RuntimeError('Teacher changed: '+name)
    meta=json.loads((stage/'video.json').read_text())
    if digest(stage/'frames.rgb')!=meta['raw_sha256']:raise RuntimeError('SD media SHA mismatch')
    frames=np.memmap(stage/'frames.rgb',dtype=np.uint8,mode='r',
        shape=(meta['frames'],meta['height'],meta['width'],3))
    output=stage/('run_'+time.strftime('%Y%m%d_%H%M%S'));output.mkdir()
    (stage/'current_run.txt').write_text(str(output))
    (stage/'daemon.pid').write_text(str(os.getpid()))
    stop=threading.Event();lock=threading.Lock();latest=None;error=None;count=0;attempts=0
    started=time.monotonic();ps_times=[];pl_times=[];inputs=set();outputs=set()
    def request_stop(*_):stop.set()
    signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGINT,request_stop)
    def source_id():return int((time.monotonic()-started)*meta['fps'])
    def infer():
        nonlocal latest,error,count,attempts
        backend=None;pipeline=None;hardware_safe=True
        try:
            pipeline=run_teacher.HandsPipeline(a.teacher_work,2)
            backend=LayerHardwareBackend(Path('/home/xilinx/kws_hdmi.bit'),a.pl_work/'registers.json')
            graph=HandGraph(a.pl_work/'model',backend)
            fraction=next(s['fraction'] for s in graph.graph if s['kind']=='InputLayer')
            with (output/'results.jsonl').open('x') as log:
                while not stop.is_set():
                    frame_id=source_id();index=frame_id%len(frames);rgb=frames[index].copy()
                    begin=time.monotonic();hands,metrics=pipeline.process(rgb);ps_s=time.monotonic()-begin
                    attempts+=1
                    if not hands:
                        stop.wait(.05);continue
                    hand=max(hands,key=lambda h:h['presence'])
                    try:crop,inverse=canonical_roi(rgb[...,::-1],hand['points'])
                    except ValueError:continue
                    codes=np.clip(np.rint(np.ldexp(crop,fraction)),-32768,32767).astype('<i2')
                    backend.mac_calls=backend.vector_calls=0
                    try:coordinates,pl_metrics=graph.run(codes,verbose=False)
                    except TimeoutError:
                        hardware_safe=False;raise
                    if len(coordinates)!=64 or not np.isfinite(coordinates).all():raise RuntimeError('Invalid PL output')
                    if (pl_metrics['mac_calls'],pl_metrics['vector_calls'])!=(49,13):raise RuntimeError('PL call counts changed')
                    count+=1;ps_times.append(ps_s);pl_times.append(pl_metrics['elapsed_s'])
                    input_sha=digest_bytes(codes.tobytes());output_sha=digest_bytes(coordinates.tobytes())
                    inputs.add(input_sha);outputs.add(output_sha)
                    record=dict(sequence=count,source_frame=frame_id,sd_frame=index,PS_localization_s=ps_s,
                        PL_forward_s=pl_metrics['elapsed_s'],mac_calls=49,vector_calls=13,
                        outputs=coordinates.tolist(),input_sha256=input_sha,output_sha256=output_sha,
                        pc_inference=False,pc_ROI=False,PL_CPU_neural_fallback=False,
                        PS_locator='full teacher palm + landmark; pose display from lite PL graph only')
                    log.write(json.dumps(record)+'\n');log.flush()
                    with lock:latest=dict(record=record,crop=(crop*255).astype(np.uint8),captured=begin)
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
            print(error,flush=True)
        finally:
            if backend and hardware_safe:backend.close()
            if pipeline:pipeline.close()
    writer=run_teacher.HdmiWriter(a.owner_pid)
    # Match the established HDMI receiver's RGB matrix, then copy RGB directly.
    color=MMIO(0x40010000,65536)
    for i,value in enumerate([0,0,256,0,256,0,256,0,0,0,0,0]):color.write(0x10+i*8,value)
    font=ImageFont.truetype('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',23)
    large=ImageFont.truetype('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',31)
    worker=threading.Thread(target=infer);worker.start();rendered=0;deadline=time.monotonic()
    base=dict(mode=3,scope='SD -> board PS full teacher ROI -> existing lite PL pose -> HDMI',
        network_required=False,PC_required=False,FPGA_reprogrammed=False,
        new_full_teacher_PL_migration=False,video_fps=meta['fps'],raw_sha256=meta['raw_sha256'],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),display_owner=a.owner_pid)
    atomic_json(output/'configuration.json',base)
    try:
        while not stop.is_set():
            fid=source_id();index=fid%len(frames);rgb=frames[index]
            clip=next(c for c in meta['clips'] if c['first_frame']<=index<c['end_frame'])
            canvas=np.full((720,1280,3),20,np.uint8)
            canvas[140:545,15:735]=cv2.resize(rgb,(720,405))
            with lock:result=latest
            if result:
                crop=result['crop'].copy();points=np.asarray(result['record']['outputs'][:63]).reshape(21,3)[:,:2]
                points=np.clip(np.rint(points),-1000,1000).astype(int)
                for i,j in EDGES:cv2.line(crop,tuple(points[i]),tuple(points[j]),(0,255,80),2)
                for point in points:cv2.circle(crop,tuple(point),3,(255,210,0),-1)
                canvas[140:588,790:1238]=cv2.resize(crop,(448,448))
            image=Image.fromarray(canvas);draw=MixedDraw(image)
            draw.text((20,15),'模式三  板端独立运行',font=large,fill=(255,220,60))
            draw.text((20,65),'SD本地视频 → PS手部定位 → PL关键点 → HDMI直接输出',font=font,fill='white')
            draw.text((20,105),'连续视频：'+clip['label'],font=font,fill='white')
            draw.text((790,105),'PL实际输入与21点结果',font=font,fill='white')
            elapsed=time.monotonic()-started
            text='视频帧 %d | 视频目标 %d fps | 新关键点 %.2f 次/秒'%(fid,meta['fps'],count/max(elapsed,.001))
            draw.text((20,610),text,font=font,fill='white')
            if result:
                r=result['record']
                draw.text((20,647),'结果 %d | 来源帧 %d | 帧龄 %.1fs | PS %.0fms | PL %.0fms'%(
                    r['sequence'],r['source_frame'],time.monotonic()-result['captured'],r['PS_localization_s']*1000,r['PL_forward_s']*1000),font=font,fill=(130,255,160))
            else:draw.text((20,647),'正在板端定位与推理，请稍候…',font=font,fill='white')
            if error:draw.text((20,683),'推理异常，已保留最后结果；请检查运行日志',font=font,fill=(255,100,80))
            writer.check();writer.frame.array[:]=np.asarray(image).reshape(-1).view('<u4');rendered+=1
            if rendered%10==0:
                state=dict(base,active=True,video_frame=fid,rendered=rendered,results=count,attempts=attempts,
                    unique_PL_inputs=len(inputs),unique_PL_outputs=len(outputs),result_hz=count/max(elapsed,.001),
                    elapsed_s=elapsed,error=error,last_result=result['record'] if result else None)
                atomic_json(output/'state.json',state);image.save(output/'latest.jpg')
            deadline+=1/meta['fps'];stop.wait(max(0,deadline-time.monotonic()))
            if deadline<time.monotonic()-.5:deadline=time.monotonic()
    finally:
        stop.set();worker.join()  # Finish any in-flight kernel before releasing CMA.
        atomic_json(output/'report.json',dict(base,active=False,results=count,rendered=rendered,error=error,
            PS_localization_median_ms=float(np.median(ps_times)*1000) if ps_times else None,
            PL_forward_median_ms=float(np.median(pl_times)*1000) if pl_times else None))


def digest_bytes(data):return hashlib.sha256(data).hexdigest()


if __name__=='__main__':main()
