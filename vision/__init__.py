"""Workspace import anchor; implementation lives in vision/src/vision.

Keeps python -m vision.keypoints / vision.m1 / vision.webapp usable from the
repository root while source code, data and models are physically separated.
"""
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parent.parent
SOURCE_ROOT=REPO_ROOT/'vision/src/vision'
__path__.insert(0,str(SOURCE_ROOT))
