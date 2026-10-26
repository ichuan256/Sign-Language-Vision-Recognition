# -*- coding: utf-8 -*-
"""w2：以全画幅精剪模板启动 Sign Vision Lab 上位机。

用法（仓库根目录）：
  F:\\PLD\\.venv-vision\\Scripts\\python.exe -X utf8 webapp/run_fullframe_20261024.py

浏览器打开 http://127.0.0.1:8001
模板：models/sign_templates_fullframe_20261024.npz（video/done 全画幅精剪 636 条/440 类）
不改动曹同学任何文件：模板路径经 pipeline_factory 注入；特征层名在构造时按模型实测解析。
"""
import sys
from pathlib import Path

import uvicorn

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vision/src"))

from fastapi import HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402

from vision.webapp.app import create_app  # noqa: E402
from vision.webapp.pipeline import SignRecognitionPipeline  # noqa: E402
from signrec.features import DEFAULT_BACKBONE_PATH  # noqa: E402
from signrec.person_detector import DEFAULT_MODEL_PATH  # noqa: E402
from signrec.pose_estimator import DEFAULT_POSE_MODEL_PATH  # noqa: E402

TEMPLATES = ROOT / "vision/data/models" / "sign_templates_fullframe_20261024.npz"

# 片段库：第 8/9/10 课精剪（Tomcat 提交），供 UI 快速切换
LESSON_DIRS = {
    "8": "第八课购物_NL08_85条_20261022",
    "9": "第九课聚会_NL09_102条_20261022",
    "10": "第十课旅游_NL10_100条_20261022",
}
DONE = ROOT / "vision/video" / "done" / "Tomcat"


def scan_library() -> list[dict]:
    """启动时扫一次：每条的 id 即列表索引。"""
    clips = []
    for lesson, dirname in LESSON_DIRS.items():
        base = DONE / dirname
        if not base.is_dir():
            continue
        for mp4 in sorted(base.rglob("*.mp4")):
            clips.append({"id": len(clips), "lesson": lesson,
                          "label": mp4.parent.name, "name": mp4.stem,
                          "path": mp4})
    return clips


LIBRARY = scan_library()


def factory() -> SignRecognitionPipeline:
    return SignRecognitionPipeline(
        person_model=DEFAULT_MODEL_PATH,
        pose_model=DEFAULT_POSE_MODEL_PATH,
        backbone_model=DEFAULT_BACKBONE_PATH,
        templates_path=TEMPLATES,
    )


if __name__ == "__main__":
    app = create_app(pipeline_factory=factory)

    @app.get("/api/clips")
    def list_clips() -> dict:
        return {"clips": [{"id": c["id"], "lesson": c["lesson"],
                           "label": c["label"], "name": c["name"]}
                          for c in LIBRARY]}

    @app.get("/api/clips/{clip_id}/file")
    def clip_file(clip_id: int) -> FileResponse:
        if clip_id < 0 or clip_id >= len(LIBRARY):
            raise HTTPException(404, "clip not in library")
        return FileResponse(LIBRARY[clip_id]["path"], media_type="video/mp4")

    print(f"templates: {TEMPLATES}")
    print(f"library clips: {len(LIBRARY)}")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
