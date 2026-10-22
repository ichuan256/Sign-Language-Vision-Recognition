# MediaPipe person detector

This model processes the complete input frame after aspect-preserving letterboxing to 224×224. The upstream output's first box is a face-region box, not a full-person box; it also returns four body anchors (hip center, full-body point, shoulder center, upper-body point). The code derives coarse upper/full-body ROIs from those anchors for visualization or later feature extraction. It does not return wrists or finger landmarks, and the original frame remains unchanged.

Model: `person_detection_mediapipe_2023mar.onnx`

Source repository: https://github.com/opencv/opencv_zoo/tree/47534e27c9851bb1128ccc0102f1145e27f23f98/models/person_detection_mediapipe
Model LFS SHA-256: `47fd5599d6fa17608f03e0eb0ae230baa6e597d7e8a2c8199fe00abea55a701f`
Model size: 11,990,159 bytes
License: Apache-2.0; see the vendored OpenCV Zoo license at `src/signrec/_vendor/opencv_zoo/LICENSE`.

The Python inference wrapper is vendored unchanged from the same pinned OpenCV Zoo revision at `src/signrec/_vendor/opencv_zoo/mp_persondet.py`.
