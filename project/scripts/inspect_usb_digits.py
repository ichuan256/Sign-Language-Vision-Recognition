"""Save USB digit/speech telemetry without camera images or session tokens."""
import json,time,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    controllers=[p for p in (ROOT/'project/_tmp/demo_control').iterdir() if p.is_dir() and p.name[:8].isdigit()]
    controller=max(controllers,key=lambda p:p.name)
    worker=max((p for p in controller.glob('video_*') if p.is_dir()),key=lambda p:p.name)
    live=json.loads((worker/'live.json').read_text(encoding='utf-8'))
    events=[]
    with (worker/'teacher_frames.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            try:row=json.loads(line)
            except json.JSONDecodeError:continue
            digit=row.get('digit_recognition',{})
            if digit.get('announce') is not None:
                events.append(dict(frame=row['frame'],value=digit['announce'],single_hand=digit['hand_count']==1))
    audio=[]
    for path in sorted((worker/'digit_voice').glob('*.wav')):
        with wave.open(str(path)) as wav:
            audio.append(dict(value=int(path.stem),sample_rate=wav.getframerate(),seconds=wav.getnframes()/wav.getframerate()))
    record=dict(date='2026-11-01',worker=str(worker.relative_to(ROOT)),active=live['active'],
        source=live['input_source'],teacher_frames=live['teacher_frames'],digit=live['digit_recognition'],
        recognition_events=events,generated_audio=audio,trained=False,firmware_changed=False,
        scope='PC frozen Holistic landmarks; geometric single-hand count; speech status recorded only if enabled',
        physical_acceptance='separate user feedback required')
    output=ROOT/'project/analysis/usb_digits_20261101';output.mkdir(exist_ok=True)
    path=output/('observe_'+str(time.time_ns())+'.json');path.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(evidence=str(path.relative_to(ROOT)),digit=record['digit'],events=len(events),audio=len(audio)),ensure_ascii=False))

if __name__=='__main__':main()
