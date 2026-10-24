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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from webapp.app import create_app  # noqa: E402
from webapp.pipeline import SignRecognitionPipeline  # noqa: E402
from signrec.features import DEFAULT_BACKBONE_PATH  # noqa: E402
from signrec.person_detector import DEFAULT_MODEL_PATH  # noqa: E402
from signrec.pose_estimator import DEFAULT_POSE_MODEL_PATH  # noqa: E402

TEMPLATES = ROOT / "models" / "sign_templates_fullframe_20261024.npz"


def factory() -> SignRecognitionPipeline:
    return SignRecognitionPipeline(
        person_model=DEFAULT_MODEL_PATH,
        pose_model=DEFAULT_POSE_MODEL_PATH,
        backbone_model=DEFAULT_BACKBONE_PATH,
        templates_path=TEMPLATES,
    )


if __name__ == "__main__":
    app = create_app(pipeline_factory=factory)
    print(f"templates: {TEMPLATES}")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
