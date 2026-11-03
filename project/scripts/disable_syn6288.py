"""Withdraw this task's unused board UART gateway, without opening serial."""
import getpass,json,time
from pathlib import Path
from install_syn6288 import ROOT,HOST,run

def main():
    stage='/home/xilinx/usb_tts_20261101/disable_'+str(time.time_ns())
    run(['ssh','-o','BatchMode=yes',HOST,'mkdir -p '+stage])
    run(['scp','-o','BatchMode=yes',str(ROOT/'project/board/usb_tts/disable_board.py'),HOST+':'+stage+'/'])
    password=getpass.getpass('Board sudo password for disabling unused gateway (hidden): ')
    result=run(['ssh','-T','-o','BatchMode=yes',HOST,"sudo -S -p '' /usr/bin/python3 -I "+stage+'/disable_board.py'],input=password+'\n')
    password=None;record=json.loads(result.stdout)
    out=ROOT/'project/analysis/usb_digits_20261101'
    (out/('syn_disabled_'+str(time.time_ns())+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()
