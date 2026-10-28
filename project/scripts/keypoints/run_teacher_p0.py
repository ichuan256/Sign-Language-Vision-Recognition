"""Isolated SSH tools for teacher profiling; never train or load an FPGA image."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8']


def remote(host, source, timeout=60):
    result = subprocess.run(SSH+[host, 'python3 -'], input=source, text=True,
                            encoding='utf-8', capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return json.loads(result.stdout)


def inspect(host, work, output):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('Use a new project/_tmp directory')
    source = '''import hashlib,json,os,platform,time
from pathlib import Path
work=Path(WORK)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
files={}
for name in ('libhands_tflite.so','palm_detection_full.tflite','hand_landmark_full.tflite','run_teacher.py','teacher_geometry.py','teacher_runtime.py','tflite_runner.cpp','build_native.sh'):
    p=work/name
    files[name]=dict(bytes=p.stat().st_size,sha256=digest(p))
processes=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        comm=(p/'comm').read_text().strip()
        if not any(x in comm for x in ('python','cc1','c++','g++','cmake','make')):continue
        args=(p/'cmdline').read_bytes().split(b'\\0')
        scripts=[Path(x.decode(errors='replace')).name for x in args if x.endswith((b'.py',b'.sh'))]
        processes.append(dict(pid=int(p.name),comm=comm,scripts=scripts))
    except (OSError,ValueError):pass
headers={}
base=work/'tensorflow-2.12.1/tensorflow/lite'
for name in ('profiling/buffered_profiler.h','profiling/profile_buffer.h','core/api/profiler.h','delegates/utils/simple_delegate.h'):
    p=base/name
    if p.exists():headers[name]=p.read_text()
firmware={}
for name in ('kws_hdmi.bit','kws_hdmi.hwh'):
    p=Path('/home/xilinx')/name
    firmware[name]=dict(sha256=digest(p),bytes=p.stat().st_size)
print(json.dumps(dict(scope='read_only_teacher_board_inventory',architecture=platform.machine(),
    board_clock_unix_s=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    uptime=Path('/proc/uptime').read_text().strip(),meminfo=Path('/proc/meminfo').read_text(),
    model_workdir=str(work),files=files,firmware_files=firmware,
    loaded_firmware_caveat='file hashes are not proof of current PL programming identity',
    processes=processes,headers=headers,
    compile_commands=json.loads((work/'tflite_build/compile_commands.json').read_text()),
    wrapper_link=(work/'tflite_build/CMakeFiles/hands_tflite.dir/link.txt').read_text())))
'''.replace('WORK', repr(work), 1)
    report = remote(host, source)
    output.mkdir(parents=True)
    headers = report.pop('headers')
    for name, value in headers.items():
        path = output/'headers'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')
    commands = report.pop('compile_commands')
    (output/'compile_commands.json').write_text(json.dumps(commands, indent=2)+'\n', encoding='utf-8')
    (output/'wrapper_link.txt').write_text(report.pop('wrapper_link'), encoding='utf-8')
    (output/'board_inventory.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    matches = [c for c in commands if c['file'].endswith('/tflite_runner.cpp')]
    if len(matches) == 1:
        (output/'wrapper_compile.json').write_text(json.dumps(matches[0], indent=2)+'\n', encoding='utf-8')
    else:
        report['wrapper_compile_caveat'] = 'Not present in compile_commands; use target flags.make'
    (output/'board_inventory.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(output=str(output),boot_id=report['boot_id'],processes=report['processes'],
                          models={k:v for k,v in report['files'].items() if k.endswith('.tflite')})))


def build_probe(host, work, output):
    if output.exists() or not output.is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('Use a new project/_tmp directory')
    cpp = (ROOT/'project/board/teacher_hands/teacher_probe.cpp').read_text(encoding='utf-8')
    script = '''import hashlib,json,shlex,subprocess
from pathlib import Path
work=Path(WORK); stage=work/STAGE
stage.mkdir(exist_ok=False)
(stage/'teacher_probe.cpp').write_text(SOURCE)
(stage/'tflite_runner.cpp').write_bytes((work/'tflite_runner.cpp').read_bytes())
build=work/'tflite_build'
flags={}
for line in (build/'CMakeFiles/hands_tflite.dir/flags.make').read_text().splitlines():
    if ' = ' in line:
        key,value=line.split(' = ',1);flags[key]=value
obj=str(stage/'teacher_probe.o'); library=str(stage/'libhands_probe.so')
compile=['/usr/bin/c++']+shlex.split(flags.get('CXX_DEFINES',''))+shlex.split(flags.get('CXX_INCLUDES',''))+shlex.split(flags.get('CXX_FLAGS',''))+['-c',str(stage/'teacher_probe.cpp'),'-o',obj]
link=shlex.split((build/'CMakeFiles/hands_tflite.dir/link.txt').read_text())
link=[obj if x.endswith('tflite_runner.cpp.o') else x for x in link]
link[link.index('-o')+1]=library
link=[x.replace('-soname,libhands_tflite.so','-soname,libhands_probe.so') for x in link]
status=[]
for label,command in [('compile',compile),('link',link)]:
    run=subprocess.run(command,cwd=str(build),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)
    (stage/(label+'.log')).write_text(run.stdout)
    status.append(dict(step=label,returncode=run.returncode,command=command))
    if run.returncode:break
report=dict(stage=str(stage),steps=status,success=all(x['returncode']==0 for x in status),
    diagnostics_only=True,fpga_access=False,original_wrapper_sha256=hashlib.sha256((work/'tflite_runner.cpp').read_bytes()).hexdigest())
if Path(library).exists():report['probe_sha256']=hashlib.sha256(Path(library).read_bytes()).hexdigest()
(stage/'build_report.json').write_text(json.dumps(report,indent=2))
report['logs']={name:(stage/(name+'.log')).read_text() for name in ('compile','link') if (stage/(name+'.log')).exists()}
print(json.dumps(report))
'''.replace('WORK', repr(work), 1).replace('STAGE', repr(output.name), 1).replace('SOURCE', repr(cpp), 1)
    report = remote(host, script, timeout=500)
    output.mkdir(parents=True)
    for name, data in report.pop('logs').items():
        (output/(name+'.log')).write_text(data, encoding='utf-8')
    (output/'build_report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'steps'}))
    if not report['success']:
        raise RuntimeError('Isolated diagnostic build failed; inspect local logs')


def run_baseline(host, work, output, video, probe_build, frames, profile_inputs):
    if output.exists() or not output.is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('Use a new project/_tmp directory')
    if not 1 <= frames <= 300 or not 1 <= profile_inputs <= 24:
        raise ValueError('Bounded run required')
    payload = dict(script=(ROOT/'project/board/teacher_hands/teacher_p0_board.py').read_text(encoding='utf-8'),
                   video=base64.b64encode(video.read_bytes()).decode(),frames=frames,
                   profile_inputs=profile_inputs,probe_build=probe_build)
    script = '''import base64,hashlib,json,subprocess
from pathlib import Path
work=Path(WORK);stage=work/STAGE;payload=PAYLOAD
stage.mkdir(exist_ok=False)
(stage/'teacher_p0_board.py').write_text(payload['script'])
(stage/'frozen_input.mp4').write_bytes(base64.b64decode(payload['video']))
probe=Path(payload['probe_build'])/'libhands_probe.so'
command=['/usr/local/share/pynq-venv/bin/python','-u',str(stage/'teacher_p0_board.py'),
    '--work',str(work),'--video',str(stage/'frozen_input.mp4'),'--probe',str(probe),
    '--output',str(stage/'result'),'--frames',str(payload['frames']),
    '--profile-inputs',str(payload['profile_inputs'])]
with (stage/'console.log').open('w') as log:
    run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=900)
files={p.name:p.read_text() for p in (stage/'result').glob('*.json')}
print(json.dumps(dict(stage=str(stage),returncode=run.returncode,files=files,
    console=(stage/'console.log').read_text(),command=command)))
'''.replace('WORK',repr(work),1).replace('STAGE',repr(output.name),1).replace('PAYLOAD',repr(payload),1)
    output.mkdir(parents=True)
    # Save the planned request before any remote activity; no credentials are stored.
    (output/'request.json').write_text(json.dumps(dict(work=work,frames=frames,profile_inputs=profile_inputs,
        video=str(video.relative_to(ROOT)),probe_build=probe_build),indent=2)+'\n',encoding='utf-8')
    response=remote(host,script,timeout=960)
    (output/'console.log').write_text(response.pop('console'),encoding='utf-8')
    for name,data in response.pop('files').items():
        if Path(name).name != name or not name.endswith('.json'):
            raise RuntimeError('Unexpected artifact name')
        (output/name).write_text(data,encoding='utf-8')
    (output/'remote_run.json').write_text(json.dumps(response,indent=2)+'\n',encoding='utf-8')
    if not (output/'report.json').exists():
        raise RuntimeError('Board process produced no report; inspect console and remote_run.json')
    report=json.loads((output/'report.json').read_text(encoding='utf-8'))
    print(json.dumps(dict(output=str(output),completed=report['completed'],
        baseline=report.get('baseline'),diagnostics=report.get('diagnostics'),error=report.get('error'))))
    if response['returncode'] or not report['completed']:
        raise RuntimeError('Bounded P0 run failed; inspect report and console')


def status(host, work, output):
    script='''import json
from pathlib import Path
stage=Path(WORK)/STAGE
log=stage/'console.log'
report=stage/'result/report.json'
data=json.loads(report.read_text()) if report.exists() else {}
print(json.dumps(dict(stage=str(stage),tail=log.read_text().splitlines()[-6:] if log.exists() else [],
    completed=data.get('completed'),baseline_frames=data.get('baseline',{}).get('frames'),error=data.get('error'))))
'''.replace('WORK',repr(work),1).replace('STAGE',repr(output.name),1)
    print(json.dumps(remote(host,script)))


def postprocess(host,work,output,baseline_stage):
    if output.exists() or not output.is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('Use a new project/_tmp directory')
    script='''import hashlib,json,sys,time
from pathlib import Path
import cv2,numpy as np
work=Path(WORK);stage=work/STAGE;baseline=Path(BASELINE)
stage.mkdir(exist_ok=False)
sys.path.insert(0,str(work))
from teacher_geometry import letterbox_rgb,decode_palms
inputs=json.loads((baseline/'result/probe_inputs.json').read_text())['palm'][:12]
capture=cv2.VideoCapture(str(baseline/'frozen_input.mp4'));ok,bgr=capture.read();capture.release()
if not ok:raise RuntimeError('Cannot decode fixed input')
rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
letterbox=[]
for _ in range(12):
    start=time.perf_counter();_,padding=letterbox_rgb(rgb);letterbox.append((time.perf_counter()-start)*1000)
cases=[]
for item in inputs:
    with np.load(baseline/'result'/item['file'],allow_pickle=False) as data:
        outputs=[data['output_0'],data['output_1']]
    scores=next(x for x in outputs if x.size==2016).reshape(-1)
    values=[]
    for _ in range(2):
        start=time.perf_counter();detections=decode_palms(outputs,padding);values.append((time.perf_counter()-start)*1000)
    cases.append(dict(input=item['file'],decode_ms=values,detections=len(detections),
        scalar_loop_candidates=int(np.count_nonzero(scores>-100.)),
        raw_logits_above_zero=int(np.count_nonzero(scores>=0.))))
result=dict(scope='original_PS_postprocessing_timing_only_no_semantic_changes',
    source_geometry_sha256=hashlib.sha256((work/'teacher_geometry.py').read_bytes()).hexdigest(),
    letterbox_ms=letterbox,cases=cases,labels=False,training=False,fpga_access=False,
    caveat='Cached original model outputs; no pipeline, model, threshold or detector frequency was changed')
(stage/'postprocess.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
'''.replace('WORK',repr(work),1).replace('STAGE',repr(output.name),1).replace('BASELINE',repr(baseline_stage),1)
    # Run under the same NumPy/OpenCV environment as the teacher.
    command='/usr/local/share/pynq-venv/bin/python -'
    response=subprocess.run(SSH+[host,command],input=script,text=True,encoding='utf-8',capture_output=True,timeout=120)
    if response.returncode:raise RuntimeError(response.stderr[-3000:])
    report=json.loads(response.stdout)
    output.mkdir(parents=True)
    (output/'postprocess.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(output),letterbox_mean_ms=sum(report['letterbox_ms'])/len(report['letterbox_ms']),
        decode_mean_ms=sum(v for c in report['cases'] for v in c['decode_ms'])/(len(report['cases'])*2))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect','build-probe','baseline','status','postprocess'])
    parser.add_argument('--host', default='xilinx@192.168.2.99')
    parser.add_argument('--work', default='/home/xilinx/hands_teacher_20261027_v1')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--video', type=Path)
    parser.add_argument('--probe-build')
    parser.add_argument('--frames',type=int,default=120)
    parser.add_argument('--profile-inputs',type=int,default=12)
    parser.add_argument('--baseline-stage')
    args = parser.parse_args()
    if args.action == 'inspect':
        inspect(args.host, args.work, args.output.resolve())
    elif args.action == 'build-probe':
        build_probe(args.host, args.work, args.output.resolve())
    elif args.action == 'status':
        status(args.host,args.work,args.output)
    elif args.action == 'postprocess':
        if not args.baseline_stage:parser.error('postprocess needs --baseline-stage')
        postprocess(args.host,args.work,args.output.resolve(),args.baseline_stage)
    else:
        if not args.video or not args.probe_build:
            parser.error('baseline needs --video and --probe-build')
        run_baseline(args.host,args.work,args.output.resolve(),args.video.resolve(),args.probe_build,
                     args.frames,args.profile_inputs)


if __name__ == '__main__':
    main()
