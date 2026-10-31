"""Three independent HDMI columns. Rendering only; no model/hardware access."""
import re
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont


class ThreePanel:
    def __init__(self,font=None):
        cjk=font or next(str(p) for p in map(Path,('C:/Windows/Fonts/msyh.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')) if p.is_file())
        latin='C:/Windows/Fonts/arial.ttf' if Path('C:/Windows/Fonts/arial.ttf').exists() else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        self.cjk=ImageFont.truetype(cjk,23);self.latin=ImageFont.truetype(latin,23)
        image=Image.new('RGB',(1280,720),(18,18,18));draw=ImageDraw.Draw(image)
        self.text(draw,(18,20),'妙手通言 · 视觉与听觉同步展示')
        for x,label in ((18,'单目实时画面'),(445,'关键点叠加'),(872,'听觉字幕与手语播放')):
            self.text(draw,(x,90),label,(100,235,190))
        self.text(draw,(18,660),'OV1 单目 · 视听并行运行',(255,215,90))
        self.text(draw,(872,430),'等待听觉服务',(180,180,180))
        self.background=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
        self.previous=None;self.sign=None
        error=Image.new('RGB',(426,42),(55,25,15));self.text(ImageDraw.Draw(error),(12,2),'听觉连接中断',(255,194,102))
        self.disconnected=cv2.cvtColor(np.asarray(error),cv2.COLOR_RGB2BGR)

    def text(self,draw,xy,value,color='white'):
        x,y=xy
        for run in re.findall(r'[\x00-\xff]+|[^\x00-\xff]+',value):
            font=self.latin if ord(run[0])<256 else self.cjk
            draw.text((x,y),run,font=font,fill=color)
            x+=font.getlength(run) if hasattr(font,'getlength') else font.getsize(run)[0]

    def compose(self,raw,annotation,audio,*,raw_item,teacher_info,counts,now):
        canvas=self.background.copy()
        if raw is not None:canvas[145:385,:426]=raw
        if annotation is not None:canvas[145:385,427:853]=annotation
        if audio is not None:
            canvas[145:715,854:1280]=audio['image']
            if now-audio['received']>3:canvas[145:187,854:1280]=self.disconnected
        def numbers(x,y,value):cv2.putText(canvas,value,(x,y),cv2.FONT_HERSHEY_SIMPLEX,.58,(235,235,235),1,cv2.LINE_AA)
        numbers(18,440,'Capture %d | New raw %d'%counts)
        if raw_item:
            numbers(18,485,'Frame %d'%raw_item['frame'])
            numbers(18,530,'Age %.2fs'%(now-raw_item['captured']))
        label='等待视觉识别'
        if teacher_info:
            numbers(445,440,'Frame %s'%teacher_info['frame_id'])
            numbers(445,485,'Age %.2fs'%(now-teacher_info['source_timestamp_s']))
            label='手语：'+((teacher_info.get('sign_recognition') or {}).get('label') or '未确定')
        if label!=self.previous:
            strip=Image.new('RGB',(409,40),(18,18,18));self.text(ImageDraw.Draw(strip),(0,0),label)
            self.sign=cv2.cvtColor(np.asarray(strip),cv2.COLOR_RGB2BGR);self.previous=label
        canvas[535:575,445:854]=self.sign
        return canvas
