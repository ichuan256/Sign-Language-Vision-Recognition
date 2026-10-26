# MediaPipe Pose localizer

This optional second stage consumes the face-region box and body anchors from the person detector, then returns 33 body keypoints, 6 auxiliary points, a person mask, and a confidence score. It is used only to refine shoulder/elbow/wrist/hand-anchor regions; it is not the sign classifier and does not provide detailed finger joints.

Model: `pose_estimation_mediapipe_2023mar_int8bq.onnx`
Pinned OpenCV Zoo revision: `47534e27c9851bb1128ccc0102f1145e27f23f98`
Model LFS SHA-256: `1848ea80f657f4620e0de160594f598ed8107c9e7785d0be74f65cf15aa6deb1`
Model size: 1,694,896 bytes
License: Apache-2.0; see `LICENSE` in this folder and the vendored wrapper at `vision/src/signrec/_vendor/opencv_zoo/mp_pose.py`.

The source frame is passed unchanged; the upstream pose model forms an in-memory ROI from the detector's hip/full-body anchors. The current bundled clips are cropped 200×250, so ROI sizes must be revalidated on uncropped camera frames.
