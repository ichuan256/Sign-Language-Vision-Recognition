"""Update the HDMI-only UI without restarting it or touching the FPGA."""
import argparse
import json
import os
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('text', nargs='?', default='你好，世界！')
    parser.add_argument('--page', choices=('calibration', 'dashboard'), default='dashboard')
    parser.add_argument('--state', default='/home/xilinx/hdmi_state.json')
    args = parser.parse_args()
    destination = Path(args.state)
    # Replace within the same directory so the UI never sees half-written JSON.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump({'page': args.page, 'text': args.text}, stream, ensure_ascii=False)
            stream.write('\n')
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    print('HDMI display content updated')


if __name__ == '__main__':
    main()
