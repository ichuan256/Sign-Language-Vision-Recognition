"""Package the no-audio HDMI regression candidate with explicit HWH comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    current=ROOT/'project/board/ov5640_snapshot/release_av_hpd_20261101'
    def load(path):
        tree=ET.parse(path)
        return tree,{x.get('FULLNAME'):x for x in tree.findall('.//MODULE')}
    tree,modules=load(args.build/'ov5640_snapshot.hwh')
    old_tree,old_modules=load(current/'ov5640_snapshot.hwh')
    assert '/audio_codec_ctrl_0' not in modules and '/clk_wiz_audio' not in modules
    ports={p.get('NAME'):p for p in tree.findall('.//EXTERNALPORTS/PORT')}
    assert ports['hdmi_out_hpd'].get('DIR')=='I'
    assert not any(p.startswith(('IIC_1','audio_clk')) or p in ('bclk','lrclk','sdata_i','sdata_o','codec_addr') for p in ports)
    def params(module):return {p.get('NAME'):p.get('VALUE') for p in module.findall('./PARAMETERS/PARAMETER')}
    changed={}
    for name,previous in old_modules.items():
        if not name.startswith('/video/') or name not in modules:continue
        a,b=params(previous),params(modules[name])
        differences={k:[a.get(k),b.get(k)] for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
        if differences:changed[name]=differences
    assert not changed, 'Video hierarchy parameters changed: '+repr(changed)
    for name in ('/camera','/capture_dma','/camera_control','/video_status_gpio','/video_status_cdc','/video_flags_cdc','/video_locked_cdc'):
        assert name in modules and params(modules[name])==params(old_modules[name]),name
    ranges=[r for r in tree.findall('.//MEMRANGE') if r.get('INSTANCE')=='video_status_gpio' and r.get('MEMTYPE')=='REGISTER']
    assert len(ranges)==1 and int(ranges[0].get('BASEVALUE'),0)==0x41210000
    ps=params(modules['/ps7'])
    assert all(int(ps[k])==0 for k in ('PCW_EN_I2C1','PCW_EN_EMIO_I2C1','PCW_I2C1_PERIPHERAL_ENABLE'))
    subprocess.run([sys.executable,str(ROOT/'project/scripts/ov5640/package_snapshot.py'),
        '--build',str(args.build),'--output',str(args.output),'--allow-unverified-io','--hdmi-output'],check=True)
    manifest_path=args.output/'release_manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    previous=json.loads((current/'release_manifest.json').read_text(encoding='utf-8'))
    manifest['design'].update(audio_input=False,hdmi_hpd_input=True,hdmi_hpd_active_low=True,
        video_status=previous['design']['video_status'])
    manifest['validation']['board_video_status']=False
    manifest['regression_isolation']=dict(reference_bit_sha256=previous['files']['bit']['sha256'],
        purpose='HDMI regression after AV merge; retain camera/video/HPD diagnostics, remove audio IP/MCLK/I2C1',
        video_parameter_differences=changed,board_display_passed=False,
        cold_boot_only=True,runtime_redownload_forbidden=True)
    helper=ROOT/'project/board/ov5640_snapshot/hdmi_color_probe.py'
    manifest['runtime_software']={helper.relative_to(ROOT).as_posix():hashlib.sha256(helper.read_bytes()).hexdigest()}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(packaged=True,files=manifest['files'],video_parameters_unchanged=True,
        audio_removed=True,board_verified=False)))


if __name__=='__main__':main()
