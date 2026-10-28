"""Stage bounded P1 diagnostics without overwriting deployed teacher or firmware."""
import argparse
import base64
import getpass
import json
from pathlib import Path
from run_teacher_p0 import ROOT, remote


def run(args):
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('Use a new project/_tmp output')
    if args.action == 'postprocess':
        sources = {'teacher_p1_postprocess.py':'teacher_p1_postprocess.py',
                   'teacher_geometry_fast.py':'teacher_geometry.py',
                   'test_teacher_postprocess.py':'test_teacher_postprocess.py'}
        command = ['teacher_p1_postprocess.py', '--baseline', args.baseline,
                   '--frames', str(args.frames), '--rounds', str(args.rounds)]
        if args.cached_only:
            command.append('--cached-only')
    elif args.action == 'boundary':
        if not args.replay_models or not args.probe:
            raise ValueError('boundary requires --replay-models and --probe')
        sources = {'teacher_p1_boundary.py':'teacher_p1_boundary.py'}
        command = ['teacher_p1_boundary.py', '--baseline', args.baseline,
                   '--probe', args.probe, '--cases', str(args.cases)]
    elif args.action == 'transfer':
        sources = {'teacher_p1_transfer.py':'teacher_p1_transfer.py'}
        command = ['teacher_p1_transfer.py']
    else:
        raise ValueError('Unsupported action')
    payload = {dest:base64.b64encode((ROOT/'project/board/teacher_hands'/src).read_bytes()).decode()
               for dest,src in sources.items()}
    if args.action == 'boundary':
        manifest_path = args.replay_models/'replay_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for name in ['replay_manifest.json']+[c['file'] for c in manifest['candidates']]:
            if Path(name).name!=name:
                raise ValueError('Replay path must be a filename')
            payload[name]=base64.b64encode((args.replay_models/name).read_bytes()).decode()
    request = dict(action=args.action, work=args.work, stage=output.name, command=command,
                   sources=list(payload), training=False, fpga_access=False)
    output.mkdir(parents=True)
    (output/'request.json').write_text(json.dumps(request, indent=2)+'\n', encoding='utf-8')
    script = '''import base64,json,subprocess
from pathlib import Path
work=Path(__WORK__); stage=work/__STAGE__; payload=__PAYLOAD__; args=__ARGS__; action=__ACTION__
sudo_password=__SUDO_PASSWORD__
stage.mkdir(exist_ok=False)
for name,encoded in payload.items():
    (stage/name).write_bytes(base64.b64decode(encoded))
del payload, encoded
command=['/usr/local/share/pynq-venv/bin/python','-u',str(stage/args[0])]+args[1:]+['--work',str(work),'--output',str(stage/'result')]
if action=='transfer':
    command=(['sudo','-S','-p',''] if sudo_password is not None else ['sudo','-n'])+['env','XILINX_XRT=/usr']+command
with (stage/'console.log').open('w') as log:
    proc=subprocess.run(command,input=None if sudo_password is None else (sudo_password+'\\n').encode(),stdout=log,stderr=subprocess.STDOUT,timeout=2400)
files={p.name:p.read_text() for p in (stage/'result').glob('*.json')}
print(json.dumps(dict(returncode=proc.returncode,stage=str(stage),files=files,console=(stage/'console.log').read_text())))
'''.replace('__WORK__',repr(args.work),1).replace('__STAGE__',repr(output.name),1).replace('__ARGS__',repr(command),1).replace('__ACTION__',repr(args.action),1).replace('__SUDO_PASSWORD__',repr(args._sudo_password),1).replace('__PAYLOAD__',repr(payload),1)
    # Validate packaging locally before opening SSH. Delimited placeholders
    # cannot collide with the base64 alphabet or corrupt binary payloads.
    compile(script,'<p1-remote-request>','exec')
    try:
        result = remote(args.host, script, timeout=2460)
    except Exception as error:
        message=str(error)
        if args._sudo_password:
            message=message.replace(args._sudo_password,'<redacted>')
        (output/'transport_failure.json').write_text(json.dumps(dict(error=message[-2000:]),indent=2)+'\n',encoding='utf-8')
        raise RuntimeError(message) from None
    (output/'console.log').write_text(result.pop('console'), encoding='utf-8')
    for name, text in result.pop('files').items():
        if Path(name).name != name or not name.endswith('.json'):
            raise RuntimeError('Unexpected result filename')
        (output/name).write_text(text, encoding='utf-8')
    (output/'remote_run.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    report = json.loads((output/'report.json').read_text(encoding='utf-8')) if (output/'report.json').exists() else {}
    print(json.dumps(dict(returncode=result['returncode'],completed=report.get('completed'),
                         error=report.get('error'),passes=report.get('passes'),pairs=report.get('pairs'))))
    if result['returncode'] or not report.get('completed'):
        raise RuntimeError('P1 diagnostic failed; inspect console and report')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['postprocess','boundary','transfer'])
    p.add_argument('--host', default='xilinx@192.168.2.99')
    p.add_argument('--work', default='/home/xilinx/hands_teacher_20261027_v1')
    p.add_argument('--baseline', default='/home/xilinx/hands_teacher_20261027_v1/teacher_p0_baseline_20261028_v1')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--frames', type=int, default=120)
    p.add_argument('--rounds', type=int, default=2)
    p.add_argument('--cached-only', action='store_true')
    p.add_argument('--replay-models',type=Path)
    p.add_argument('--probe')
    p.add_argument('--cases',type=int,default=100)
    p.add_argument('--sudo-password-prompt',action='store_true',help='Transfer only: read sudo password without echo; never save it')
    args = p.parse_args()
    if not 1 <= args.frames <= 300 or not 1 <= args.rounds <= 3 or not 1<=args.cases<=100:
        p.error('Bounded frames/rounds required')
    if args.sudo_password_prompt and args.action!='transfer':
        p.error('sudo password is only needed for CMA transfer measurement')
    args._sudo_password=getpass.getpass('Board sudo password: ') if args.sudo_password_prompt else None
    run(args)


if __name__ == '__main__':
    main()
