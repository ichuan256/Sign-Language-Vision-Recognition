"""Read-only workspace video inventory; creates a fresh evidence directory only.

No media is changed. SHA-256 identifies byte-identical files, not independent
performances. ffprobe reads metadata only and does not verify full decoding.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

VIDEO_EXTENSIONS = {'.mp4', '.m4v', '.mov', '.mkv', '.avi', '.webm', '.wmv',
                    '.mpg', '.mpeg', '.m2v', '.mts', '.m2ts', '.ts', '.flv',
                    '.f4v', '.3gp', '.3g2', '.vob', '.ogv', '.rm', '.rmvb',
                    '.asf', '.mpv', '.hevc', '.h264', '.264', '.h265', '.265'}
ARCHIVE_EXTENSIONS = {'.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz'}


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def norm(value):
    return str(value or '').replace('\\', '/').lstrip('./')


def basename(value):
    return norm(value).rsplit('/', 1)[-1]


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    with path.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def linked(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def scan(root):
    files, skipped, errors = [], [], []
    def onerror(error):
        errors.append(str(error))
    for current, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        parent = Path(current)
        keep = []
        for name in sorted(dirs):
            path = parent / name
            if name == '.git' or linked(path):
                skipped.append(path.relative_to(root).as_posix())
            else:
                keep.append(name)
        dirs[:] = keep
        for name in sorted(names):
            path = parent / name
            if linked(path):
                skipped.append(path.relative_to(root).as_posix())
                continue
            files.append(path)
    return files, skipped, errors


def directory_group(relative):
    parts = relative.split('/')
    if parts[:2] in (['video', 'done'], ['video', 'raw'], ['video', 'inbox'], ['video', 'archive']):
        # Keep shallow category folders distinguishable from contributor batches.
        return '/'.join(parts[:4] if parts[2:3] in (['wsy'], ['Tomcat']) else parts[:3])
    if parts[:2] == ['data', 'legacy']:
        return '/'.join(parts[:3])
    return parts[0] if len(parts) > 1 else '(workspace root)'


def probe(path, executable):
    if not executable:
        return {'probe_status': 'unknown_no_ffprobe'}
    try:
        result = subprocess.run([executable, '-v', 'error', '-show_entries',
            'format=duration:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames,duration',
            '-of', 'json', str(path)], capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=45)
        if result.returncode:
            return {'probe_status': 'error', 'probe_error': result.stderr.strip()[:1000]}
        data = json.loads(result.stdout)
        streams = data.get('streams', [])
        video = next((s for s in streams if s.get('codec_type') == 'video'), None)
        if not video:
            return {'probe_status': 'no_video_stream'}
        rate = video.get('avg_frame_rate') or video.get('r_frame_rate')
        try:
            numerator, denominator = rate.split('/')
            fps = float(numerator) / float(denominator)
        except (ValueError, ZeroDivisionError, AttributeError):
            fps = ''
        return {'probe_status': 'metadata_ok', 'duration_s': data.get('format', {}).get('duration', video.get('duration', '')),
                'width': video.get('width', ''), 'height': video.get('height', ''),
                'fps': fps, 'fps_fraction': rate or '', 'codec': video.get('codec_name', ''),
                'declared_frames': video.get('nb_frames', ''),
                'audio_streams': sum(s.get('codec_type') == 'audio' for s in streams)}
    except Exception as error:
        return {'probe_status': 'error', 'probe_error': str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, help='Must not exist; defaults to a timestamp under analysis/materials')
    parser.add_argument('--ffprobe', help='Existing ffprobe executable; never downloads tools')
    parser.add_argument('--probe-workers', type=int, default=2)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / 'analysis' / 'materials' / datetime.now().strftime('%Y%m%d_%H%M%S')).resolve()
    if not output.is_relative_to(root):
        parser.error('Output must stay inside the workspace')
    if output.exists():
        parser.error('Output already exists; choose a new output directory')
    started = datetime.now(timezone.utc).isoformat()
    all_files, skipped, scan_errors = scan(root)
    videos = [p for p in all_files if p.suffix.lower() in VIDEO_EXTENSIONS]
    archives = [p for p in all_files if p.suffix.lower() in ARCHIVE_EXTENSIONS]
    bundled_probes = [root / 'tools/portable/losslesscut/resources/ffprobe.exe',
                      root / '工具/losslesscut/resources/ffprobe.exe']
    ffprobe = args.ffprobe or next((str(p) for p in bundled_probes if p.is_file()), None) or shutil.which('ffprobe')
    if ffprobe and not Path(ffprobe).is_file():
        parser.error('ffprobe executable does not exist')
    git = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True)
    tracked = set(git.stdout.decode('utf-8', errors='replace').split('\0')) if git.returncode == 0 else set()
    manifest_path = root / 'data/manifests/manifest_fullframe_20261024.csv'
    audit_path = root / 'analysis/dataset/label_source_audit_20261025.json'
    manifest = read_csv(manifest_path)
    current_names = {basename(row['输出路径']).casefold() for row in manifest}
    audit = json.loads(audit_path.read_text(encoding='utf-8-sig'))
    audit_records = {norm(r['path']): r for r in audit.get('records', [])}
    expected_hashes = {r['sha256'].lower() for r in audit_records.values() if r.get('sha256')}
    historical_hashes, historical_names, historical_paths = set(), set(), set()
    historical_manifest_sources, csv_errors = [], []
    for path in all_files:
        if path.suffix.lower() != '.csv' or path == manifest_path:
            continue
        try:
            source_rows = read_csv(path)
            references = 0
            for row in source_rows:
                for key, value in row.items():
                    if not value or not isinstance(value, str):
                        continue
                    if key and ('sha256' in key.lower() or key.lower() == 'sha') and re.fullmatch('[0-9a-fA-F]{64}', value.strip()):
                        historical_hashes.add(value.strip().lower())
                    if Path(value).suffix.lower() in VIDEO_EXTENSIONS and (('/' in value) or ('\\' in value)):
                        historical_paths.add(norm(value))
                        historical_names.add(basename(value).casefold())
                        references += 1
            if references:
                historical_manifest_sources.append({'path': path.relative_to(root).as_posix(), 'rows': len(source_rows), 'media_references': references})
        except (OSError, UnicodeError, csv.Error) as error:
            csv_errors.append({'path': path.relative_to(root).as_posix(), 'error': str(error)})
    inventory, hash_errors, by_hash, by_name = [], [], defaultdict(list), defaultdict(list)
    total_bytes = sum(p.stat().st_size for p in videos)
    print(f'Scanned {len(videos)} video files, {total_bytes:,} bytes; hashing every file', flush=True)
    last_progress = time.monotonic()
    for index, path in enumerate(videos, 1):
        relative = path.relative_to(root).as_posix()
        stat = path.stat()
        item = {'relative_path': relative, 'bytes': stat.st_size,
                'mtime_utc': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                'directory_group': directory_group(relative), 'git_tracked': relative in tracked,
                'extension': path.suffix.lower(), 'sha256': '', 'hash_status': 'ok'}
        try:
            item['sha256'] = sha256(path)
            after = path.stat()
            if (stat.st_size, stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise RuntimeError('file changed while hashing')
        except Exception as error:
            item['hash_status'], item['sha256'] = 'error', ''
            hash_errors.append({'path': relative, 'error': str(error)})
        name = path.name.casefold()
        item['current_636_content'] = item['sha256'] in expected_hashes if item['sha256'] else False
        item['historical_sha_reference'] = item['sha256'] in historical_hashes if item['sha256'] else False
        item['historical_path_reference'] = relative in historical_paths
        item['historical_name_reference'] = name in historical_names
        item['current_636_name_reference'] = name in current_names
        item['reference_class'] = ('current_636_sha_verified' if item['current_636_content'] else
            'historical_sha_verified' if item['historical_sha_reference'] else
            'historical_path_reference' if item['historical_path_reference'] else
            'current_636_name_candidate_only' if item['current_636_name_reference'] else
            'historical_name_candidate_only' if item['historical_name_reference'] else 'unreferenced_candidate_review')
        lesson = re.search(r'(?:NL|P)(\d{2})[_\-]', path.name, re.IGNORECASE)
        item['filename_lesson_hint'] = lesson.group(1) if lesson else ''
        item['shallow_done_layout'] = relative.startswith('video/done/') and len(relative.split('/')) == 4
        inventory.append(item)
        by_name[name].append(item)
        if item['sha256']:
            by_hash[item['sha256']].append(item)
        if index % 100 == 0 or time.monotonic() - last_progress > 25:
            print(f'Hashed {index}/{len(videos)} files', flush=True)
            last_progress = time.monotonic()
    print(f'Hash complete; probing {len(by_hash)} unique contents using {ffprobe or "no tool"}', flush=True)
    with ThreadPoolExecutor(max_workers=max(1, min(args.probe_workers, 4))) as pool:
        futures = {pool.submit(probe, root / rows[0]['relative_path'], ffprobe): digest for digest, rows in by_hash.items()}
        for index, future in enumerate(as_completed(futures), 1):
            for item in by_hash[futures[future]]:
                item.update(future.result())
            if index % 100 == 0 or time.monotonic() - last_progress > 25:
                print(f'Probed {index}/{len(by_hash)} unique contents', flush=True)
                last_progress = time.monotonic()
    by_path = {r['relative_path']: r for r in inventory}
    coverage, referenced_paths = [], set()
    for index, row in enumerate(manifest, 1):
        path = norm(row['输出路径'])
        prior = audit_records.get(path, {})
        expected = (prior.get('sha256') or '').lower()
        matches = by_hash.get(expected, []) if expected else []
        direct = by_path.get(path)
        names = by_name.get(basename(path).casefold(), [])
        suffix_candidates = [r for r in names if r['relative_path'].endswith('/'.join(path.split('/')[-2:]))]
        verified = bool(direct and expected and direct['sha256'] == expected)
        status = ('direct_sha_verified' if verified else 'relocated_sha_verified' if matches and not direct else
            'direct_mismatch_sha_elsewhere' if matches else 'direct_sha_mismatch' if direct and expected else
            'direct_unverified_no_expected_sha' if direct else 'name_candidate_only' if names else 'missing')
        coverage.append({'manifest_row': index, 'label': row['类别'], 'sample_id': row['样本编号'],
            'part': row.get('part', ''), 'manifest_path': path, 'expected_sha256': expected,
            'expected_sha_source': 'analysis/dataset/label_source_audit_20261025.json:records' if expected else '',
            'direct_path_exists': bool(direct), 'direct_sha256': direct['sha256'] if direct else '',
            'status': status, 'sha_verified_candidate_count': len(matches),
            'sha_verified_candidates': json.dumps([r['relative_path'] for r in matches], ensure_ascii=False),
            'same_name_candidates': json.dumps([r['relative_path'] for r in names], ensure_ascii=False),
            'label_filename_suffix_candidates': json.dumps([r['relative_path'] for r in suffix_candidates], ensure_ascii=False)})
        referenced_paths.update(r['relative_path'] for r in matches)
    duplicates = []
    for digest, rows in by_hash.items():
        for item in rows:
            item['same_content_file_count'] = len(rows)
        if len(rows) > 1:
            duplicates.append({'sha256': digest, 'file_count': len(rows), 'bytes_per_copy': rows[0]['bytes'],
                'total_bytes': sum(r['bytes'] for r in rows), 'theoretical_redundant_bytes': (len(rows)-1)*rows[0]['bytes'],
                'tracked_copies': sum(r['git_tracked'] for r in rows),
                'paths': json.dumps([r['relative_path'] for r in rows], ensure_ascii=False),
                'current_636_content': digest in expected_hashes})
    groups = []
    for group in sorted({r['directory_group'] for r in inventory}):
        rows = [r for r in inventory if r['directory_group'] == group]
        hashes = {r['sha256'] for r in rows if r['sha256']}
        groups.append({'directory_group': group, 'files': len(rows), 'bytes': sum(r['bytes'] for r in rows),
            'unique_contents': len(hashes), 'unique_content_bytes': sum(by_hash[h][0]['bytes'] for h in hashes),
            'tracked_files': sum(r['git_tracked'] for r in rows),
            'reference_classes': dict(Counter(r['reference_class'] for r in rows))})
    unique_bytes = sum(rows[0]['bytes'] for rows in by_hash.values())
    summary = {'inventory_version': 1, 'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
        'workspace_root': str(root), 'output_directory': str(output),
        'scan_policy': 'os.walk includes ignored/local files; .git, all directory junctions/symlinks and file symlinks excluded',
        'video_extensions': sorted(VIDEO_EXTENSIONS), 'skipped_links_and_git': skipped, 'scan_errors': scan_errors,
        'video_files': len(inventory), 'video_bytes': total_bytes, 'unique_contents': len(by_hash),
        'unique_content_bytes': unique_bytes, 'exact_duplicate_groups': len(duplicates),
        'files_in_duplicate_groups': sum(r['file_count'] for r in duplicates),
        'redundant_copies': sum(r['file_count']-1 for r in duplicates),
        'theoretical_redundant_bytes': sum(r['theoretical_redundant_bytes'] for r in duplicates),
        'deduplication_boundary': 'Theoretical byte upper bound only; deleting any copy may break live/historical manifests. No deletions or moves performed.',
        'git_ls_files_ok': git.returncode == 0, 'git_tracked_video_files': sum(r['git_tracked'] for r in inventory),
        'hash_errors': hash_errors, 'historical_csv_read_errors': csv_errors, 'historical_manifest_sources': historical_manifest_sources,
        'full_manifest': {'path': manifest_path.relative_to(root).as_posix(), 'sha256': sha256(manifest_path), 'rows': len(manifest),
            'expected_rows': 636, 'matches_expected_rows': len(manifest) == 636,
            'audit_record_count': len(audit_records), 'audit_sha256': sha256(audit_path),
            'audit_declared_manifest_sha256_matches': audit.get('full_manifest', {}).get('sha256') == sha256(manifest_path),
            'coverage_counts': dict(Counter(r['status'] for r in coverage)),
            'direct_exists': sum(r['direct_path_exists'] for r in coverage),
            'rows_with_sha_verified_content': sum(r['sha_verified_candidate_count'] > 0 for r in coverage),
            'missing_content_rows': sum(r['sha_verified_candidate_count'] == 0 for r in coverage),
            'rows_with_multiple_verified_copies': sum(r['sha_verified_candidate_count'] > 1 for r in coverage)},
        'reference_class_file_counts': dict(Counter(r['reference_class'] for r in inventory)),
        'reference_class_unique_contents': {key: len({r['sha256'] for r in inventory if r['reference_class'] == key and r['sha256']})
            for key in sorted({r['reference_class'] for r in inventory})},
        'candidate_boundary': 'No current-manifest or known historical hash/path/name reference means candidate for review, not proven newly added. mtime is descriptive only; names/paths are weaker than SHA.',
        'shallow_video_done_files': sum(r['shallow_done_layout'] for r in inventory),
        'shallow_video_done_lesson_hints': dict(Counter(r['filename_lesson_hint'] or 'unknown' for r in inventory if r['shallow_done_layout'])),
        'directory_groups': groups, 'ffprobe': ffprobe,
        'probe_unique_status_counts': dict(Counter(rows[0].get('probe_status', 'not_probed') for rows in by_hash.values())),
        'probe_boundary': 'Container/stream metadata only; no full frame decoding, semantic label validation or visual acceptance.',
        'unexpanded_archives': [{'relative_path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size,
            'git_tracked': p.relative_to(root).as_posix() in tracked} for p in archives]}
    assert len(inventory) == len(videos)
    assert sum(g['files'] for g in groups) == len(inventory)
    assert sum(summary['full_manifest']['coverage_counts'].values()) == len(manifest)
    assert len(inventory) - len(by_hash) - len(hash_errors) == summary['redundant_copies']
    assert total_bytes - unique_bytes - sum(r['bytes'] for r in inventory if not r['sha256']) == summary['theoretical_redundant_bytes']
    output.mkdir(parents=True, exist_ok=False)
    fields = ['relative_path', 'bytes', 'mtime_utc', 'directory_group', 'extension', 'git_tracked', 'sha256', 'hash_status',
        'same_content_file_count', 'reference_class', 'current_636_content', 'historical_sha_reference',
        'historical_path_reference', 'historical_name_reference', 'current_636_name_reference', 'filename_lesson_hint', 'shallow_done_layout',
        'probe_status', 'duration_s', 'width', 'height', 'fps', 'fps_fraction', 'codec', 'declared_frames', 'audio_streams', 'probe_error']
    write_csv(output / 'inventory.csv', inventory, fields)
    write_csv(output / 'duplicate_groups.csv', duplicates, ['sha256', 'file_count', 'bytes_per_copy', 'total_bytes',
        'theoretical_redundant_bytes', 'tracked_copies', 'current_636_content', 'paths'])
    write_csv(output / 'manifest_coverage.csv', coverage, list(coverage[0]) if coverage else ['manifest_row'])
    with (output / 'summary.json').open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    # Verify serialized CSV row counts, not just in-memory lengths.
    for filename, expected in [('inventory.csv', len(inventory)), ('duplicate_groups.csv', len(duplicates)), ('manifest_coverage.csv', len(manifest))]:
        assert len(read_csv(output / filename)) == expected, filename
    print(json.dumps({'output': str(output), 'video_files': len(inventory), 'unique_contents': len(by_hash),
        'duplicate_groups': len(duplicates), 'manifest_coverage': summary['full_manifest']['coverage_counts'],
        'hash_errors': len(hash_errors), 'probe_status': summary['probe_unique_status_counts']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
