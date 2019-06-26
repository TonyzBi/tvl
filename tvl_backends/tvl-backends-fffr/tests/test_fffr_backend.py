import PIL.Image
import pytest
import torch
from numpy.testing import assert_allclose

from tvl_backends.fffr import FffrBackendFactory


def test_duration(backend):
    assert backend.duration == 2.0


def test_frame_rate(backend):
    assert backend.frame_rate == 25


def test_n_frames(backend):
    assert backend.n_frames == 50


def test_width(backend):
    assert backend.width == 1280


def test_height(backend):
    assert backend.height == 720


def test_read_frame(backend, first_frame_image):
    rgb = backend.read_frame()
    assert(rgb.size() == (3, 720, 1280))
    img = PIL.Image.fromarray(rgb.cpu().permute(1, 2, 0).numpy(), 'RGB')
    assert_allclose(img, first_frame_image, rtol=0, atol=50)


def test_eof(backend):
    backend.seek(2.0)
    with pytest.raises(EOFError):
        backend.read_frame()


def test_read_all_frames(backend):
    n_read = 0
    for i in range(1000):
        try:
            backend.read_frame()
            n_read += 1
        except EOFError:
            break
    assert n_read == 50


def test_seek(backend, mid_frame_image):
    backend.seek(1.0)
    rgb = backend.read_frame()
    img = PIL.Image.fromarray(rgb.cpu().permute(1, 2, 0).numpy(), 'RGB')
    assert_allclose(img, mid_frame_image, rtol=0, atol=50)


def test_memory_leakage(backend):
    """Check that the memory manager is not leaking memory."""
    device = backend.image_allocator.device
    if device.type == 'cuda':
        start_mem = torch.cuda.memory_allocated(device.index)
        for _ in range(5):
            backend.read_frame()
        end_mem = torch.cuda.memory_allocated(device.index)
        assert end_mem == start_mem
    else:
        for _ in range(5):
            backend.read_frame()
    assert len(backend.image_allocator.tensors) == 0


def test_read_frame_float32_cpu(video_filename, first_frame_image):
    backend = FffrBackendFactory().create(video_filename, 'cpu', torch.float32)
    rgb_frame = backend.read_frame()
    assert rgb_frame.shape == (3, 720, 1280)
    actual = PIL.Image.fromarray((rgb_frame * 255).byte().permute(1, 2, 0).numpy(), 'RGB')
    assert_allclose(actual, first_frame_image, atol=50)
