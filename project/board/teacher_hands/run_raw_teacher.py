"""Run the complete teacher on board-local RGB888 video; optionally refresh existing HDMI framebuffer."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import cv2
import numpy as np
from run_teacher import HandsPipeline,HdmiWriter,sha256
from teacher_geometry import draw_hands


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--frames',type=int,default=48);p.add_argument('--threads',type=int,default=2,choices=(1,2))
    p.add_argument('--display-owner-pid',type=int);p.add_argument('--save-preview',action='store_true')
    a=p.parse_args()
    if a.output.exists() or not 1<=a.frames<=240:raise ValueError('New output and 1..240 frames required')
    meta=json.loads(a.manifest.read_text())
    if (meta['width'],meta['height'],meta['channels'])!=(1280,720,3):raise ValueError('Expected RGB888 720p')
    if sha256(a.raw)!=meta['raw_sha256']:raise ValueError('Raw video SHA mismatch')
    source=np.memmap(a.raw,mode='r',dtype=np.uint8,shape=(meta['frames'],720,1280,3))
    a.output.mkdir(parents=True)
    report=dict(scope='board_local_full_teacher_RGB_video_no_PC_ROI',completed=False,frames_requested=a.frames,
        raw_sha256=meta['raw_sha256'],source_sha256=meta['source_sha256'],threads=a.threads,
        models={name:sha256(a.work/name) for name in ('palm_detection_full.tflite','hand_landmark_full.tflite')},
        runtime_sha256=sha256(a.work/'libhands_tflite.so'),display_enabled=bool(a.display_owner_pid),
        pc_inference=False,teacher_labels_as_input=False,screen_visually_confirmed=False)
    pipeline=HandsPipeline(a.work,a.threads);writer=HdmiWriter(a.display_owner_pid) if a.display_owner_pid else None
    records=[];previews=[]
    try:
        start_all=time.perf_counter()
        for frame_id in range(a.frames):
            frame_start=time.perf_counter();rgb=np.array(source[frame_id%meta['frames']],copy=True)
            hands,metrics=pipeline.process(rgb)
            annotated=draw_hands(rgb,hands);elapsed=time.perf_counter()-start_all
            fps=(frame_id+1)/elapsed
            if writer:
                cv2.rectangle(annotated,(0,0),(1280,65),(0,0,0),-1)
                cv2.putText(annotated,'PS TFLITE FULL TEACHER | %.2f FPS | %d HANDS'%(fps,len(hands)),(14,28),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,220,255),2,cv2.LINE_AA)
                cv2.putText(annotated,'BOARD-LOCAL PALMS + ROI + 21 POINTS + TRACKING',(14,54),cv2.FONT_HERSHEY_SIMPLEX,.55,(255,255,255),1,cv2.LINE_AA)
                writer.write(annotated)
            if a.save_preview and frame_id%8==0:
                cv2.imwrite(str(a.output/('frame_%03d.jpg'%frame_id)),cv2.cvtColor(annotated,cv2.COLOR_RGB2BGR))
            record=dict(frame_id=frame_id,end_to_end_ms=(time.perf_counter()-frame_start)*1000,
                hands=len(hands),presence=[h['presence'] for h in hands],
                points=[h['points'].tolist() for h in hands],**metrics)
            records.append(record)
            print('TEACHER_FRAME',frame_id,'hands',len(hands),'ms',round(record['end_to_end_ms'],1),flush=True)
        elapsed=time.perf_counter()-start_all;latencies=[r['end_to_end_ms'] for r in records]
        report.update(completed=len(records)==a.frames,frames=len(records),elapsed_s=elapsed,
            end_to_end_fps=len(records)/elapsed,end_to_end_ms_P50=float(np.percentile(latencies,50)),
            end_to_end_ms_P95=float(np.percentile(latencies,95)),
            palm_inference_frames=sum(r['palm_ms']>0 for r in records),
            tracked_frames=sum(r['palm_ms']==0 for r in records),
            hands_detected_frames=sum(r['hands']>0 for r in records))
    except Exception as error:
        report.update(completed=False,error=str(error));raise
    finally:
        pipeline.close();(a.output/'frames.json').write_text(json.dumps(records)+'\n')
        (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('TEACHER_REPORT '+json.dumps(report),flush=True)

if __name__=='__main__':main()
