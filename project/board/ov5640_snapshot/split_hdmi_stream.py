"""OV1 local raw HDMI + exact PC annotated frame, separate latest-only paths."""
import argparse,base64,json,os,re,signal,sys,threading,time
from pathlib import Path
from urllib.request import build_opener,ProxyHandler
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import capture as c
import continuous_capture as cc
import hdmi_preview as hp


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--assume-cold-boot',action='store_true');p.add_argument('--seconds',type=int,default=3600)
    p.add_argument('--pc-url',default='http://127.0.0.1:18781/frame.jpg')
    p.add_argument('--triple',action='store_true',help='OV1 + teacher + live board-audio ASR/playback')
    p.add_argument('--audio-url',default='http://127.0.0.1:18765/panel.jpg')
    a=p.parse_args();metadata,files=c.verify_manifest(a.manifest);hp.verify_hdmi_manifest(metadata)
    cv2.setNumThreads(1)
    if a.triple and hasattr(os,'sched_setaffinity') and os.cpu_count()>=2:
        os.sched_setaffinity(0,{0})
    if not a.assume_cold_boot or not 10<=a.seconds<=86400:raise RuntimeError('Explicit cold-boot and bounded capture required')
    if a.triple and metadata['design'].get('audio_input') is not True:raise RuntimeError('Triple mode needs cold-loaded audio hardware')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    marker=json.loads(Path('/run/ov1_hdmi_boot.json').read_text())
    if marker.get('boot_id')!=boot or marker.get('bit_sha256')!=metadata['files']['bit']['sha256']:raise RuntimeError('OV1 HDMI cold marker mismatch')
    # Preserve protocol stdout before redirecting library diagnostics to stderr.
    wire=sys.stdout.buffer;sys.stdout=sys.stderr
    from pynq import Overlay,MMIO,Clocks,allocate
    overlay=Overlay(str(files['bit']),download=False);c.verify_overlay(overlay)
    if abs(float(Clocks.fclk0_mhz)-100)>1:raise RuntimeError('FCLK must already be 100MHz')
    lock=cc.ProcessLock('/run/lock/ov5640_continuous_capture.lock').acquire()
    if cc.competing_processes():raise RuntimeError('Another camera capture is active')
    a.output.mkdir(parents=True,exist_ok=False)
    stop=threading.Event();condition=threading.Condition();latest=None;pc=None;pc_error=None;audio=None;audio_error=None
    session=None;display=None;publisher=None;fetcher=None;capture_thread=None
    captured=0;sent=0;shown=0;raw_updates=0;started=time.monotonic()
    for number in (signal.SIGINT,signal.SIGTERM):signal.signal(number,lambda *_:stop.set())
    def emit(header,raw=b''):
        wire.write((json.dumps(header)+'\n').encode());wire.write(raw);wire.flush()
    def on_frame(buffer,row):
        nonlocal latest,captured
        if not row['image_safe']:return
        raw=memoryview(buffer)[:c.FRAME_BYTES].tobytes()
        captured+=1
        with condition:
            latest=dict(raw=raw,frame=captured,captured=time.monotonic());condition.notify_all()
    def capture():
        try:session.run()
        finally:stop.set()
    def publish():
        nonlocal sent
        previous=0
        try:
            while not stop.is_set():
                with condition:
                    condition.wait_for(lambda:stop.is_set() or (latest is not None and latest['frame']!=previous),timeout=.3)
                    item=latest
                if stop.is_set():break
                if item is None or item['frame']==previous:continue
                previous=item['frame']
                emit(dict(event='frame',frame=previous,bytes=len(item['raw']),width=1280,height=720,format='RGB565_LE',
                    board_capture_monotonic_s=item['captured'],dma_shutdown_confirmed=True),item['raw'])
                sent+=1;stop.wait(.25)  # latest frame only, at most 4 Hz for the PC path
        except (BrokenPipeError,OSError):stop.set()
    def fetch():
        nonlocal pc,pc_error
        opener=build_opener(ProxyHandler({}))
        while not stop.is_set():
            try:
                with opener.open(a.pc_url,timeout=2) as response:
                    info=json.loads(base64.b64decode(response.headers['X-Frame-Metadata']))
                    payload=response.read(2*1024*1024)
                image=cv2.imdecode(np.frombuffer(payload,np.uint8),cv2.IMREAD_COLOR)
                if image is None or image.shape!=(720,1280,3):raise RuntimeError('Invalid annotated PC image')
                with condition:pc=dict(image=cv2.resize(image,(426,240) if a.triple else (640,360)),metadata=info,received=time.monotonic());pc_error=None
            except Exception as exc:
                with condition:pc_error=str(exc)
            stop.wait(.25)
    def fetch_audio():
        nonlocal audio,audio_error
        opener=build_opener(ProxyHandler({}))
        while not stop.is_set():
            try:
                with opener.open(a.audio_url,timeout=2) as response:
                    info=json.loads(base64.b64decode(response.headers['X-Frame-Metadata']))
                    payload=response.read(1024*1024)
                image=cv2.imdecode(np.frombuffer(payload,np.uint8),cv2.IMREAD_COLOR)
                if image is None or image.shape!=(570,426,3):raise RuntimeError('Invalid audio panel image')
                with condition:audio=dict(image=image,metadata=info,received=time.monotonic());audio_error=None
            except Exception as exc:
                with condition:audio_error=str(exc)
            stop.wait(.15)
    # CJK fallback lacks Latin/digits: draw each run with its supported font.
    cjk=ImageFont.truetype('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',23)
    latin=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
    def text(draw,xy,value,color='white'):
        x,y=xy
        for run in re.findall(r'[\x00-\xff]+|[^\x00-\xff]+',value):
            font=latin if ord(run[0])<256 else cjk
            draw.text((x,y),run,font=font,fill=color)
            x+=font.getlength(run) if hasattr(font,'getlength') else font.getsize(run)[0]
    background=Image.new('RGB',(1280,720),(18,18,18));draw=ImageDraw.Draw(background)
    text(draw,(18,20),'OV1 单摄像头：实时取景 / 识别结果')
    text(draw,(18,90),'原始视频：不等待识别',color=(100,235,190))
    text(draw,(658,90),'识别结果：标注对应来源帧',color=(100,235,190))
    text(draw,(18,660),'左右刷新分别计数；当前使用一个摄像头，OV2 未启用。',color=(255,215,90))
    background=cv2.cvtColor(np.asarray(background),cv2.COLOR_RGB2BGR)
    layout=None
    if a.triple:
        from av_layout import ThreePanel
        layout=ThreePanel()
    owner_file=Path('/home/xilinx/ov1_hdmi_20261031/color_probe.json')
    writer_file=owner_file.with_name('split_writer.json')
    writer_identity=dict(pid=os.getpid(),pid_start_ticks=int(Path('/proc/self/stat').read_text().split()[21]))
    def writer_state(active):
        temp=writer_file.with_suffix('.tmp');temp.write_text(json.dumps(dict(writer_identity,active=active)));temp.replace(writer_file)
    try:
        # Never instantiate a video driver here: preserve the already lit owner,
        # its timing, and its frame address (the validated W6 paint-live route).
        owner=json.loads(owner_file.read_text());address=owner['frame_address']
        assert owner['boot_id']==boot and owner['bit_sha256']==marker['bit_sha256']
        assert owner['frame_bytes']==1280*720*3 and address%8==0 and 0x100000<=address<=0x20000000-owner['frame_bytes']
        vdma=MMIO(overlay.ip_dict['video/axi_vdma']['phys_addr'],65536)
        def check_owner():
            status=Path('/proc')/str(owner['pid'])/'stat'
            current=json.loads(owner_file.read_text())
            if not status.exists() or int(status.read_text().split()[21])!=owner['pid_start_ticks']:
                raise RuntimeError('HDMI buffer owner exited; stop painting')
            if not current.get('active') or current.get('closing') or current['pid']!=owner['pid']:
                raise RuntimeError('HDMI owner is closing; stop painting')
            if vdma.read(4)&0x71 or any(vdma.read(0x5c+4*i)!=address for i in range(4)):
                raise RuntimeError('HDMI mode/address changed; stop painting')
        writer_state(True);check_owner()
        screen=MMIO(address,1280*720*3).array.view(np.uint8).reshape(720,1280,3)
        session=cc.CaptureSession(MMIO(c.CONTROL_BASE,65536),MMIO(c.DMA_BASE,65536),allocate,a.output,
            c.polarity_for_manifest(metadata),seconds=a.seconds,max_attempts=1000000,max_errors=5,max_samples=0,
            stop_requested=stop.is_set,on_frame=on_frame)
        emit(dict(event='ready',pid=os.getpid(),input='OV1',HDMI=True,independent_local_preview=True))
        capture_thread=threading.Thread(target=capture);publisher=threading.Thread(target=publish);fetcher=threading.Thread(target=fetch,daemon=True)
        capture_thread.start();publisher.start();fetcher.start();deadline=time.monotonic();last_saved=0
        if a.triple:threading.Thread(target=fetch_audio,daemon=True).start()
        previous_raw=None;small_raw=None;previous_sign=None;sign_strip=None
        while not stop.is_set() and time.monotonic()-started<a.seconds:
            compose_started=time.monotonic()
            with condition:item=latest;annotation=pc;pc_problem=pc_error;audio_panel=audio;audio_problem=audio_error
            canvas=background.copy()
            if item is not None:
                if previous_raw!=item['frame']:
                    packed=np.frombuffer(item['raw'],np.uint8).reshape(720,1280,2)
                    small_raw=cv2.cvtColor(cv2.resize(packed,(426,240) if a.triple else (640,360),interpolation=cv2.INTER_NEAREST),cv2.COLOR_BGR5652BGR)
                    previous_raw=item['frame'];raw_updates+=1
                if not a.triple:canvas[145:505,:640]=small_raw
            if annotation is not None and not a.triple:canvas[145:505,640:]=annotation['image']
            def numbers(x,y,value):cv2.putText(canvas,value,(x,y),cv2.FONT_HERSHEY_SIMPLEX,.65,(235,235,235),1,cv2.LINE_AA)
            elapsed=time.monotonic()-started
            numbers(18,565,'Capture %d | New raw %d | Writes %.1f Hz'%(captured,raw_updates,shown/max(elapsed,.001)))
            if item:numbers(18,610,'Frame %d | Age %.2fs'%(item['frame'],time.monotonic()-item['captured']))
            if annotation:
                info=annotation['metadata'];age=time.monotonic()-info['source_timestamp_s']
                numbers(658,565,'Frame %s | Age %.2fs'%(info['frame_id'],age))
                sign=info.get('sign_recognition') or {}
                label='手语：'+(sign.get('label') or '未确定')
            else:label='等待识别画面；左侧独立运行'
            if label!=previous_sign:
                strip=Image.new('RGB',(620,40),(18,18,18));text(ImageDraw.Draw(strip),(0,0),label)
                sign_strip=cv2.cvtColor(np.asarray(strip),cv2.COLOR_RGB2BGR);previous_sign=label
            canvas[585:625,658:1278]=sign_strip
            if a.triple:
                canvas=layout.compose(small_raw,annotation['image'] if annotation else None,audio_panel,
                    raw_item=item,teacher_info=annotation['metadata'] if annotation else None,
                    counts=(captured,raw_updates),now=time.monotonic())
            compose_ms=(time.monotonic()-compose_started)*1000;write_started=time.monotonic()
            # Stable fixed address, same as the successful W6 in-place display.
            # This can tear during a write; no allocation/address swap per frame.
            check_owner()
            screen[:]=canvas  # Uncached mapping; owner never flushes over this.
            shown+=1
            if time.monotonic()-last_saved>=1:
                state=dict(active=True,physical_camera=1,complete_frames=captured,PC_frames_sent=sent,HDMI_frames=shown,
                    elapsed_s=elapsed,local_display_hz=shown/max(elapsed,.001),PC_connection_error=pc_problem,
                    raw_unique_updates=raw_updates,compose_ms=compose_ms,write_ms=(time.monotonic()-write_started)*1000,
                    stable_frame_address=address,HDMI_owner_pid=owner['pid'],HDMI_reconfigured=False,
                    in_place_updates=True,tearing_possible=True,
                    raw_source_frame=item['frame'] if item else None,
                    PC_source_frame=annotation['metadata']['frame_id'] if annotation else None,
                    triple_mode=a.triple,audio_connection_error=audio_problem,
                    audio=audio_panel['metadata'] if audio_panel else None,
                    downloaded=False,raw_waits_for_PC=False)
                temp=a.output/'live.tmp';temp.write_text(json.dumps(state,indent=2));temp.replace(a.output/'live.json')
                preview_temp=a.output/'latest.tmp.jpg'
                if not cv2.imwrite(str(preview_temp),canvas,[cv2.IMWRITE_JPEG_QUALITY,80]):
                    raise RuntimeError('Failed to encode three-column preview')
                preview_temp.replace(a.output/'latest.jpg')
                last_saved=time.monotonic()
            deadline+=.1;stop.wait(max(0,deadline-time.monotonic()))
            if deadline<time.monotonic()-.5:deadline=time.monotonic()
    finally:
        stop.set()
        with condition:condition.notify_all()
        if capture_thread:capture_thread.join()
        if publisher:publisher.join()
        camera_unsafe=session is not None and session.hardware_started and not session.dma_safe
        if not camera_unsafe:writer_state(False)
        if display:
            try:display.close()
            except Exception:pass
        hdmi_unsafe=display is not None and not display.safe
        report=dict(complete_frames=captured,PC_frames_sent=sent,HDMI_frames=shown,unsafe_camera=camera_unsafe,
            unsafe_hdmi=hdmi_unsafe,downloaded=False)
        (a.output/'report.json').write_text(json.dumps(report,indent=2))
        if camera_unsafe or hdmi_unsafe:
            print('DMA Halted not confirmed: preserve process/buffers and power OFF before retry',file=sys.stderr,flush=True)
            while True:time.sleep(60)
        lock.release()


if __name__=='__main__':main()
