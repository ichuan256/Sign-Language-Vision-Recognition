"""Create deterministic RTL vectors from the independent integer image oracle."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'project/board/vision_preprocess'))
from preprocess import AffineJob, affine_job, letterbox_job, roi_job, pack_rgb565_le
from preprocess import reference_rgb888, expand_rgb565, quantized_maps


def pattern(width, height, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    y, x = np.indices((height, width))
    image = np.stack(((x * 17 + y * 31) % 256, (x * 7 + y * 11) % 256,
                      (x * 37 + y * 3) % 256), axis=-1).astype(np.uint8)
    if width * height < 5000:
        image ^= rng.integers(0, 32, image.shape, dtype=np.uint8)
    return image


def cases():
    base = 0x01000000
    result = []
    def add(name, width, height, matrix, dw=None, dh=None, stride=None):
        result.append((name, affine_job(width, height, dw or width, dh or height, matrix,
                                        src_base=base, src_stride=stride)))
    identity = ((1, 0, 0), (0, 1, 0))
    add('identity_1x1', 1, 1, identity)
    add('identity_odd_padded_rows', 5, 3, identity, stride=16)
    add('fractional_black_border', 5, 4, ((.75, .125, -.5), (-.125, .875, .25)), 7, 6)
    add('translation_black_padding', 3, 2, ((1, 0, -2), (0, 1, -1)), 7, 5)
    add('negative_phase_half_tie', 3, 2, ((.5, 0, -1 / 64), (0, .5, -1 / 64)), 7, 5)
    add('negative_phase_below_tie', 3, 2, ((.5, 0, -1025 / 65536), (0, .5, -1025 / 65536)), 7, 5)
    add('fully_outside_no_reads', 3, 2, ((1, 0, -10), (0, 1, -10)), 4, 3)
    add('rotation_90_degrees', 9, 7, ((0, 1, 0), (-1, 0, 6)), 7, 9)
    result.append(('rotation_30_degrees', roi_job(29, 19, (.51, .47, .8, .7, math.pi / 6), 13, src_base=base)))
    add('upsample_single_pixel_border', 1, 1, ((.5, 0, -.5), (0, .5, -.5)), 3, 3)
    result.append(('positive_coordinate_no_32bit_wrap', AffineJob(base, 8, 4, 3, 4, 4,
                    0x7fffffff, 0x7fffffff, 0, 0, 65536, 0)))
    result.append(('negative_coordinate_no_32bit_wrap', AffineJob(base, 8, 4, 3, 4, 4,
                    -0x80000000, -0x80000000, 0, 0, 65536, 0)))
    add('source_width_4096_edge', 4096, 1, ((1, 0, 4094), (0, 0, 0)), 4, 1)
    add('source_height_4096_edge', 1, 4096, ((0, 0, 0), (0, 1, 4094)), 1, 4)
    result.append(('native_720p_letterbox_192', letterbox_job(1280, 720, src_base=base)))
    result.append(('native_720p_rotated_roi_224', roi_job(1280, 720, (.5, .5, .45, .7, .31), src_base=base)))
    return result


def generate(output, *, require_opencv=False):
    import numpy as np
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT / 'project'):
        raise ValueError('Keep generated artifacts inside project/')
    output.mkdir(parents=True, exist_ok=False)
    try:
        import cv2
    except ImportError:
        if require_opencv:
            raise RuntimeError('OpenCV oracle required but not available')
        cv2 = None
    entries = []
    # Independent hardware ROM oracle: NumPy performs actual float32 division.
    normalize = np.arange(256, dtype=np.float32) / np.float32(255)
    (output / 'normalize_expected.mem').write_text(
        ''.join(f'{int(value):08x}\n' for value in normalize.view(np.uint32)), encoding='ascii')
    for index, (name, job) in enumerate(cases()):
        image = pattern(job.src_width, job.src_height, 1028 + index)
        raw, stride = pack_rgb565_le(image, job.src_stride)
        expected = reference_rgb888(raw, job)
        cv_remap = None
        cv_warp = None
        if cv2 is not None:
            source = expand_rgb565(raw, job)
            qx, qy = quantized_maps(job)
            remapped = cv2.remap(source, qx.astype(np.float32) / 32,
                                qy.astype(np.float32) / 32, cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            difference = np.abs(expected.astype(np.int16) - remapped.astype(np.int16))
            cv_remap = int(difference.max())
            if cv_remap:
                raise AssertionError(f'{name}: integer reference differs from OpenCV quantized remap')
            warped = cv2.warpAffine(source, np.array(job.inverse_matrix),
                                    (job.dst_width, job.dst_height),
                                    flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                    borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
            difference = np.abs(expected.astype(np.int16) - warped.astype(np.int16))
            cv_warp = dict(max_abs_channel_error=int(difference.max()),
                           differing_pixels=int(np.any(difference, axis=-1).sum()),
                           total_pixels=job.dst_width * job.dst_height)
        config = output / f'case_{index}_cfg.mem'
        config.write_text(''.join(f'{value:08x}\n' for value in job.words()), encoding='ascii')
        input_file = output / f'case_{index}_input.mem'
        input_file.write_text(''.join(f'{int(value):08x}\n' for value in np.frombuffer(raw, dtype='<u4')), encoding='ascii')
        pixels = expected.reshape(-1, 3).astype(np.uint32)
        words = pixels[:, 0] | (pixels[:, 1] << 8) | (pixels[:, 2] << 16)
        expected_file = output / f'case_{index}_expected.mem'
        expected_file.write_text(''.join(f'{int(value):06x}\n' for value in words), encoding='ascii')
        fp32 = expected.astype(np.float32) / np.float32(255)
        (output / f'case_{index}_fp32_expected.mem').write_text(
            ''.join(f'{int(value):08x}\n' for value in fp32.reshape(-1).view(np.uint32)), encoding='ascii')
        entries.append(dict(index=index, name=name, job=dict(zip(job.__dataclass_fields__, job.words())),
                            source_bytes=len(raw), output_pixels=len(words), output_bytes=job.output_bytes,
                            source_sha256=hashlib.sha256(raw).hexdigest(),
                            expected_sha256=hashlib.sha256(expected.tobytes()).hexdigest(),
                            fp32_expected_sha256=hashlib.sha256(fp32.astype('<f4').tobytes()).hexdigest(),
                            opencv_quantized_remap_max_error=cv_remap, opencv_warp_comparison=cv_warp))
    (output / 'case_count.mem').write_text(f'{len(entries):08x}\n', encoding='ascii')
    report = dict(schema_version=2, seed_base=1028, cases=entries,
                  numpy_version=np.__version__, opencv_version=cv2.__version__ if cv2 is not None else None,
                  note='warpAffine comparison measures coordinate-quantization differences, not a promised bit-exact contract')
    (output / 'vectors.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-opencv', action='store_true')
    args = parser.parse_args()
    report = generate(args.output, require_opencv=args.require_opencv)
    print(json.dumps(dict(cases=len(report['cases']), opencv=report['opencv_version'],
                          output=str(args.output)), indent=2))


if __name__ == '__main__':
    main()
