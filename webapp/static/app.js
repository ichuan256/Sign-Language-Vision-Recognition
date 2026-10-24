const $ = (selector) => document.querySelector(selector);
const fileInput = $("#videoInput");
const dropzone = $("#dropzone");
const runButton = $("#runButton");
const cancelButton = $("#cancelButton");
const sourceVideo = $("#sourceVideo");
const processedVideo = $("#processedVideo");
const downloadButton = $("#downloadButton");
const processedFrame = $("#processedFrame");
const placeholder = $("#mediaPlaceholder");
const mediaStage = $("#mediaStage");
const frameOverlay = $("#frameOverlay");
const resultEmpty = $("#resultEmpty");
const resultContent = $("#resultContent");
let selectedFile = null;
let previewUrl = null;
let activeJobId = null;
let socket = null;
let uploadRequest = null;
let currentView = "original";
let hasProcessedFrame = false;
let annotatedVideoUrl = null;
let annotatedVideoFilename = "annotated.mp4";
const EMPTY_PIXEL = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=";

function toast(message, kind) {
  const node = $("#toast");
  node.textContent = message;
  node.className = "toast" + (kind ? " " + kind : "");
  node.hidden = false;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { node.hidden = true; }, 3500);
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return "";
  return bytes >= 1024 * 1024 ? (bytes / (1024 * 1024)).toFixed(1) + " MB" : Math.max(1, Math.round(bytes / 1024)) + " KB";
}

function setStatus(text, className) {
  const node = $("#jobStatus");
  node.textContent = text;
  node.className = className || "";
}

function setProgress(value) {
  const percent = Math.max(0, Math.min(100, Math.round((value || 0) * 100)));
  $("#progressFill").style.width = percent + "%";
  $("#progressPercent").textContent = percent + "%";
}

function selectFile(file) {
  if (!file) return;
  const allowed = [".mp4", ".mov", ".avi", ".mkv"].some((suffix) => file.name.toLowerCase().endsWith(suffix));
  if (!allowed) { toast("请选择 MP4、MOV、AVI 或 MKV 视频。", "error"); return; }
  selectedFile = file;
  const name = $("#dropTitle");
  name.replaceChildren(document.createTextNode("已选择 "));
  const bold = document.createElement("b");
  bold.textContent = file.name;
  name.append(bold);
  $("#dropMeta").textContent = "单段已剪切视频 · 本机临时处理";
  $("#fileName").textContent = file.name;
  $("#fileSize").textContent = formatBytes(file.size);
  $(".file-dot").classList.add("ready");
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  clearAnnotatedVideo();
  previewUrl = URL.createObjectURL(file);
  sourceVideo.src = previewUrl;
  sourceVideo.hidden = false;
  hasProcessedFrame = false;
  processedFrame.src = EMPTY_PIXEL;
  processedFrame.hidden = true;
  frameOverlay.hidden = true;
  placeholder.hidden = true;
  currentView = "original";
  setActiveTab();
  runButton.disabled = false;
  resetResult();
  setStatus("已就绪");
}

function setActiveTab() {
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === currentView);
  });
  const compare = Boolean(selectedFile && currentView === "compare");
  mediaStage.classList.toggle("compare", compare);
  const showOriginal = Boolean(selectedFile && (currentView === "original" || compare));
  const showResultVideo = Boolean(annotatedVideoUrl && (currentView === "processed" || compare));
  const showProcessedFrame = Boolean(!annotatedVideoUrl && hasProcessedFrame && (currentView === "processed" || compare));
  sourceVideo.hidden = !showOriginal;
  processedVideo.hidden = !showResultVideo;
  processedFrame.hidden = !showProcessedFrame;
  frameOverlay.hidden = !showProcessedFrame || compare;
  placeholder.hidden = showOriginal || showResultVideo || showProcessedFrame;
  downloadButton.hidden = !annotatedVideoUrl;
  downloadButton.disabled = !annotatedVideoUrl;
}

