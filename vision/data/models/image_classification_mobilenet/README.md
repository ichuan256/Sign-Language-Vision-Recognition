# MobileNetV2 visual backbone

This is the OpenCV Zoo MobileNetV2 ImageNet model, block-quantized to INT8. This project reads the 1280-D tensor before the ImageNet classifier (`onnx_node!GlobalAveragePool_97`) as a per-frame visual feature, L2-normalizes it, then matches clip sequences with DTW. It is a feature backbone, not a hand-sign classifier by itself.

Pinned OpenCV Zoo revision: `47534e27c9851bb1128ccc0102f1145e27f23f98`
Model: `image_classification_mobilenetv2_2022apr_int8bq.onnx`
LFS SHA-256: `3fe457eda49d71b664918ae87349bdb3e3815a56bb82cdb7f477bc83597f4313`
Model size: 3,872,948 bytes
Upstream model card: https://github.com/opencv/opencv_zoo/tree/47534e27c9851bb1128ccc0102f1145e27f23f98/models/image_classification_mobilenet
License: Apache-2.0; the full upstream license is retained at `vision/src/signrec/_vendor/opencv_zoo/LICENSE`.

Input frames are letterboxed to 224×224 after RGB ImageNet normalization; no frame content is cropped or stretched. Results trained with the current `vision/data/legacy/material/` clips are a cropped-domain prototype and must not be taken as full-frame/camera accuracy.
