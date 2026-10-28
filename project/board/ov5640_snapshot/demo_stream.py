"""Stream only complete OV5640 RGB565 frames over an existing SSH session.

Uses the existing conservative capture/reset/lock path unchanged. This firmware
has no HDMI. No bitstream loading, partial-frame padding, or model inference.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

import continuous_capture as cc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--assume-cold-boot',action='store_true')
    args=parser.parse_args()
    original=cc.CaptureSession
    class StreamingSession(original):
        pending=None
        frame_number=0
        def _capture_one(self):
            self.pending=None
            result=super()._capture_one()
            self.pending=result
            return result
        def _halt(self):
            super()._halt()
            pending=self.pending;self.pending=None
            if pending is None or not pending['image_safe'] or self.buffer is None:return
            # DMA Halted has been confirmed by the original helper before readout.
            self.buffer.invalidate()
            raw=memoryview(self.buffer)[:pending['received_bytes']].tobytes()
            self.frame_number+=1
            header=dict(event='frame',frame=self.frame_number,bytes=len(raw),width=1280,height=720,
                format='RGB565_LE',board_capture_monotonic_s=time.monotonic(),dma_shutdown_confirmed=True)
            try:
                sys.stdout.buffer.write((json.dumps(header)+'\n').encode())
                sys.stdout.buffer.write(raw);sys.stdout.buffer.flush()
            except BrokenPipeError:os.kill(os.getpid(),signal.SIGINT)
    cc.CaptureSession=StreamingSession
    # All stop routes enter the existing interrupt flag and DMA Halted cleanup.
    signal.signal(signal.SIGTERM,lambda *_:os.kill(os.getpid(),signal.SIGINT))
    print(json.dumps(dict(event='ready',pid=os.getpid(),input='OV5640',HDMI=False)),flush=True)
    result=cc.run_capture(args.output,args.manifest,assume_cold_boot=args.assume_cold_boot,
        seconds=86400,max_attempts=1000000,max_errors=5,max_samples=0)
    print(json.dumps(dict(event='finished',result=result)),flush=True)
    if cc.UNSAFE_SESSIONS:
        # Keep the DMA buffer and flock alive exactly as the original CLI does.
        print('DMA unsafe: preserve this process; power OFF the board before any retry.',file=sys.stderr,flush=True)
        while True:time.sleep(60)


if __name__=='__main__':main()
