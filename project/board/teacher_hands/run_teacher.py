"""Board-independent full MediaPipe Hands: image -> palms -> ROI -> 21 landmarks -> tracking/display."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import cv2
import numpy as np
from teacher_runtime import TFLiteModel
from teacher_geometry import decode_palms,letterbox_rgb,roi_from_palm,run_landmark,roi_from_landmarks,associate,draw_hands


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


class HandsPipeline:
    def __init__(self, work, threads=2):
        self.palm=TFLiteModel(work/'libhands_tflite.so',work/'palm_detection_full.tflite',threads)
        self.landmark=TFLiteModel(work/'libhands_tflite.so',work/'hand_landmark_full.tflite',threads)
        self.rois=[]

    def close(self):
        self.palm.close();self.landmark.close()

    def process(self, rgb):
        metrics=dict(palm_ms=0.,landmark_ms=[],detections=0,palm_detections=[])
        rois=self.rois
        if len(rois)!=2:
            tensor,padding=letterbox_rgb(rgb)
            start=time.perf_counter();outputs=self.palm.invoke(tensor)
            metrics['palm_ms']=(time.perf_counter()-start)*1000
            detections=decode_palms(outputs,padding)
            metrics['detections']=len(detections)
            metrics['palm_detections']=[dict(score=d['score'],box=d['box'].tolist(),keypoints=d['keypoints'].tolist()) for d in detections]
            detected=[roi_from_palm(d,rgb.shape) for d in detections[:2]]
            rois=associate(detected,self.rois)
        metrics['input_rois']=[r.tolist() for r in rois[:2]]
        metrics['presence_scores']=[];metrics['candidate_points']=[]
        hands=[];next_rois=[]
        for roi in rois[:2]:
            start=time.perf_counter();hand=run_landmark(self.landmark,rgb,roi)
            metrics['landmark_ms'].append((time.perf_counter()-start)*1000)
            metrics['presence_scores'].append(hand['presence'])
            metrics['candidate_points'].append(hand['points'].tolist())
            if hand['accepted']:
                hands.append(hand);next_rois.append(roi_from_landmarks(hand['points'],rgb.shape))
        self.rois=next_rois
        return hands,metrics


class HdmiWriter:
    def __init__(self, owner_pid):
        from pynq import MMIO
        self.owner=Path('/proc')/str(owner_pid)
        if b'hdmi_display.py' not in (self.owner/'cmdline').read_bytes():
            raise RuntimeError('Existing HDMI owner is not alive')
        self.identity=(self.owner/'stat').read_text().rsplit(')',1)[1].split()[19]
        self.dma=MMIO(0x44A00000,65536)
        self.addresses=[self.dma.read(0x5c+4*i) for i in range(4)]
        if not self.addresses[0] or len(set(self.addresses))!=1:
            raise RuntimeError('Expected one retained framebuffer')
        self.check()
        self.frame=MMIO(self.addresses[0],1280*720*3)

    def check(self):
        if b'hdmi_display.py' not in (self.owner/'cmdline').read_bytes() or (self.owner/'stat').read_text().rsplit(')',1)[1].split()[19]!=self.identity:
            raise RuntimeError('HDMI owner changed')
        if self.addresses!=[self.dma.read(0x5c+4*i) for i in range(4)] or self.dma.read(4)&0x71:
            raise RuntimeError('VDMA state changed')
        if self.dma.read(0x50)!=720 or self.dma.read(0x54)!=3840 or self.dma.read(0x58)&0xffffff!=3840:
            raise RuntimeError('Expected 720p RGB888 mode')

    def write(self,rgb):
        self.check()
        if rgb.shape[:2]!=(720,1280):
            rgb=cv2.resize(rgb,(1280,720),interpolation=cv2.INTER_LINEAR)
        # kws_hdmi.bit hdmi_out swaps R and B between framebuffer and TMDS
        # (verified 2026-10-28 with quadrant test); compensate in software
        # until the BD wiring is fixed in the M0b rebuild.
        rgb=rgb[...,::-1]
        self.frame.array[:]=np.ascontiguousarray(rgb,dtype=np.uint8).reshape(-1).view('<u4')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--video',type=Path);p.add_argument('--frames',type=int,default=60)
    p.add_argument('--threads',type=int,default=2,choices=(1,2));p.add_argument('--benchmark-only',action='store_true')
    p.add_argument('--display-owner-pid',type=int);p.add_argument('--record',action='store_true')
    p.add_argument('--loop',action='store_true',help='restart the video at EOF until --frames is reached')
    a=p.parse_args()
    if a.output.exists() or not 1<=a.frames<=10000:raise ValueError('New bounded output required')
    if not a.benchmark_only and not a.video:raise ValueError('--video is required outside benchmark-only')
    a.output.mkdir(parents=True)
    report=dict(scope='board_local_full_MediaPipe_Hands_no_PC_ROI',completed=False,
        model='unmodified palm_detection_full + hand_landmark_full',threads=a.threads,
        models={name:sha256(a.work/name) for name in ('palm_detection_full.tflite','hand_landmark_full.tflite')},
        runtime_sha256=sha256(a.work/'libhands_tflite.so'),pc_inference=False,teacher_labels_as_input=False)
    pipeline=HandsPipeline(a.work,a.threads);records=[];writer=None;capture=None;recorder=None
    try:
        if a.benchmark_only:
            palm,palm_metrics=pipeline.palm.benchmark(5)
            landmark,landmark_metrics=pipeline.landmark.benchmark(5)
            np.savez(a.output/'zero_input_outputs.npz',
                **{f'palm_{i}':x for i,x in enumerate(palm)},
                **{f'landmark_{i}':x for i,x in enumerate(landmark)})
            report.update(completed=True,palm=palm_metrics,landmark=landmark_metrics)
        else:
            capture=cv2.VideoCapture(str(a.video))
            if not capture.isOpened():raise RuntimeError('Board-local video cannot decode')
            if a.display_owner_pid:writer=HdmiWriter(a.display_owner_pid)
            if a.record:recorder=cv2.VideoWriter(str(a.output/'annotated.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),10,(1280,720))
            start_all=time.perf_counter()
            for frame_id in range(a.frames):
                frame_start=time.perf_counter();ok,bgr=capture.read()
                if not ok:
                    if not a.loop:break
                    capture.release();capture=cv2.VideoCapture(str(a.video))
                    ok,bgr=capture.read()
                    if not ok:break
                rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
                hands,metrics=pipeline.process(rgb)
                annotated=draw_hands(rgb,hands)
                elapsed_so_far=time.perf_counter()-start_all
                fps=(frame_id+1)/elapsed_so_far
                if writer:
                    display=cv2.resize(annotated,(1280,720)) if annotated.shape[:2]!=(720,1280) else annotated
                    cv2.rectangle(display,(0,0),(1280,65),(0,0,0),-1)
                    cv2.putText(display,'PS TFLITE FULL TEACHER | %.2f FPS | %d HANDS'%(fps,len(hands)),(14,28),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,220,255),2,cv2.LINE_AA)
                    cv2.putText(display,'BOARD-LOCAL PALMS + ROI + 21 POINTS + TRACKING',(14,54),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),1,cv2.LINE_AA)
                    writer.write(display)
                if recorder:
                    frame=cv2.resize(annotated,(1280,720));recorder.write(cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
                record=dict(frame_id=frame_id,captured_monotonic_s=time.monotonic(),
                    end_to_end_ms=(time.perf_counter()-frame_start)*1000,hands=len(hands),
                    presence=[h['presence'] for h in hands],points=[[h['points'].tolist()] for h in hands],**metrics)
                records.append(record)
                print('TEACHER_FRAME',frame_id,'hands',len(hands),'ms',round(record['end_to_end_ms'],1),flush=True)
            elapsed=time.perf_counter()-start_all
            latencies=[r['end_to_end_ms'] for r in records]
            report.update(completed=len(records)==a.frames,frames=len(records),elapsed_s=elapsed,
                end_to_end_fps=len(records)/elapsed if elapsed else 0,
                end_to_end_ms_P50=float(np.percentile(latencies,50)) if latencies else None,
                end_to_end_ms_P95=float(np.percentile(latencies,95)) if latencies else None,
                tracked_frames=sum(r['palm_ms']==0 for r in records),display_enabled=bool(writer),
                screen_visually_confirmed=False)
        (a.output/'frames.json').write_text(json.dumps(records)+'\n')
    except Exception as error:
        report.update(completed=False,error=str(error));raise
    finally:
        if recorder:recorder.release()
        if capture:capture.release()
        pipeline.close()
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('TEACHER_REPORT '+json.dumps(report),flush=True)

if __name__=='__main__':main()
