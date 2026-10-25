#!/usr/bin/env python3
"""板端按键监听：冷启动固件加载后常驻；按一下 BTN0 => 通知 PC 启动音频演示。

- 读 axi_gpio_btns（0x43C10000，W6+btn 固件，2026-10-23 起）；
- 信号经 ssh 远程转发隧道 board:18770 -> PC:18770 送达 PC 常驻服务
  （audio_resident.py）；隧道不在（PC 没开）时按键静默忽略；
- 日志进 journalctl（button-watch.service），死机现场取证用串口重定向见
  AGENTS.md §3.2。

依赖：pynq-venv python，root（/dev/mem）。勿在本脚本加载任何 bitstream。
"""
import socket
import time

from pynq import MMIO

GPIO_ADDR = 0x43C10000
BTN0_MASK = 0x1
TRIGGER = ('127.0.0.1', 18770)   # 板端本地，由 PC 的 ssh -R 转发到 PC
POLL_S = 0.05
DEBOUNCE_S = 0.3


def notify():
    try:
        with socket.create_connection(TRIGGER, timeout=2) as sock:
            sock.sendall(b'START\n')
        print('NOTIFY_OK', flush=True)
    except OSError as exc:
        print('NOTIFY_FAIL %s' % exc, flush=True)


def main():
    gpio = MMIO(GPIO_ADDR, 16)
    print('BUTTON_WATCH_READY addr=0x%08X' % GPIO_ADDR, flush=True)
    pressed_since = None
    while True:
        value = gpio.read(0) & BTN0_MASK
        now = time.monotonic()
        if value:
            if pressed_since is None:
                pressed_since = now
            elif now - pressed_since >= DEBOUNCE_S:
                print('BTN0 pressed', flush=True)
                notify()
                pressed_since = None
                while gpio.read(0) & BTN0_MASK:   # 等松手，防止连发
                    time.sleep(POLL_S)
        else:
            pressed_since = None
        time.sleep(POLL_S)


if __name__ == '__main__':
    main()
