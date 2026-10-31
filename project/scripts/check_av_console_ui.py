"""Read the served UI contract without emitting the session token."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.request import build_opener,ProxyHandler

class Buttons(HTMLParser):
    def __init__(self):super().__init__();self.modes=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='button' and 'data-mode' in a:self.modes.append(a['data-mode'])
        if 'id' in a:self.ids.append(a['id'])

def main():
    opener=build_opener(ProxyHandler({}));html=opener.open('http://127.0.0.1:18790/',timeout=5).read().decode()
    parser=Buttons();parser.feed(html)
    state=json.loads(opener.open('http://127.0.0.1:18790/api/state',timeout=5).read())
    result=dict(modes=parser.modes,legacy_cold_checkbox='coldBoot' in parser.ids,
        teacher_latency_label='教师单帧耗时' in html,console_profile=state.get('console_profile'),
        mode=state.get('mode'),busy=state.get('busy'),error=state.get('error'))
    out=Path(__file__).resolve().parents[2]/'project/analysis/av_console_20261101';out.mkdir(exist_ok=True)
    (out/'ui_verified.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    assert parser.modes==['av','camera','sd_teacher','idle'] and not result['legacy_cold_checkbox']
    assert result['console_profile']=='av_current_firmware_v1'

if __name__=='__main__':main()
