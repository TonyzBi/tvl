from pathlib import Path

import PIL.Image
import pytest

data_dir = Path(__file__).parent.parent.parent.parent.joinpath('data')


@pytest.fixture
def video_filename():
    return str(data_dir.joinpath('board_game-h264.mkv'))


@pytest.fixture
def first_frame_image():
    return PIL.Image.open(data_dir.joinpath('board_game_first.jpg'), 'r')


@pytest.fixture
def mid_frame_image():
    return PIL.Image.open(data_dir.joinpath('board_game_mid.jpg'), 'r')
