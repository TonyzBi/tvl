import numpy as np
import pyfffr
import torch

from tvl.backend import Backend, BackendFactory
from tvl_backends.fffr.memory import TorchImageAllocator


class FffrBackend(Backend):
    def __init__(self, filename, device, dtype):
        device = torch.device(device)
        if device.type == 'cuda':
            device_index = device.index
            if device_index is None:
                device_index = torch.cuda.current_device()
        else:
            device_index = -1

        allocator_dtype = dtype
        # The FFFR backend does not currently support direct conversion to float32 for software
        # decoding, so we will read as uint8 and do the data type conversion afterwards.
        if device.type == 'cpu' and dtype != torch.uint8:
            allocator_dtype = torch.uint8

        image_allocator = TorchImageAllocator(device, allocator_dtype)
        frame_reader = pyfffr.TvFFFrameReader(image_allocator, filename, device_index)
        # We need to hold a reference to image_allocator for at least as long as the
        # TvFFFrameReader that uses it is around, since we retain ownership of image_allocator.
        setattr(frame_reader, '__image_allocator_ref', image_allocator)

        self.image_allocator = image_allocator
        self.frame_reader = frame_reader
        self.dtype = dtype
        self._at_eof = False

    @property
    def duration(self):
        return self.frame_reader.get_duration()

    @property
    def frame_rate(self):
        return self.frame_reader.get_frame_rate()

    @property
    def n_frames(self):
        return self.frame_reader.get_number_of_frames()

    @property
    def width(self):
        return self.frame_reader.get_width()

    @property
    def height(self):
        return self.frame_reader.get_height()

    def seek(self, time_secs):
        try:
            self.frame_reader.seek(time_secs)
            self._at_eof = False
        except RuntimeError:
            if time_secs < self.duration - (1.0 / self.frame_rate + 1e-9):
                raise
            self._at_eof = True

    def _convert_frame(self, ptr):
        ptr = int(ptr)
        rgb_tensor = self.image_allocator.get_frame_tensor(ptr)
        self.image_allocator.free_frame(ptr)  # Release reference held by the memory manager.

        if self.dtype == torch.float32:
            if self.image_allocator.dtype != torch.float32:
                return rgb_tensor.to(self.dtype).div_(255)
            return rgb_tensor
        elif self.dtype == torch.uint8:
            return rgb_tensor
        raise NotImplementedError(f'Unsupported dtype: {self.dtype}')

    def read_frame(self):
        if self._at_eof:
            raise EOFError()

        ptr = self.frame_reader.read_frame()
        if not ptr:
            raise EOFError()

        return self._convert_frame(ptr)

    def _read_frames_by_index(self, indices):
        frame_indices = torch.tensor(indices, device='cpu', dtype=torch.int64)
        ptrs = torch.zeros(frame_indices.shape, device='cpu', dtype=torch.int64)
        n_frames_read = self.frame_reader.read_frames_by_index(
            frame_indices.data_ptr(), frame_indices.shape[0], ptrs.data_ptr())
        return [self._convert_frame(ptr) for ptr in ptrs[:n_frames_read].tolist()]

    def select_frames(self, frame_indices, seek_hint=3):
        if FffrBackendFactory._USE_FFFR_SELECT_FRAMES:
            sorted_frame_indices = np.unique(frame_indices)
            start_frame = sorted_frame_indices[0]
            self.seek_to_frame(start_frame)
            if self._at_eof:
                raise EOFError()
            frames = self._read_frames_by_index(sorted_frame_indices - start_frame)
            assert len(frames) == len(sorted_frame_indices), \
                'read_frames_by_index returned fewer frames than expected.'
            return frames
        else:
            return super().select_frames(frame_indices, seek_hint)


class FffrBackendFactory(BackendFactory):
    _USE_FFFR_SELECT_FRAMES = False

    def create(self, filename, device, dtype, backend_opts=None) -> FffrBackend:
        if backend_opts is None:
            backend_opts = {}
        return FffrBackend(filename, device, dtype, **backend_opts)
