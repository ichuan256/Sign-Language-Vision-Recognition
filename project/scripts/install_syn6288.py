"""Stage and install the fixed board USB-UART digit gateway, without saved credentials."""
import getpass,hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HOST='xilinx@192.168.2.99'

def run(command,**kwargs):
    result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',timeout=40,**kwargs)
    if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    return result

def main():
    source=ROOT/'project/board/usb_tts';stage='/home/xilinx/usb_tts_20261101/stage_'+str(time.time_ns())
    sha=hashlib.sha256((source/'syn6288_gateway.py').read_bytes()).hexdigest()
    run(['ssh','-o','BatchMode=yes',HOST,'mkdir -p '+stage])
    run(['scp','-o','BatchMode=yes',str(source/'syn6288_gateway.py'),str(source/'install_board.py'),HOST+':'+stage+'/'])
    password=getpass.getpass('Board sudo password (hidden): ')
    result=run(['ssh','-T','-o','BatchMode=yes',HOST,"sudo -S -p '' /usr/bin/python3 -I "+stage+
        '/install_board.py --source '+stage+'/syn6288_gateway.py --sha256 '+sha],input=password+'\n')
    password=None;record=json.loads(result.stdout)
    output=ROOT/'project/analysis/usb_digits_20261101';output.mkdir(exist_ok=True)
    (output/('syn_install_'+str(time.time_ns())+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()