function syncComparePlay() {
  // 并列对比：原视频与标注视频同起点同步播放（静音以满足浏览器自动播放策略）
  if (!annotatedVideoUrl || currentView !== "compare") return;
  for (const video of [sourceVideo, processedVideo]) {
    video.currentTime = 0;
    video.muted = true;
  }
  sourceVideo.play().catch(() => {});
  processedVideo.play().catch(() => {});
}

function mirrorCompareControl(source, target) {
  // 任一视频被拖动/暂停/播放时，另一个跟随（仅并列对比模式生效）
  source.addEventListener("play", () => {
    if (currentView === "compare" && annotatedVideoUrl) target.play().catch(() => {});
  });
  source.addEventListener("pause", () => {
    if (currentView === "compare" && annotatedVideoUrl) target.pause();
  });
  source.addEventListener("seeked", () => {
    if (currentView === "compare" && annotatedVideoUrl
        && Math.abs(target.currentTime - source.currentTime) > 0.15) {
      target.currentTime = source.currentTime;
    }
  });
}
mirrorCompareControl(sourceVideo, processedVideo);
mirrorCompareControl(processedVideo, sourceVideo);
window.setInterval(() => {
  // 播放漂移纠偏：差异超 0.25s 时把标注视频拉回齐
  if (currentView === "compare" && annotatedVideoUrl && !sourceVideo.paused
      && Math.abs(sourceVideo.currentTime - processedVideo.currentTime) > 0.25) {
    processedVideo.currentTime = sourceVideo.currentTime;
  }
}, 500);

function clearAnnotatedVideo() {
  processedVideo.pause();
  processedVideo.removeAttribute("src");
  processedVideo.load();
  annotatedVideoUrl = null;
  annotatedVideoFilename = "annotated.mp4";
  downloadButton.hidden = true;
  downloadButton.disabled = true;
}

function resetResult() {
  clearAnnotatedVideo();
  hasProcessedFrame = false;
  processedFrame.src = EMPTY_PIXEL;
  frameOverlay.hidden = true;
  $("#mediaHint").textContent = "识别过程中查看处理帧；完成后可播放标注视频";
  setActiveTab();
  resultEmpty.hidden = false;
  resultContent.hidden = true;
  $("#classifyStep").classList.remove("active", "done");
  $("#classifyStep .pipeline-state").textContent = "○";
  $("#frameMetric").textContent = "—";
  $("#fpsMetric").textContent = "— FPS";
  $("#personMetric").textContent = "— / —";
  setProgress(0);
}

