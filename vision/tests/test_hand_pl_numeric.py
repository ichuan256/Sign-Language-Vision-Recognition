"""Numerical contracts; no TensorFlow, HLS tool, board or camera required."""
import numpy as np
import pytest

from project.scripts.keypoints.import_tflite_hand import conv_kernel, depthwise_kernel
from project.scripts.keypoints.fixed_hand_reference import quantize, rescale, fractional_bits
from project.scripts.keypoints.prepare_hand_rois import canonical_roi
from project.scripts.keypoints.run_tile_hls import rounded_shift, first_layer_vector
import json


def test_conv_layout():
    source = np.arange(2*3*3*4).reshape(2,3,3,4)
    kernel = conv_kernel(source)
    assert kernel.shape == (3,3,4,2)
    assert kernel[1,2,3,0] == source[0,1,2,3]


def test_depthwise_layout_and_multiplier():
    source = np.arange(1*3*3*6).reshape(1,3,3,6)
    kernel = depthwise_kernel(source,3,2)
    assert kernel.shape == (3,3,3,2)
    assert kernel[1,2,2,1] == source[0,1,2,5]
    with pytest.raises(ValueError):
        depthwise_kernel(source,4,2)


def test_round_nearest_even_signed():
    raw = np.array([1,3,5,7,-1,-3,-5,-7])
    expected = np.array([0,2,2,4,0,-2,-2,-4])
    assert np.array_equal(rescale(raw,1,0)[0],expected)
    assert [rounded_shift(v,1) for v in raw] == expected.tolist()


def test_saturation_and_left_shift():
    assert rounded_shift(40000,0) == 32767
    assert rounded_shift(-40000,0) == -32768
    assert rounded_shift(3,-2) == 12
    codes,clipped = quantize([-10,0,10],4,8)
    assert codes.tolist() == [-128,0,127]
    assert clipped == 2


def test_per_channel_fraction_broadcast():
    peak = np.array([1.,6.])
    fractions = fractional_bits(peak,16)
    codes,clipped = quantize(np.ones((3,2)),fractions,16)
    assert fractions.tolist() == [14,12]
    assert codes[0].tolist() == [16384,4096]
    assert clipped == 0


def test_canonical_roi_inverse_maps_wrist_upward():
    image = np.full((200,200,3),[10,20,30],np.uint8)
    hand = np.zeros((21,3),np.float32)
    hand[:,0] = np.linspace(.4,.6,21)
    hand[:,1] = np.linspace(.7,.3,21)
    hand[0,:2] = [.5,.8]
    hand[9,:2] = [.5,.4]
    roi,inverse = canonical_roi(image,hand)
    assert roi.shape == (224,224,3)
    assert roi.dtype == np.float32
    assert 0<=roi.min()<=roi.max()<=1
    affine = np.linalg.inv(np.vstack([inverse,[0,0,1]]))[:2]
    wrist = affine@np.r_[hand[0,:2]*200,1]
    mcp = affine@np.r_[hand[9,:2]*200,1]
    assert mcp[1]<wrist[1]
    assert abs(mcp[0]-wrist[0])<1e-5


def test_canonical_roi_rejects_invalid_points():
    with pytest.raises(ValueError):
        canonical_roi(np.zeros((20,20,3),np.uint8),np.full((21,3),np.nan))


def test_first_layer_probe_takes_16_of_24_channels(tmp_path):
    specs = [dict(kind='InputLayer',fraction=0),
             dict(kind='Conv2D',name='conv',fraction=0,weight_fraction=[0]*24,
                  padding='same',dilation=[1,1],output_shape=[1,112,112,24],strides=[2,2])]
    (tmp_path/'graph.json').write_text(json.dumps(specs),encoding='utf-8')
    np.savez(tmp_path/'weights.npz',conv_kernel=np.ones((3,3,3,24),np.int16),conv_bias_float=np.zeros(24))
    np.savez(tmp_path/'roi.npz',roi_rgb=np.ones((1,224,224,3),np.float32),validation_indices=[0])
    m,n,k,a,b,bias,shift,expected = first_layer_vector(tmp_path,tmp_path/'roi.npz')
    assert (m,n,k)==(16,16,27)
    assert np.all(expected==27)
