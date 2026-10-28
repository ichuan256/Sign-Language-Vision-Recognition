import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from loop_core import Session, VideoLexicon


class SDCacheTests(unittest.TestCase):
    def setup_manifest(self, folder, prefer=True):
        payload=b'content verified on SD'
        digest=hashlib.sha256(payload).hexdigest()
        manifest=folder/'lexicon.json'
        manifest.write_text(json.dumps(dict(asset_base_url='http://127.0.0.1:1/assets/',
            asset_cache_dir='playback_cache',prefer_verified_cache=prefer,
            clips=[dict(phrases=['你好'],file='new.mp4',sha256=digest,label='你好')])),encoding='utf-8')
        cache=folder/'playback_cache';cache.mkdir()
        target=cache/(digest+'.mp4')
        return manifest,target,payload

    def test_matching_cache_avoids_network_and_matches_phrase(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest,target,payload=self.setup_manifest(Path(folder))
            target.write_bytes(payload)
            with patch('loop_core.build_opener',side_effect=AssertionError('Network must not be used')):
                lex=VideoLexicon(manifest)
            clips,missing=lex.match('你好！')
            self.assertEqual(missing,'');self.assertEqual(Path(clips[0]['path']),target)

    def test_changed_cache_cannot_be_trusted(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest,target,payload=self.setup_manifest(Path(folder))
            target.write_bytes(b'tampered')
            with patch('loop_core.build_opener') as opener:
                opener.return_value.open.return_value.__enter__.return_value.read.return_value=payload
                VideoLexicon(manifest)
            self.assertEqual(target.read_bytes(),payload)

    def test_default_still_checks_SD_even_if_cache_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest,target,payload=self.setup_manifest(Path(folder),prefer=False)
            target.write_bytes(payload)
            with patch('loop_core.build_opener') as opener:
                opener.return_value.open.return_value.__enter__.return_value.read.return_value=b'changed SD file'
                with self.assertRaisesRegex(ValueError,'SD asset hash mismatch'):
                    VideoLexicon(manifest)

    def test_sentence_cycles_expand_in_source_order(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest,target,payload=self.setup_manifest(Path(folder))
            target.write_bytes(payload)
            second=b'second source cycle';digest=hashlib.sha256(second).hexdigest()
            second_path=target.parent/(digest+'.mp4');second_path.write_bytes(second)
            data=json.loads(manifest.read_text())
            first=data['clips'][0]
            first['sequence']=[dict(file=first['file'],sha256=first['sha256']),
                               dict(file='cycle2.mp4',sha256=digest)]
            manifest.write_text(json.dumps(data),encoding='utf-8')
            with patch('loop_core.build_opener',side_effect=AssertionError('No download')):
                lex=VideoLexicon(manifest)
            clips,missing=lex.match('你好！')
            self.assertEqual(missing,'')
            self.assertEqual([Path(x['path']) for x in clips],[target,second_path])
            session=Session(lex)
            self.assertEqual(session.snapshot()['lexicon_videos'],2)
            session.final('你好！')
            self.assertEqual([Path(x['path']) for x in session.pop()['clips']],[target,second_path])


if __name__=='__main__':unittest.main()