fileInput.addEventListener("change", (event) => selectFile(event.target.files[0]));
dropzone.addEventListener("dragover", (event) => { event.preventDefault(); dropzone.classList.add("dragging"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragging"));
dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragging");
  selectFile(event.dataTransfer.files[0]);
});
document.querySelectorAll(".view-tab").forEach((button) => {
  button.addEventListener("click", () => {
    currentView = button.dataset.view;
    setActiveTab();
    if (currentView === "compare") syncComparePlay();
  });
});
runButton.addEventListener("click", startJob);
cancelButton.addEventListener("click", cancelJob);
downloadButton.addEventListener("click", downloadAnnotatedVideo);

function startJob() {
  if (!selectedFile || activeJobId) return;
  resetResult();
  runButton.disabled = true;
  cancelButton.disabled = false;
  setStatus("上传中…");
  $("#progressLabel").textContent = "上传进度";
  const form = new FormData();
  form.append("file", selectedFile);
  uploadRequest = new XMLHttpRequest();
  uploadRequest.open("POST", "/api/jobs");
  uploadRequest.upload.onprogress = (event) => { if (event.lengthComputable) setProgress(event.loaded / event.total); };
  uploadRequest.onerror = () => finishWithError("上传失败，请确认本地识别服务正在运行。");
  uploadRequest.onload = () => {
    if (uploadRequest.status < 200 || uploadRequest.status >= 300) {
      let detail = "无法创建识别任务";
      try { detail = JSON.parse(uploadRequest.responseText).detail || detail; } catch (_) {}
      finishWithError(detail);
      return;
    }
    const payload = JSON.parse(uploadRequest.responseText);
    activeJobId = payload.job_id;
    currentView = "processed";
    setActiveTab();
    $("#progressLabel").textContent = "识别进度";
    $("#classifyStep").classList.add("active");
    setStatus("排队中");
    connectJob(payload.job_id);
  };
  uploadRequest.send(form);
}

function connectJob(jobId) {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(scheme + "://" + location.host + "/ws/jobs/" + jobId);
  socket.onmessage = (message) => {
    const event = JSON.parse(message.data);
    if (event.type === "snapshot") { updateSnapshot(event); return; }
    if (event.type === "frame") {
      processedFrame.src = "data:image/jpeg;base64," + event.image_base64;
      hasProcessedFrame = true;
      processedFrame.hidden = false;
      frameOverlay.hidden = false;
      $("#frameLabel").textContent = (event.people || 0) + " 人体 · " + (event.poses || 0) + " 姿态";
      $("#frameCount").textContent = (event.frame_index + 1) + " / " + event.total_frames;
      if (currentView === "processed") setActiveTab();
      updateMetrics(event);
      setProgress(event.progress);
      setStatus("处理中", "running");
      return;
    }
    if (event.type === "progress") { setProgress(event.progress); updateMetrics(event); return; }
    if (event.type === "status") {
      if (event.status === "cancelling") setStatus("正在取消…");
      else if (event.status === "processing") setStatus("处理中", "running");
      return;
    }
    if (event.type === "completed") {
      if (event.result) renderResult(event.result, activeJobId);
      else if (event.predictions) renderResult(event, activeJobId);
      setProgress(1);
      setStatus("完成", "done");
      $("#classifyStep").classList.remove("active");
      $("#classifyStep").classList.add("done");
      $("#classifyStep .pipeline-state").textContent = "●";
      finishControls();
      return;
    }
    if (event.type === "error") { finishWithError(event.error || "处理失败"); return; }
    if (event.type === "cancelled") { setStatus("已取消"); finishControls(); }
  };
  socket.onerror = () => toast("预览连接中断；尝试读取任务状态。", "error");
  socket.onclose = () => { if (activeJobId) fetchJob(jobId); };
}

function updateSnapshot(snapshot) {
  setProgress(snapshot.progress);
  updateMetrics(snapshot);
  if (snapshot.status === "processing") setStatus("处理中", "running");
  else if (snapshot.status === "completed") {
    if (snapshot.result) renderResult(snapshot.result, snapshot.job_id || activeJobId);
    setStatus("完成", "done");
    $("#classifyStep").classList.remove("active");
    $("#classifyStep").classList.add("done");
    $("#classifyStep .pipeline-state").textContent = "●";
    finishControls();
  } else if (snapshot.status === "error") finishWithError(snapshot.error || "处理失败");
  else if (snapshot.status === "cancelled") { setStatus("已取消"); finishControls(); }
}

async function fetchJob(jobId) {
  try {
    const response = await fetch("/api/jobs/" + jobId);
    if (response.ok) updateSnapshot(await response.json());
  } catch (_) {}
}

function updateMetrics(event) {
  if (event.total_frames) $("#frameMetric").textContent = (event.frame_index + 1) + " / " + event.total_frames;
  if (Number.isFinite(event.processing_fps)) $("#fpsMetric").textContent = event.processing_fps.toFixed(1) + " FPS";
  if (event.people !== undefined || event.poses !== undefined) $("#personMetric").textContent = (event.people || 0) + " / " + (event.poses || 0);
}

function renderResult(result, jobId = activeJobId) {
  const candidates = result.predictions || [];
  const videoUrl = result.video_url || (jobId ? "/api/jobs/" + encodeURIComponent(jobId) + "/video" : null);
  if (videoUrl) {
    annotatedVideoUrl = videoUrl;
    const sourceName = selectedFile ? selectedFile.name.replace(/\.[^.]+$/, "") : "video";
    annotatedVideoFilename = result.video_filename || ((sourceName || "video") + "-annotated.mp4");
    processedVideo.src = annotatedVideoUrl;
    processedVideo.load();
    if (currentView !== "compare") currentView = "processed";
    $("#mediaHint").textContent = "识别完成 · 标注视频可播放/下载（无音轨，保留 1 小时）";
    setActiveTab();
    syncComparePlay();
  }
  if (!candidates.length) { toast("没有生成候选结果。", "error"); return; }
  resultEmpty.hidden = true;
  resultContent.hidden = false;
  $("#winnerLabel").textContent = candidates[0].label;
  const list = $("#candidateList");
  list.replaceChildren();
  candidates.slice(1, 5).forEach((item, index) => {
    const row = document.createElement("div"); row.className = "candidate-row";
    const rank = document.createElement("span"); rank.className = "rank"; rank.textContent = "0" + (index + 2);
    const label = document.createElement("span"); label.className = "label"; label.textContent = item.label;
    const distance = document.createElement("span"); distance.className = "distance"; distance.textContent = "DTW " + Number(item.distance).toFixed(3);
    row.append(rank, label, distance); list.append(row);
  });
  if (result.result_domain) toast("识别完成：当前是裁剪素材域实验结果。", "");
}

async function downloadAnnotatedVideo() {
  if (!annotatedVideoUrl) return;
  if (!window.isSecureContext || typeof window.showSaveFilePicker !== "function") {
    const link = document.createElement("a");
    link.href = annotatedVideoUrl + "?download=true";
    link.download = annotatedVideoFilename;
    document.body.append(link);
    link.click();
    link.remove();
    toast("已开始下载；保存位置由浏览器下载设置决定。", "");
    return;
  }

  try {
    const handle = await window.showSaveFilePicker({
      suggestedName: annotatedVideoFilename,
      types: [{ description: "MP4 视频", accept: { "video/mp4": [".mp4"] } }],
    });
    const response = await fetch(annotatedVideoUrl);
    if (!response.ok || !response.body) throw new Error("无法读取标注视频");
    const writable = await handle.createWritable();
    await response.body.pipeTo(writable);
    toast("标注视频已保存。", "");
  } catch (error) {
    if (error && error.name === "AbortError") return;
    toast("保存失败：" + (error.message || "请重试"), "error");
  }
}

async function cancelJob() {
  if (!activeJobId) return;
  try { await fetch("/api/jobs/" + activeJobId + "/cancel", { method: "POST" }); } catch (_) {}
  setStatus("正在取消…");
}

function finishWithError(message) {
  setStatus("处理失败", "error");
  toast(message, "error");
  finishControls();
}

function finishControls() {
  activeJobId = null;
  runButton.disabled = !selectedFile;
  cancelButton.disabled = true;
  uploadRequest = null;
  if (socket) { socket.close(); socket = null; }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    const ready = health.status === "assets-present";
    $("#healthDot").classList.toggle("offline", !ready);
    $("#healthText").textContent = ready ? "模型文件齐备" : (health.status === "opencv-dnn-unavailable" ? "OpenCV DNN 不可用" : "模型文件缺失");
    $("#backendNote").textContent = ready ? (health.inference_loaded ? "推理模型已加载 · 本机临时处理" : "首次识别时加载模型 · 本机临时处理") : "检查 OpenCV DNN 与 models/ 资产";
    if (!ready) toast("当前 OpenCV DNN 或模型文件不齐，请检查运行环境。", "error");
  } catch (_) {
    $("#healthDot").classList.add("offline");
    $("#healthText").textContent = "服务未连接";
    $("#backendNote").textContent = "请在项目根目录启动本地服务";
  }
}
checkHealth();
