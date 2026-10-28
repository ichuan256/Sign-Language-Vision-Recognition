"""Safely back up the loaded camera firmware and stage one paired build."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

BASE = Path('/home/xilinx/jupyter_notebooks/ov5640_snapshot')
STAGE = Path('/home/xilinx/ov5640_release_v15_20261027')
OLD_BIT = 'c0705d38513f45f421a3410dea5077c53ad64fddd856004eb2307b0cce28611f'
OLD_HWH = '4bf00374ab229f7423aabf033f805ce9e0cd269451c87d3b48ef4c5d78dbcd0a'
FILES = ('ov5640_snapshot.bit', 'ov5640_snapshot.hwh', 'release_manifest.json', 'build_provenance.json')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    marker = BASE / 'boot_switch_from_id.txt'
    if marker.read_text().strip() == boot:
        raise RuntimeError('A reboot is already required; this boot already contains a staged release')
    if Path('/run/ov5640_snapshot_download_attempted').read_text().strip() != boot:
        raise RuntimeError('Current boot firmware-load marker mismatch')
    import sys
    sys.path.insert(0, str(STAGE))
    from capture import verify_manifest
    manifest, staged = verify_manifest(STAGE / 'release_manifest.json')
    if manifest['design'].get('manual_sccb_version') != 1 or manifest['design'].get('post_init_sccb_version') != 1:
        raise RuntimeError('Candidate firmware contract mismatch')
    for kind, name in [('bit', 'ov5640_snapshot.bit'), ('hwh', 'ov5640_snapshot.hwh')]:
        if digest(staged[kind]) != manifest['files'][kind]['sha256']:
            raise RuntimeError('Staged hash mismatch: ' + name)
    current, _ = verify_manifest(BASE / 'release/release_manifest.json')
    if current['files']['bit']['sha256'] != OLD_BIT or current['files']['hwh']['sha256'] != OLD_HWH:
        raise RuntimeError('The loaded release is not the expected V14 pair')
    result = subprocess.run(['ps', '-eo', 'args='], text=True, capture_output=True, check=True)
    active = [line.strip() for line in result.stdout.splitlines()
              if ('sensor_probe.py' in line or 'capture.py' in line)
              and 'stage_v15.py' not in line and 'python -c' not in line]
    if active:
        raise RuntimeError('Capture process is active; refusing stage: ' + '; '.join(active))
    backup = BASE / ('backup_before_v15_checked_' + boot)
    backup.mkdir(exist_ok=False)
    shutil.copytree(BASE / 'release', backup / 'release')
    for source in (BASE / 'capture.py', Path('/boot/boot.py'), marker):
        target = backup / ('boot.py' if source == Path('/boot/boot.py') else source.relative_to(BASE))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if digest(source) != digest(target):
            raise RuntimeError('Backup mismatch: ' + str(source))
    incoming = BASE / ('.release_v15_incoming_' + boot)
    shutil.copytree(BASE / 'release', incoming)
    for name in FILES:
        shutil.copy2(STAGE / name, incoming / name)
        if digest(STAGE / name) != digest(incoming / name):
            raise RuntimeError('Incoming file mismatch: ' + name)
    manifest2, _ = verify_manifest(incoming / 'release_manifest.json')
    if manifest2['files']['bit']['sha256'] != digest(incoming / 'ov5640_snapshot.bit'):
        raise RuntimeError('Incoming bit/manifest mismatch')
    if manifest2['files']['hwh']['sha256'] != digest(incoming / 'ov5640_snapshot.hwh'):
        raise RuntimeError('Incoming HWH/manifest mismatch')
    shutil.copy2(STAGE / 'capture.py', BASE / 'capture.py')
    retired = BASE / ('.release_v14_retired_' + boot)
    release = BASE / 'release'
    release.rename(retired)
    try:
        incoming.rename(release)
    except BaseException:
        retired.rename(release)
        raise
    final_manifest, final_files = verify_manifest(release / 'release_manifest.json')
    if final_manifest['files']['bit']['sha256'] != digest(final_files['bit']):
        raise RuntimeError('Final bit validation failed')
    if final_manifest['files']['hwh']['sha256'] != digest(final_files['hwh']):
        raise RuntimeError('Final HWH validation failed')
    marker.write_text(boot + chr(10))
    record = dict(staged_from_boot=boot, backup=str(backup), old_release=retired.name,
                  release=str(release), files=final_manifest['files'], reboot_required=True,
                  firmware_downloaded=False)
    (STAGE / 'deployment.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))
    print('STAGED_REBOOT_REQUIRED')

if __name__ == '__main__':
    main()
