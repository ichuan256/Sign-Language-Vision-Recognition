"""Record a bounded LINE IN probe from current W6, without loading a bitstream."""
import argparse
import json
import wave

import numpy as np
from pynq import Overlay
from pynq.lib.audio import AudioADAU1761


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=3)
    parser.add_argument('--output', default='/home/xilinx/asr_offline/w6_mic_probe.wav')
    args = parser.parse_args()
    overlay = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
    audio = AudioADAU1761(overlay.ip_dict['audio_codec_ctrl_0'])
    print('AUDIO_CONFIGURING_CURRENT_W6', flush=True)
    audio.configure()
    audio.select_line_in()
    print('AUDIO_RECORDING seconds=%s' % args.seconds, flush=True)
    audio.record(args.seconds)
    # The codec stores signed 24-bit samples in 32-bit words.
    signed = (audio.buffer.astype(np.int32) << 8) >> 8
    channels = signed.reshape(-1, 2).astype(np.float64) / 8388608
    report = {'sample_rate': audio.sample_rate, 'samples': len(channels),
              'peak': np.abs(channels).max(axis=0).tolist(),
              'rms': np.sqrt(np.mean(channels ** 2, axis=0)).tolist(),
              'dc': channels.mean(axis=0).tolist()}
    with wave.open(args.output, 'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(audio.sample_rate)
        output.writeframes((signed >> 8).astype('<i2').tobytes())
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
