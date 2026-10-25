# Cropped-material sign-template prototype

This experimental archive uses the existing cropped clips, not full-frame camera recordings. It is a reproducible baseline only and must not be treated as camera-domain accuracy.

2026-10-25 workspace cleanup: the template archive and its historical results remain unchanged, but 224 source clips were removed from the workspace. Only one real test fixture remains. The old 225-row source manifest is provenance metadata, not a complete locally available dataset; a full feature rebuild requires the original media again. `build_templates.py` now requires explicit `--manifest` and `--output` arguments.

- Archive: `sign_templates_cropped.npz`
- Source manifest: `data/legacy/material/dataset_manifest_20261020.csv`
- Input clips: 225 videos / 132 labels; 77 labels have only one video.
- Feature model: OpenCV Zoo MobileNetV2 INT8, 1280-D GlobalAveragePool features, L2 normalized.
- Temporal matching: cosine-distance DTW over 8 uniformly sampled frames per clip.
- Rebuild: `python scripts/build_templates.py --manifest data/legacy/material/dataset_manifest_20261020.csv --output models/sign_templates_cropped.npz --frames 8 --overwrite`
- Inference: `python scripts/infer_sign.py <video.mp4> --templates models/sign_templates_cropped.npz --frames 8 --top-k 5`
- Evaluation: `python scripts/evaluate_templates.py --templates models/sign_templates_cropped.npz`
- Archive SHA-256: `D35C2B62C631B71705C8324196A23D572F3D5809BA9B1D3D9617C8EDD2B395E0`

## Current leave-one-video-out result

On clips from the same current material collection, leave-one-video-out covers 148 clips in 55 classes with at least two examples. The baseline scored top-1 accuracy 0.6419 and macro-F1 0.6116; 0.2365 of held-out queries were nearest to a singleton-class template. These are within-corpus results only: most classes occur in a single source part, so this does not measure cross-signer or full-frame camera transfer.

The returned `similarity` is an exponential transform of DTW distance, not a calibrated probability. A same-corpus threshold sweep gave:

| max DTW distance | known coverage | accuracy on accepted known clips | false accept rate on singleton pseudo-unknowns |
| ---: | ---: | ---: | ---: |
| 0.01 | 0.68% | 100.00% | 0.00% |
| 0.02 | 18.24% | 74.07% | 0.00% |
| 0.03 | 62.84% | 79.57% | 48.05% |
| 0.05 | 99.32% | 64.63% | 100.00% |

Singleton clips are only same-corpus pseudo-unknowns. The sharp coverage/rejection tradeoff means no threshold is selected for deployment; calibrate it on separate known and unknown camera clips.
