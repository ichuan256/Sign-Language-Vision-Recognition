# Sign Vision Lab

A local browser UI for one pre-segmented sign clip. It streams person/pose overlays and progress while processing, then returns the final top-5 DTW template matches. It is a prototype, not continuous sentence recognition.

## Run locally

From the repository root on the development PC:

```powershell
python -m pip install -r requirements-web.txt
python -m uvicorn webapp.app:app --host 127.0.0.1 --port 8000
```

The requirements install the local web layer plus NumPy/OpenCV DNN. For PYNQ-Z2, use a board-compatible OpenCV build rather than assuming that a desktop wheel works; run the benchmark/preflight on the target before deployment.

Open `http://127.0.0.1:8000`, choose an MP4/MOV/AVI/MKV clip, then select **开始识别**. The original file is previewed in the browser; the server streams annotated frames over WebSocket. Uploaded input is held in a per-job temporary directory and removed after inference; successful annotated output is retained temporarily. Only one video job runs at a time; the default upload cap is 512 MiB.

The classifier uses 8 uniformly sampled frames and emits its final class result after the clip finishes. Intermediate frame overlays and progress are streamed during processing; there are no per-frame sign labels. Person detection runs every 2 frames and pose estimation every 4 frames by default, with short-gap tracking between detections. The displayed DTW distance/similarity is not a calibrated probability.

After a successful run, the page also provides an H.264/MP4 video containing the per-frame person and pose overlays. It is silent (the input audio track is not copied), can be played in the result preview, and is kept in the local job directory for one hour before cleanup (or until the app shuts down). On supported desktop browsers the download button opens a Save As picker; other browsers use their normal download behavior and save-location settings. An OpenCV build without AVC/H.264 encoding support will report a processing error rather than produce a non-playable artifact.

A Windows x64 host processed the current 43-frame 200×250 cropped sample at 17.83 FPS with this schedule. This is not a full-frame or PYNQ-Z2 result; frame resolution, scene, capture/decode and board runtime will change throughput.

## Validation limits

The bundled template archive was built from cropped 200×250 material. This UI does not establish full-frame camera accuracy or PYNQ-Z2 speed. The ATK-OV5640 DVP capture path is not connected; the server accepts uploaded files, not a live DVP sensor or UVC camera. Bind to `127.0.0.1` unless authentication and an upload policy are added before exposing it to a network.
