"""Run one serialized Vivado stage on a fresh keypoint+HDMI project."""
import argparse
from pathlib import Path
import subprocess
import shutil

ROOT=Path(__file__).resolve().parents[3]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['inspect','prepare','constraints_resume','synth','synth_resume','impl'])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=Path,help='Reuse only deliberate exported Tcl/inventory, never generated project state')
    parser.add_argument('--attempt',default='',help='Distinct alphanumeric log suffix for a deliberate retry')
    args=parser.parse_args()
    out=args.output.resolve()
    if not out.is_relative_to(ROOT) or out==ROOT:raise ValueError('Output must remain inside workspace')
    if args.seed:
        if args.mode!='prepare' or out.exists():raise ValueError('Seed only a new prepare directory')
        out.mkdir(parents=True)
        for name in ('base_bd.tcl','inventory.tcl'):
            shutil.copy2(args.seed/name,out/name)
    if args.attempt and not args.attempt.isalnum():raise ValueError('Alphanumeric attempt label required')
    label=out.name+'_'+args.mode+('_'+args.attempt if args.attempt else '')
    log=out.parent/(label+'_console.log')
    if log.exists():raise FileExistsError(log)
    script=ROOT/'project/fpga/scripts/keypoints_system.tcl'
    command=['cmd.exe','/d','/c','F:/APP/Xilinx/Vivado/2024.1/bin/vivado.bat',
        '-mode','batch','-nojournal','-log',str(out.parent/(label+'_vivado.log')),
        '-source',str(script),'-tclargs',args.mode,str(out)]
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run(command,cwd=out.parent,stdout=stream,stderr=subprocess.STDOUT)
    print('VIVADO_STAGE',args.mode,'RETURN_CODE',result.returncode,'LOG',log)
    if result.returncode:raise RuntimeError('Vivado stage failed; inspect log')

if __name__=='__main__':main()
