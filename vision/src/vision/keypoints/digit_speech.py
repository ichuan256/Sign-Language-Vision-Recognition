"""Send stable digits to the board USB-UART SYN6288, retaining one pending digit."""
import json
from pathlib import Path
import subprocess
import threading


class DigitSpeaker:
    def __init__(self,output):
        self.output=Path(output);self.condition=threading.Condition();self.pending=None;self.stopping=False
        self.state=dict(ready=False,error=None,spoken_count=0,accepted_count=0,last_spoken=None,
            output='FPGA USB / SYN6288',device='/dev/ttyUSB0')
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()

    def announce(self,value):
        if type(value) is not int or value not in range(1,6):raise ValueError('Only digits 1..5 may be spoken')
        with self.condition:
            if not self.stopping:self.pending=value;self.condition.notify_all()

    def snapshot(self):
        with self.condition:return dict(self.state)

    @staticmethod
    def call(action):
        if action not in ('probe','1','2','3','4','5'):raise ValueError('Invalid SYN6288 action')
        result=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=5',
            '-o','ServerAliveInterval=3','-o','ServerAliveCountMax=2','xilinx@192.168.2.99',
            'sudo -n /usr/local/sbin/sign-digit-say '+action],
            stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',
            timeout=12,creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:raise RuntimeError(result.stderr.strip() or 'SYN6288 board gateway failed')
        return json.loads(result.stdout)

    def run(self):
        try:
            status=self.call('probe')
            with self.condition:self.state.update(ready=status['ready'],last_board_reply=status,
                error=None if status['ready'] else 'SYN6288未回复状态，请检查模块供电与串口接线')
            while True:
                with self.condition:
                    self.condition.wait_for(lambda:self.stopping or self.pending is not None)
                    if self.stopping:break
                    value=self.pending;self.pending=None
                try:
                    reply=self.call(str(value))
                    with (self.output/'digit_speech.jsonl').open('a',encoding='utf-8') as log:
                        log.write(json.dumps(reply,ensure_ascii=False)+'\n')
                    confirmed=reply['command_accepted'] or reply['completion_confirmed']
                    with self.condition:self.state.update(ready=confirmed,last_spoken=value,last_board_reply=reply,
                        accepted_count=self.state['accepted_count']+int(reply['command_accepted']),
                        spoken_count=self.state['spoken_count']+int(reply['completion_confirmed']),
                        error=None if confirmed else '已发送播报指令，但未收到SYN6288回传')
                except Exception as exc:
                    with self.condition:self.state.update(ready=False,error=str(exc))
        except Exception as exc:
            with self.condition:self.state.update(ready=False,error=str(exc))

    def close(self):
        with self.condition:self.stopping=True;self.pending=None;self.condition.notify_all()
        self.thread.join(timeout=15)
