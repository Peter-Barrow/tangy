#ifndef __std__
#define __std__

#include "base.h"

typedef u64 timetag;

typedef struct std {
    u8 channel;
    timetag timestamp;
} standard;

typedef f64 std_res;

typedef struct std_slice {
    usize length;
    u8* channel;
    timetag* timestamp;
} std_slice;

#define VEC_T timetag
#define VEC_NAME std_vec
#include "vector.h"

// typedef struct std_cc_result std_cc_result;
// struct std_cc_result {
//     std_res resolution;
//     f64 read_time;
//     usize total_records;
//     usize n_channels;
//     u8* channels;
//     vec_timetag* records;
// };

#define STUB std
#define T standard
#define TS timetag
#define RESOLUTION std_res
#define SLICE std_slice
#define TT_VECTOR vec_timetag
#define TT_VECTOR_INIT(C) std_vec_init(C)
#define TT_VECTOR_DEINIT(C) std_vec_deinit(C)
#define TT_VECTOR_PUSH(V_PTR, E) std_vec_push(V_PTR, E)
#define TT_VECTOR_RESET(V_PTR) std_vec_reset(V_PTR)
// #define CC_RESULT std_cc_result

#include "ring_buffers.h"

u64
std_conversion_factor(std_res resolution) {
    return 1;
}

u64
std_size_of() {
    u64 elem_size = sizeof(uint8_t) + sizeof(uint64_t);
    return elem_size;
}

inline standard
std_record_at(const std_buffer* const buffer, u64 absolute_index) {
    standard record = { .channel = buffer->ptrs.channel[absolute_index],
                        .timestamp = buffer->ptrs.timestamp[absolute_index] };
    return record;
}

inline timetag
std_timestamp_at(const std_buffer* const buffer, u64 absolute_index) {
    return buffer->ptrs.timestamp[absolute_index];
}

inline u8
std_channel_at(const std_buffer* const buffer, u64 absolute_index) {
    return buffer->ptrs.channel[absolute_index];
}

inline u64
std_arrival_time_at(const std_buffer* const buffer, u64 absolute_index) {
    return buffer->ptrs.timestamp[absolute_index];
}

inline u64
std_arrival_time_at_next(u64 conversion_factor, timetag timestamp) {
    return timestamp;
}

std_slice
std_init_base_ptrs(const std_buffer* const buffer) {
    std_slice slice = { 0 };
    u64 num_elems = *buffer->capacity;

    u64 channel_offset = sizeof(std_buffer_info);
    u64 timestamp_offset = channel_offset + (sizeof(u8) * num_elems);

    slice.length = num_elems;
    slice.channel = (u8*)buffer->map_ptr + channel_offset;
    slice.timestamp = (u64*)buffer->map_ptr + (timestamp_offset / 8);
    return slice;
}

// std_slice std_get_slice(const std_buffer *const buffer, const u64 capacity,
//                         u64 start, u64 stop) {
//
//     std_slice slice = std_init_base_ptrs(buffer, capacity);
//
//     slice.length = stop - start;
//     slice.channel += start;
//     slice.timestamp += start;
//     return slice;
// }

inline u64
std_bins_from_time(const std_res resolution, const f64 time) {
    return (u64)roundl(time / resolution);
}

inline f64
std_time_from_bins(const std_res resolution, const u64 bins) {
    return (f64)bins * resolution;
}

inline f64
std_to_time(standard record, std_res resolution) {
    return (f64)record.timestamp * resolution;
}

inline u64
std_as_bins(standard record, std_res resolution) {
    return (u64)roundl((f64)record.timestamp * resolution);
}

bool
std_equal(standard a, standard b) {
    return a.timestamp == b.timestamp;
}

histogram2D_coords
std_calculate_joint_histogram_coordinates(
  delay_histogram_measurement* measurement,
  timetag* timetags) {

    usize arrival_clock = timetags[measurement->idx_clock];
    usize arrival_signal = timetags[measurement->idx_signal];
    usize arrival_idler = timetags[measurement->idx_idler];

    histogram2D_coords point = {
        .x = (arrival_clock > arrival_idler) ? arrival_clock - arrival_idler
                                             : arrival_idler - arrival_clock,
        .y = (arrival_clock > arrival_signal) ? arrival_clock - arrival_signal
                                              : arrival_signal - arrival_clock,
    };

    return point;
}

void
std_dh_measurement_check(usize n_channels,
                         u8 clock,
                         u8 signal,
                         u8 idler,
                         u8* channels,
                         delay_histogram_measurement* config) {
    bool has_clock = false;
    bool has_signal = false;
    bool has_idler = false;

    u8 idx_clock = 0;
    u8 idx_signal = 0;
    u8 idx_idler = 0;

    for (usize i = 0; i < n_channels; i++) {
        if (channels[i] == clock) {
            has_clock = true;
            idx_clock = i;
        }

        if (channels[i] == signal) {
            has_signal = true;
            idx_signal = i;
        }

        if (channels[i] == idler) {
            has_idler = true;
            idx_idler = i;
        }
    }

    if (!(has_clock == true && has_signal == true && has_idler == true)) {
        config->ok = false;
        return;
    }

    config->idx_clock = idx_clock;
    config->idx_signal = idx_signal;
    config->idx_idler = idx_idler;
    return;
}

#endif
