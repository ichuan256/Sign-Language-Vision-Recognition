"""Render a clearly marked software-only review image, no camera/mic activation."""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'ASR'),str(ROOT/'project/board/ov5640_snapshot')]
from audio_loop import Screen
from loop_core import Session
from types import SimpleNamespace
from av_layout import ThreePanel

output=ROOT/'project/analysis/av_three_panel_20261031';output.mkdir(parents=True,exist_ok=True)
previous=cv2.imread(str(ROOT/'project/analysis/ov1_hdmi_20261031/latest.jpg'))
raw=cv2.resize(previous[145:505,:640],(426,240))
teacher=cv2.resize(previous[145:505,640:1280],(426,240))
session=Session(SimpleNamespace(asset_source='布局验证',entries=[],asset_paths=[],manifest_sha256='test'))
session.update(status='听觉栏布局预览',partial='早上好，你好吗？很好，谢谢。',playing='教学视频区域',video_frames=0)
screen=Screen(session)
video=Image.new('RGB',(640,360),(24,39,61));ImageDraw.Draw(video).text((100,150),'手语视频区域',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',40),fill='white')
screen.compose(video);jpeg,meta=screen.current_panel()
audio=dict(image=cv2.imdecode(np.frombuffer(jpeg,np.uint8),cv2.IMREAD_COLOR),received=100)
frame=ThreePanel().compose(raw,teacher,audio,raw_item=dict(frame=1,captured=99.8),
    teacher_info=dict(frame_id=1,source_timestamp_s=99,sign_recognition={}),counts=(1,1),now=100)
image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));draw=ImageDraw.Draw(image)
draw.rectangle((0,0,1280,60),fill=(18,18,18))
draw.text((18,15),'软件布局预览 · 左中沿用历史截图 · 非本次现场采集',font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24),fill=(255,215,90))
image.save(output/'layout_preview.jpg')
print(str(output/'layout_preview.jpg'))
