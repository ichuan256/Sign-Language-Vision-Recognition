"""Freeze the confirmed PC-assisted runtime into an isolated, reviewable package."""
import hashlib,json,py_compile,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def replace_once(text,old,new):
    if text.count(old)!=1:raise RuntimeError('Unexpected frozen source shape: '+old[:70])
    return text.replace(old,new)

def main():
    out=ROOT/'project/analysis/av_autostart_20261101'/('package_'+str(time.time_ns()));out.mkdir(parents=True)
    package=out/'payload';runtime=package/'runtime';runtime.mkdir(parents=True)
    release=ROOT/'project/board/ov5640_snapshot/release_av_runtime_20261101'
    manifest=json.loads((release/'release_manifest.json').read_text(encoding='utf-8'))
    loaded_bit='/home/xilinx/ov1_hdmi_20261031/release/'+manifest['files']['bit']['path']
    loaded_hwh='/home/xilinx/ov1_hdmi_20261031/release/'+manifest['files']['hwh']['path']
    shutil.copytree(release,package/'release')
    for name in ('board_gateway.py','runner.py','sign-av-owner.service'):
        shutil.copy2(ROOT/'project/board/av_boot'/name,package/name)
    for name in ('capture.py','continuous_capture.py','hdmi_preview.py','av_layout.py'):
        shutil.copy2(ROOT/'project/board/ov5640_snapshot'/name,runtime/name)
    for name in ('retained_mmio.py','frame_hdmi_receiver.py','sd_video_stream.py'):
        shutil.copy2(ROOT/'project/board/av_boot'/name,runtime/name)
    owner=(ROOT/'project/board/ov5640_snapshot/hdmi_color_probe.py').read_text(encoding='utf-8')
    owner=owner.replace("root=Path('/home/xilinx/ov1_hdmi_20261031')","root=Path('/var/lib/sign-av')")
    owner=owner.replace("root/'release/release_manifest.json'","Path('/usr/local/lib/sign-av/release/release_manifest.json')")
    owner=owner.replace("root/'release'","Path('/usr/local/lib/sign-av/release')")
    owner=replace_once(owner,"Overlay(str(Path('/usr/local/lib/sign-av/release')/manifest['files']['bit']['path']),download=False)",
        'Overlay('+repr(loaded_bit)+',download=False)')
    owner=replace_once(owner,'while not stop[0] and time.monotonic()-start<3600:','while not stop[0]:')
    owner=replace_once(owner,'hdmi=overlay.video.hdmi_out;',
        "assert MMIO(0x40400000,65536).read(0x34)&1 and MMIO(0x44a00000,65536).read(4)&1, 'DMA must be Halted before boot HDMI initialization'\nhdmi=overlay.video.hdmi_out;")
    (runtime/'hdmi_owner.py').write_text(owner,encoding='utf-8')
    split=(ROOT/'project/board/ov5640_snapshot/split_hdmi_stream.py').read_text(encoding='utf-8')
    split=split.replace('/home/xilinx/ov1_hdmi_20261031','/var/lib/sign-av')
    split=replace_once(split,"Overlay(str(files['bit']),download=False)",'Overlay('+repr(loaded_bit)+',download=False)')
    split=replace_once(split,'not 10<=a.seconds<=86400','not (a.seconds==0 or 10<=a.seconds<=86400)')
    split=replace_once(split,'max_attempts=1000000','max_attempts=1000000000000')
    split=replace_once(split,'while not stop.is_set() and time.monotonic()-started<a.seconds:',
        'while not stop.is_set() and (not a.seconds or time.monotonic()-started<a.seconds):')
    (runtime/'split_hdmi_stream.py').write_text(split,encoding='utf-8')
    audio=(ROOT/'ASR/board_audio_stream.py').read_text(encoding='utf-8')
    audio=replace_once(audio,"overlay=Overlay(str(files['bit']),download=False)",'overlay=Overlay('+repr(loaded_bit)+',download=False)')
    (runtime/'board_audio_stream.py').write_text(audio,encoding='utf-8')
    for path in package.rglob('*.py'):py_compile.compile(str(path),doraise=True)
    manifest=json.loads((release/'release_manifest.json').read_text(encoding='utf-8'))
    config=dict(date='2026-11-01',scope='PC_Holistic_and_ASR_board_capture_HDMI_only',
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        bit_sha256=manifest['files']['bit']['sha256'],hwh_sha256=manifest['files']['hwh']['sha256'],
        loaded_bit_path=loaded_bit,loaded_hwh_path=loaded_hwh,
        files={str(p.relative_to(package)).replace('\\','/'):sha(p) for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts},
        no_model_training=True,firmware_changed=False,board_offline_inference=False,
        PC_sources={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [ROOT/'project/scripts/start_av_console.py',ROOT/'project/scripts/demo_control.html',ROOT/'project/scripts/av_autostart.py',ROOT/'project/scripts/demo_control.py',
            ROOT/'vision/src/vision/keypoints/ov5640_ssh_source.py',ROOT/'vision/src/vision/keypoints/single_hdmi_demo.py',
            ROOT/'vision/src/vision/keypoints/recording_demo.py',ROOT/'vision/src/vision/keypoints/sd_teaching_source.py']})
    config['files']['runtime/board_pcm_capture']=manifest['runtime_binaries']['board_pcm_capture']['sha256']
    (package/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'project/_tmp/av_autostart_package.json').write_text(json.dumps(dict(path=str(package),evidence=str(out)),indent=2),encoding='utf-8')
    print(json.dumps(dict(path=str(package),files=len(config['files']),bit_sha256=config['bit_sha256'],hwh_sha256=config['hwh_sha256']),ensure_ascii=False))
if __name__=='__main__':main()
