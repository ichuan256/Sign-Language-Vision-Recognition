"""Keypoint extraction over FrameSource streams."""
def __getattr__(name):
    if name=='HolisticTracker':
        from .holistic import HolisticTracker
        return HolisticTracker
    raise AttributeError(name)

__all__ = ["HolisticTracker"]
