#!/usr/bin/python3 -I
"""Fixed SYN6288 status / digits 1..5 on the board's CH340 USB UART."""
import argparse,json,os,select,time
from functools import reduce
from operator import xor
from pathlib import Path

DEVICE='/dev/ttyUSB0'
WORDS=('一','二','三','四','五')

def frame(command,payload=b''):
    if len(payload)>200:raise ValueError('Text exceeds the SYN6288 frame limit')
    body=bytes([command])+payload
    packet=b'\xfd'+(len(body)+1).to_bytes(2,'big')+body
    return packet+bytes([reduce(xor,packet,0)])

def digit_frame(value):
    if type(value) is not int or not 1<=value<=5:raise ValueError('Only digits 1..5')
    return frame(1,b'\0'+('[v10]'+WORDS[value-1]).encode('gb2312'))

def validate_device():
    current=Path('/sys/class/tty/ttyUSB0/device').resolve()
    for parent in (current,*current.parents):
        if (parent/'idVendor').exists():
            if ((parent/'idVendor').read_text().strip(),(parent/'idProduct').read_text().strip())!=('1a86','7523'):
                raise RuntimeError('Expected CH340 USB UART not found')
            return
    raise RuntimeError('CH340 USB UART is not connected')

def receive(fd,timeout,until_idle=False):
    result=bytearray();deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        ready,_,_=select.select([fd],[],[],max(0,deadline-time.monotonic()))
        if not ready:break
        block=os.read(fd,256)
        if not block:continue
        result.extend(block)
        if 0x45 in result:raise RuntimeError('SYN6288 rejected command: '+result.hex())
        if until_idle:
            if 0x4f in result:break
        elif 0x4e in result or 0x4f in result:break
    return bytes(result)

def send(fd,packet):
    if os.write(fd,packet)!=len(packet):raise RuntimeError('Incomplete SYN6288 UART write')

def execute(action):
    import fcntl,termios
    validate_device()
    with open('/run/lock/sign-digit-syn6288.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fd=os.open(DEVICE,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
        try:
            fcntl.ioctl(fd,termios.TIOCEXCL)
            attributes=termios.tcgetattr(fd)
            attributes[0]=0;attributes[1]=0;attributes[2]=termios.CS8|termios.CLOCAL|termios.CREAD
            attributes[3]=0;attributes[4]=termios.B9600;attributes[5]=termios.B9600
            attributes[6][termios.VMIN]=0;attributes[6][termios.VTIME]=0
            termios.tcsetattr(fd,termios.TCSANOW,attributes);termios.tcflush(fd,termios.TCIFLUSH)
            send(fd,frame(0x21));status=receive(fd,.5)
            result=dict(device=DEVICE,baud=9600,protocol='SYN6288_GB2312_XOR',status_rx=status.hex(),
                ready=bool(set(status)&{0x4e,0x4f}),written=False)
            if action=='probe':return result
            if 0x4e in status and 0x4f not in status:
                done=receive(fd,4,until_idle=True)
                if 0x4f not in done:raise RuntimeError('SYN6288 still busy; speech not interrupted')
            time.sleep(.012)
            packet=digit_frame(int(action));send(fd,packet)
            replies=receive(fd,2.5,until_idle=True)
            result.update(value=int(action),written=True,tx_hex=packet.hex(),reply_hex=replies.hex(),
                command_accepted=0x41 in replies,completion_confirmed=0x4f in replies)
            return result
        finally:
            fcntl.ioctl(fd,termios.TIOCNXCL);os.close(fd)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('probe','1','2','3','4','5'))
    args=parser.parse_args()
    if os.geteuid()!=0:raise RuntimeError('Use the installed fixed sudo entry')
    print(json.dumps(execute(args.action),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
