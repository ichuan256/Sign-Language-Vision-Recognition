"""Bounded, cold-OV1-HDMI-only physical output probe using the proven W6 driver."""
import json,os,signal,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pynq import Overlay,PL,DefaultIP,MMIO
from pynq.lib.video import VideoMode,PIXEL_BGR
from pynq.lib.video.dma import AxiVDMA
import continuous_capture as cc

root=Path('/home/xilinx/ov1_hdmi_20261031')
manifest=json.loads((root/'release/release_manifest.json').read_text())
marker=json.loads(Path('/run/ov1_hdmi_boot.json').read_text())
assert marker['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert marker['bit_sha256']==manifest['files']['bit']['sha256']
lock=cc.ProcessLock('/run/lock/ov1_hdmi_output.lock').acquire()
overlay=Overlay(str(root/'release'/manifest['files']['bit']['path']),download=False)
assert overlay.ip_dict['video/axi_vdma']['phys_addr']==0x44a00000

class OutputVDMA(AxiVDMA):
    def __init__(self,description):
        DefaultIP.__init__(self,description)
        self.framecount=int(description['parameters']['C_NUM_FSTORES'])
        self.writechannel=AxiVDMA.MM2SChannel(self,None,description['device'].default_memory)

stop=[False]
for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.__setitem__(0,True))
hdmi=overlay.video.hdmi_out;vdma=OutputVDMA(overlay.ip_dict['video/axi_vdma']);hdmi._vdma=vdma
hdmi.configure(VideoMode(640,480,24),PIXEL_BGR)
hdmi.start();hdmi._hdmi.start()
vtc=MMIO(overlay.ip_dict['video/hdmi_out/frontend/vtc_out']['phys_addr'],65536)
vtc.write(0,vtc.read(0)|1)  # AMD XVTC_CTL_SW_MASK: explicit core enable.
if not manifest['design'].get('hdmi_hpd_input'):
    MMIO(overlay.ip_dict['video/hdmi_out/frontend/hdmi_out_hpd_video']['phys_addr'],32).write(0,1)
frame=hdmi.newframe()
for index,color in enumerate(((255,255,255),(0,0,255),(0,255,0),(255,0,0))):frame[:,index*160:(index+1)*160]=color
frame.flush()
for index in range(vdma.framecount):
    vdma.writechannel._frames[index]=frame;vdma.writechannel._frames.takeownership(index)
identity=dict(pid=os.getpid(),pid_start_ticks=int(Path('/proc/self/stat').read_text().split()[21]),
    frame_address=int(frame.physical_address),frame_bytes=640*480*3,width=640,height=480,
    boot_id=marker['boot_id'],bit_sha256=marker['bit_sha256'])
def record(**fields):
    temp=root/'color_probe.tmp';temp.write_text(json.dumps(dict(identity,**fields)));temp.replace(root/'color_probe.json')
record(active=True,closing=False,pattern='white/red/green/blue',downloaded=False)
def writer_active():
    path=root/'split_writer.json'
    if not path.exists():return False
    try:
        writer=json.loads(path.read_text())
        if not writer.get('active'):return False
        status=Path('/proc')/str(writer['pid'])/'stat'
        return status.exists() and int(status.read_text().split()[21])==writer['pid_start_ticks']
    except Exception:return True  # Uncertain ownership: keep the output BO alive.
start=time.monotonic()
while not stop[0] and time.monotonic()-start<3600:time.sleep(.1)
record(active=True,closing=True,downloaded=False)
# A painter must stop before this owner can release the physical buffer.
while writer_active():time.sleep(.1)
vdma.write(0,vdma.read(0)&~1);deadline=time.monotonic()+2
while not vdma.read(4)&1 and time.monotonic()<deadline:time.sleep(.001)
safe=bool(vdma.read(4)&1)
record(active=False,Halted=safe,downloaded=False)
if not safe:
    while True:time.sleep(60)
hdmi._hdmi.stop();lock.release()
# BOs remain owned until the process closes, after confirmed MM2S Halted.
os._exit(0)
