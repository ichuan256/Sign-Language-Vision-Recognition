"""Audio subtitle and video queue logic, independent of FPGA configuration."""
import json
import hashlib
import threading
import unicodedata
from collections import deque
from pathlib import Path
from urllib.request import build_opener, ProxyHandler
from urllib.parse import quote


def normalize(text):
    return ''.join(c for c in text if not c.isspace() and
                   not unicodedata.category(c).startswith('P'))


class VideoLexicon:
    def __init__(self, manifest):
        manifest = Path(manifest).resolve()
        data = json.loads(manifest.read_text(encoding='utf-8-sig'))
        self.manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.entries = []
        self.sequences = {}
        self.asset_paths = []
        self.asset_source = '本机视频'
        seen = set()
        def asset(item):
            path = (manifest.parent / item['file']).resolve()
            if data.get('asset_base_url'):
                digest = item['sha256']
                if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                    raise ValueError('Invalid asset hash')
                cache = (manifest.parent / data.get('asset_cache_dir', '.sd_cache')).resolve()
                cache.mkdir(parents=True, exist_ok=True)
                path = cache / (digest + '.mp4')
                cached = (data.get('prefer_verified_cache', False) and path.is_file() and
                          hashlib.sha256(path.read_bytes()).hexdigest() == digest)
                if not cached:
                    with build_opener(ProxyHandler({})).open(
                            data['asset_base_url'] + quote(item['file']), timeout=10) as response:
                        payload = response.read(16 * 1024 * 1024 + 1)
                    if hashlib.sha256(payload).hexdigest() != digest:
                        raise ValueError('SD asset hash mismatch: ' + item['file'])
                    path.write_bytes(payload)
                self.asset_source = ('板卡 SD 素材，SHA校验缓存播放' if data.get('prefer_verified_cache', False)
                                     else '板卡 SD 素材，启动时读取并校验，电脑缓存播放')
            if not path.is_file():
                raise ValueError('Video does not exist: %s' % path)
            self.asset_paths.append(path)
            return path

        for item in data['clips']:
            parts = item.get('sequence', [item])
            if not isinstance(parts, list) or not parts:
                raise ValueError('Empty or invalid playback sequence')
            paths = [asset(part) for part in parts]
            for phrase in item['phrases']:
                key = normalize(phrase)
                if not key or key in seen:
                    raise ValueError('Empty or duplicate phrase: %s' % phrase)
                seen.add(key)
                label = item.get('label', phrase)
                self.entries.append((key, paths[0], label))
                self.sequences[key] = [{'phrase': key, 'path': str(path), 'label': label}
                                       for path in paths]
        self.entries.sort(key=lambda entry: len(entry[0]), reverse=True)

    def match(self, text):
        text = normalize(text)
        clips, missing = [], []
        position = 0
        while position < len(text):
            match = next((x for x in self.entries if text.startswith(x[0], position)), None)
            if match:
                phrase, path, label = match
                clips.extend(getattr(self, 'sequences', {}).get(phrase,
                    [{'phrase': phrase, 'path': str(path), 'label': label}]))
                position += len(phrase)
            else:
                missing.append(text[position])
                position += 1
        return clips, ''.join(missing)


class Session:
    def __init__(self, lexicon, limit=4):
        self.lexicon = lexicon
        self.limit = limit
        self.lock = threading.RLock()
        self.jobs = deque()
        self.state = dict(status='等待启动语音识别', partial='', final='',
                          utterance_id=0, playing='', playback_text='', missing='',
                          error='', source='', queued=0, completed=0, video_frames=0,
                          clip_time_ms=0)
        self.state['asset_source'] = lexicon.asset_source
        entries = getattr(lexicon, 'entries', ())
        self.state['lexicon_phrases'] = len(entries)
        paths = getattr(lexicon, 'asset_paths', [e[1] for e in entries])
        self.state['lexicon_videos'] = len({str(p) for p in paths})
        self.state['lexicon_manifest_sha256'] = getattr(lexicon, 'manifest_sha256', '')

    def update(self, **values):
        with self.lock:
            self.state.update(values)

    def partial(self, text):
        self.update(partial=text)

    def final(self, text):
        text = text.strip()
        if not normalize(text):
            return
        clips, missing = self.lexicon.match(text)
        with self.lock:
            self.state['utterance_id'] += 1
            self.state.update(final=text, partial='', missing=missing)
            if clips:
                if len(self.jobs) >= self.limit:
                    self.state['error'] = '播放队列已满；本句未加入，请等候后重说'
                else:
                    self.jobs.append(dict(text=text, clips=clips,
                                          utterance_id=self.state['utterance_id']))
                    self.state['error'] = ''
            self.state['queued'] = len(self.jobs)

    def pop(self):
        with self.lock:
            if not self.jobs:
                return None
            job = self.jobs.popleft()
            self.state['queued'] = len(self.jobs)
            return job

    def snapshot(self):
        with self.lock:
            return dict(self.state)
