"""HDMI Chinese renderer and preview. Hardware refresh lives in hdmi_renderer.py.

The JSON state file accepts page=calibration/dashboard and text (display only).
Preview rendering needs Pillow; board output also needs PYNQ and numpy.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1280, 720
BACKGROUND = (13, 22, 39)
FOREGROUND = (234, 241, 250)
MUTED = (151, 171, 195)
FONT_CANDIDATES = (
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    'C:/Windows/Fonts/msyh.ttc',
)


class Renderer:
    def __init__(self, font=None):
        self.font_path = font or next((p for p in FONT_CANDIDATES if Path(p).is_file()), None)
        if not self.font_path:
            raise RuntimeError('Chinese font missing: provide --font /path/to/font.ttf')
        self.fonts = {size: ImageFont.truetype(self.font_path, size)
                      for size in (22, 26, 30, 36, 44, 52, 60)}

    def render(self, state, ticks=0):
        image = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND)
        d = ImageDraw.Draw(image)

        def text(x, y, value, size=30, fill=FOREGROUND):
            d.text((x, y), value, font=self.fonts[size], fill=fill)

        text(48, 28, '妙手通言', 44)
        text(49, 87, 'HDMI 显示验证', 26, MUTED)
        d.rounded_rectangle((976, 35, 1232, 92), radius=24, fill=(23, 67, 58))
        text(1000, 45, '显示通路运行中', 26, (119, 235, 183))
        d.line((48, 131, 1232, 131), fill=(44, 61, 84), width=2)

        if state.get('page', 'calibration') == 'calibration':
            text(48, 153, '01  颜色与中文校准', 36)
            colors = ((255, 0, 0), (0, 255, 0), (0, 0, 255))
            for i, (color, label) in enumerate(zip(colors, ('1  红色 / RED', '2  绿色 / GREEN', '3  蓝色 / BLUE'))):
                x = 48 + i * 400
                d.rounded_rectangle((x, 222, x + 384, 404), radius=16, fill=color)
                text(x + 16, 423, label, 30)
            for i, (color, label) in enumerate((((255, 220, 0), '黄色'), ((255, 255, 255), '白色'), ((0, 0, 0), '黑色'))):
                x = 48 + i * 400
                d.rounded_rectangle((x, 481, x + 384, 537), radius=10, fill=color,
                                    outline=(64, 82, 107), width=2)
                text(x + 16, 548, label, 26)
            text(48, 604, '中文测试：你好，世界！谢谢。', 36)
        else:
            text(48, 153, '02  文字显示', 36)
            text(48, 207, '显示演示 · 通过文件更新文字', 26, (119, 235, 183))
            d.rounded_rectangle((48, 258, 1232, 546), radius=24, fill=(24, 39, 61))
            message = str(state.get('text', '你好，世界！'))[:180]
            lines, line = [], ''
            for character in message:
                if character == '\n' or d.textlength(line + character, font=self.fonts[52]) > 1090:
                    lines.append(line)
                    line = '' if character == '\n' else character
                else:
                    line += character
            lines.append(line)
            for i, line in enumerate(lines[:3]):
                if i == 2 and len(lines) > 3:
                    line = line[:-1] + '…'
                text(82, 282 + i * 75, line, 52)
            text(48, 582, '当前仅验证显示功能；音频与识别未接入', 30, MUTED)

        d.line((48, 663, 1232, 663), fill=(44, 61, 84), width=2)
        text(48, 675, '1280 × 720  |  RGB 24 位', 22, MUTED)
        text(899, 675, '画面更新  %06d' % ticks, 22, MUTED)
        return image


def read_state(path, previous):
    try:
        state = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(state, dict) or state.get('page', 'calibration') not in ('calibration', 'dashboard'):
            raise ValueError('state must be an object with a supported page')
        return state
    except (OSError, ValueError) as error:
        print('State unavailable; keeping previous content: %s' % error, flush=True)
        return previous


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--font')
    parser.add_argument('--preview', required=True, help='Render a PNG without accessing hardware')
    parser.add_argument('--page', choices=('calibration', 'dashboard'), default='calibration')
    args = parser.parse_args()
    renderer = Renderer(args.font)
    renderer.render({'page': args.page, 'text': '你好，世界！\n这是一条中文显示演示。'}, 12).save(args.preview)


if __name__ == '__main__':
    main()
