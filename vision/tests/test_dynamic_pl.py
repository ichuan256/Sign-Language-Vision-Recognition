"""Bounded latest-only scheduling and binary ROI framing."""
import io
import pytest
from vision.keypoints.dynamic_pl import LatestSlot
from project.board.keypoints.stream_hand_board import read_exact

def test_pending_roi_replaced_instead_of_backlog():
    slot=LatestSlot()
    slot.put(dict(frame_id=1));slot.put(dict(frame_id=2));slot.put(dict(frame_id=3))
    assert slot.take()==dict(frame_id=3)
    assert slot.dropped==2 and slot.take(timeout=0) is None

def test_roi_framing_reads_partial_chunks_and_rejects_truncation():
    class Partial(io.BytesIO):
        def read(self,n):return super().read(min(n,3))
    assert read_exact(Partial(b'1234567890'),10)==b'1234567890'
    with pytest.raises(EOFError,match='Truncated'):
        read_exact(Partial(b'123'),4)
