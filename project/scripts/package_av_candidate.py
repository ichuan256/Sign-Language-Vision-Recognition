"""Package OV1/HDMI/audio with existing camera/HDMI gates and explicit audio audit."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--video-status',action='store_true',help='Require the diagnostic GPIO and CDC blocks')
    parser.add_argument('--hpd-input',action='store_true',help='Require physical R19 HPD to be an input')
    a=parser.parse_args()
    root=ET.parse(a.build/'ov5640_snapshot.hwh').getroot()
    modules={m.get('FULLNAME'):m for m in root.findall('.//MODULE')}
    assert modules['/audio_codec_ctrl_0'].get('MODTYPE')=='audio_codec_ctrl'
    ranges=[r for r in root.findall('.//MEMRANGE') if r.get('INSTANCE')=='audio_codec_ctrl_0' and r.get('MEMTYPE')=='REGISTER']
    assert len(ranges)==1 and int(ranges[0].get('BASEVALUE'),0)==0x43c00000
    ports={p.get('NAME'):p for p in root.findall('.//EXTERNALPORTS/PORT')}
    # HWH exposes I/O/T signals; the generated top wrapper owns the IOBUFs.
    assert all(p in ports for p in ('IIC_1_scl_i','IIC_1_scl_o','IIC_1_scl_t',
        'IIC_1_sda_i','IIC_1_sda_o','IIC_1_sda_t','audio_clk_10MHz','bclk','lrclk','sdata_i','sdata_o','codec_addr'))
    assert int(ports['audio_clk_10MHz'].get('CLKFREQUENCY'))==10000000
    if a.hpd_input:
        assert a.video_status and ports['hdmi_out_hpd'].get('DIR')=='I'
    if a.video_status:
        gpio=modules['/video_status_gpio']
        assert gpio.get('MODTYPE')=='axi_gpio'
        values={p.get('NAME'):p.get('VALUE') for p in gpio.findall('./PARAMETERS/PARAMETER')}
        assert all(int(values[k],0)==v for k,v in {'C_IS_DUAL':1,'C_GPIO_WIDTH':32,'C_GPIO2_WIDTH':8,'C_ALL_INPUTS':1,'C_ALL_INPUTS_2':1}.items())
        ranges=[r for r in root.findall('.//MEMRANGE') if r.get('INSTANCE')=='video_status_gpio' and r.get('MEMTYPE')=='REGISTER']
        assert len(ranges)==1 and int(ranges[0].get('BASEVALUE'),0)==0x41210000
        for name in ('/video_status_cdc','/video_flags_cdc','/video_locked_cdc'):
            assert modules[name].get('MODTYPE')=='xpm_cdc_gen'
        values={p.get('NAME'):p.get('VALUE') for p in modules['/video_locked_cdc'].findall('./PARAMETERS/PARAMETER')}
        assert str(values['SRC_INPUT_REG']).lower() in ('true','1')
        assert int(values['DEST_SYNC_FF'])==4 and int(values['WIDTH'])==1
    subprocess.run([sys.executable,str(ROOT/'project/scripts/ov5640/package_snapshot.py'),
        '--build',str(a.build),'--output',str(a.output),'--allow-unverified-io','--hdmi-output'],check=True)
    manifest_path=a.output/'release_manifest.json';m=json.loads(manifest_path.read_text(encoding='utf-8'))
    m['design'].update(audio_input=True,audio_ip='audio_codec_ctrl_0',audio_base=0x43c00000,
                       audio_mclk_hz=10000000,audio_i2c='PS I2C1 EMIO',display_layout='raw / teacher / ASR playback')
    m['validation']['board_audio']=False
    if a.video_status:
        m['design']['video_status']=dict(ip='video_status_gpio',base=0x41210000,status_offset=0,flags_offset=8,
            cdc_stages=4,bus_coherent=False,flags=['MMCM_locked','video_locked','underflow','overflow','SOF_state','VTG_CE','HDMI_enable','AXI_reset_released'])
        m['validation']['board_video_status']=False
    if a.hpd_input:
        m['design'].update(hdmi_hpd_input=True,hdmi_hpd_active_low=True)
        m['design']['video_status']['flags'][6]='HPD_n'
    sources=[p for p in (ROOT/'project/fpga/ip_repo/audio_codec_ctrl_v1.0').rglob('*') if p.is_file()]
    sources+=[ROOT/'project/fpga/xdc/audio_w6.xdc']
    m['audio_sources']={p.relative_to(ROOT).as_posix():sha(p) for p in sources}
    m['runtime_software']={str(p):sha(ROOT/p) for p in (
        Path('project/board/ov5640_snapshot/split_hdmi_stream.py'),Path('project/board/ov5640_snapshot/av_layout.py'),
        Path('project/board/ov5640_snapshot/hdmi_color_probe.py'),Path('ASR/board_audio_stream.py'),Path('ASR/board_pcm_capture.c'))}
    manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(packaged=True,files=m['files'],audio_checked=True)))

if __name__=='__main__':main()
