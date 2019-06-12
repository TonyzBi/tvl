from pathlib import Path

import PIL.Image
import pytest
import torch

from tvl_backends.fffr import FffrBackendFactory

data_dir = Path(__file__).parent.parent.parent.parent.joinpath('data')

# Get the slow CUDA initialisation out of the way
for i in range(torch.cuda.device_count()):
    torch.empty(0).to(torch.device('cuda', i))


@pytest.fixture
def video_filename():
    return str(data_dir.joinpath('board_game-h264.mkv'))


@pytest.fixture
def first_frame_image():
    return PIL.Image.open(data_dir.joinpath('board_game_first.jpg'), 'r')


@pytest.fixture
def mid_frame_image():
    return PIL.Image.open(data_dir.joinpath('board_game_mid.jpg'), 'r')


@pytest.fixture
def cropped_video_filename():
    return str(data_dir.joinpath('board_game-h264-cropped.mkv'))


@pytest.fixture
def cropped_first_frame_image():
    return PIL.Image.open(data_dir.joinpath('board_game_first-cropped.jpg'), 'r')


@pytest.fixture(params=['cpu', 'cuda:0'])
def device(request):
    return request.param


@pytest.fixture
def backend(device, video_filename):
    return FffrBackendFactory().create(video_filename, device, torch.uint8)
