#pragma once

#include "FFFrameReader.h"
#include "ImageAllocator.h"

#include <memory>
#include <string>
#include <cuda.h>

class TvFFFrameReader
{
public:
    TvFFFrameReader(ImageAllocator* image_allocator, const std::string& filename, int gpu_index, int out_width = 0,
        int out_height = 0);
    ~TvFFFrameReader() = default;

    std::string get_filename() const;
    int get_width() const;
    int get_height() const;
    double get_duration() const;
    double get_frame_rate() const;
    int64_t get_number_of_frames() const;
    void seek(float time_secs);

    uint8_t* read_frame();

private:
    static std::shared_ptr<std::remove_pointer<CUcontext>::type> _context;
    std::shared_ptr<Ffr::Stream> _stream = nullptr;
    ImageAllocator* _image_allocator = nullptr;
    std::string _filename;
    Ffr::PixelFormat _pixel_format;

    static bool init_context(int gpu_index);
};
