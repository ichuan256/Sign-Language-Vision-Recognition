"""Exercise the local console API without printing session tokens."""
import argparse,json,re,time
from pathlib import Path
from urllib.request import Request,build_opener,ProxyHandler

ROOT=Path(__file__).resolve().parents[2];BASE='http://127.0.0.1:18790'
OPENER=build_opener(ProxyHandler({}))
def get(path):return OPENER.open(BASE+path,timeout=5).read()
def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('av','idle','camera','sd_teacher'))
    p.add_argument('--camera',type=int,default=0);p.add_argument('--wait',type=int,default=0)
    p.add_argument('--observe',type=int,default=0);a=p.parse_args()
    out=ROOT/'project/analysis/av_console_20261101'/('exercise_'+str(time.time_ns()));out.mkdir(parents=True)
    start=time.monotonic()
    if a.mode:
        token=re.search(r"const token='([^']+)'",get('/').decode()).group(1)
        request=Request(BASE+'/api/switch',data=json.dumps(dict(mode=a.mode,camera=a.camera,cold_boot=True)).encode(),
            headers={'X-Session':token,'Content-Type':'application/json'},method='POST')
        OPENER.open(request,timeout=8).close()
    def sample():return json.loads(get('/api/state'))
    state=sample()
    while state['busy'] and time.monotonic()-start<a.wait:
        time.sleep(1);state=sample()
    (out/'transition.json').write_text(json.dumps(dict(elapsed_s=time.monotonic()-start,state=state),ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'observe.jsonl').open('w',encoding='utf-8') as stream:
        deadline=time.monotonic()+a.observe
        while True:
            state=sample();stream.write(json.dumps(state,ensure_ascii=False)+'\n');stream.flush()
            detail=state.get('details',{});display=detail.get('display',{})
            print(json.dumps(dict(mode=state['mode'],busy=state['busy'],error=state.get('error'),connected=state['connected'],
                results=detail.get('results'),source_frame=detail.get('video_frame'),clip=detail.get('clip'),
                hdmi_frames=display.get('hdmi_frames'),teacher_ms=detail.get('teacher_ms'),evidence=str(out)),ensure_ascii=False),flush=True)
            if time.monotonic()>=deadline:break
            time.sleep(5)
    if state.get('error') or state['busy']:raise RuntimeError('Console transition did not complete cleanly')
    if a.mode and state['mode']!=a.mode:raise RuntimeError('Requested mode not running')

if __name__=='__main__':main()
