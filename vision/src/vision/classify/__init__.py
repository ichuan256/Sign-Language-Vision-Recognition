"""Classification baselines: mask-aware DTW templates, dynamic segmentation."""
from .dtw import TemplateClassifier, frame_costs, dtw_distance
from .segment import wrist_energy, detect_segments

__all__ = ["TemplateClassifier", "frame_costs", "dtw_distance",
           "wrist_energy", "detect_segments"]
