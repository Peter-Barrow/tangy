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
#define FIELD_PTRS std_slice
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
    // slice.timestamp = (u64*)buffer->map_ptr + (timestamp_offset / 8);
    slice.timestamp = (u64*)(&(buffer->map_ptr[channel_offset + num_elems + 1]));
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

usize
std_buffer_slice(const std_buffer* const buffer,
                 FIELD_PTRS* ptrs,
                 usize start,
                 usize stop) {
    if (ptrs->length == 0) {
        return 0;
    }

    if ((stop - start) != ptrs->length) {
        return 0;
    }

    // printf("Start:(%lu)\tStop:(%lu)\n", start, stop);

    usize capacity = *(buffer->capacity);
    circular_iterator iter = { 0 };
    if (iterator_init(&iter, capacity, start, stop) == -1) {
        return 0;
    }

    // printf("iter count:\t%lu\n", iter.count);
    // printf("lower\t->\t(%lu) : (%lu)\n", iter.lower.index, iter.lower.count);
    // printf("upper\t->\t(%lu) : (%lu)\n", iter.upper.index, iter.upper.count);

    usize i = iter.lower.index;
    for (usize j = 0; j < ptrs->length; j++) {
        // printf("i:%lu\tj:%lu ->\t(%d\t%lu)->\t(%d\t%lu)\n",
        //        i,
        //        j,
        //        ptrs->channel[j],
        //        ptrs->timestamp[j],
        //        buffer->ptrs.channel[i],
        //        buffer->ptrs.timestamp[i]);
        ptrs->channel[j] = buffer->ptrs.channel[i];
        ptrs->timestamp[j] = buffer->ptrs.timestamp[i];
        // printf("i:%lu\tj:%lu ->\t(%d\t%lu)->\t(%d\t%lu)\n",
        //        i,
        //        j,
        //        ptrs->channel[j],
        //        ptrs->timestamp[j],
        //        buffer->ptrs.channel[i],
        //        buffer->ptrs.timestamp[i]);
        i = next(&iter);
    }

    return i;
}

usize
std_buffer_push(std_buffer* const buffer,
                FIELD_PTRS slice,
                usize start,
                usize stop) {
    if (slice.length == 0) {
        return 0;
    }

    if ((stop - start) != slice.length) {
        return 0;
    }

    u64 capacity = *buffer->capacity;
    u64 start_abs = start % capacity;

    // u64 stop_abs =
    //   start > capacity ? stop % capacity : start_abs + slice.length;

    u64 stop_abs = stop % capacity;

    // printf("Start:(%lu)\tStop:(%lu)\n", start, stop);
    // printf("Start:(%lu)\tStop:(%lu)\n", start_abs, stop_abs);

    u64 total = stop - start;

    u64 mid_stop = start_abs > stop_abs ? capacity : stop_abs;

    if ((*buffer->count) == 0) {
        mid_stop = total > capacity ? capacity : total;
    }

    // u64 mid_stop = capacity;

    // if (!(start_abs > stop_abs)) {
    //     mid_stop = stop_abs;
    // }

    // if ((*buffer->count == 0) & (!(total > capacity))) {
    //     mid_stop = total;
    // }

    // printf("Mid stop:(%lu)\n", mid_stop);

    u64 i = 0;
    for (i = 0; (i + start_abs) < mid_stop; i++) {
        buffer->ptrs.channel[start_abs + i] = slice.channel[i];
        buffer->ptrs.timestamp[start_abs + i] = slice.timestamp[i];
        // printf("i:%lu, j:%lu ->\t(%d\t%lu)->\t(%d\t%lu)\n",
        //        i,
        //        start_abs + i,
        //        slice.channel[start_abs + i],
        //        slice.timestamp[start_abs + i],
        //        buffer->ptrs.channel[i],
        //        buffer->ptrs.timestamp[i]);
    }

    u64 count = i;
    // printf("Count:(%lu)\tTotal:(%lu)\n", count, total);
    if (count < total) {
        // printf("second half\n");
        i = 0;
        for (i = 0; i < stop_abs; i++) {
            buffer->ptrs.channel[i] = slice.channel[count];
            buffer->ptrs.timestamp[i] = slice.timestamp[count];
            // printf("i:%lu ->\t(%d\t%lu)->\t(%d\t%lu)\n",
            //        i,
            //        slice.channel[count],
            //        slice.timestamp[count],
            //        buffer->ptrs.channel[i],
            //        buffer->ptrs.timestamp[i]);
            count += 1;
        }
        // count += i;
    }

    // for (i = 0; i < capacity; i++) {
    //     printf(
    //       "[%lu]\t(%d\t%lu)\n", i, buffer->ptrs.channel[i], buffer->ptrs.timestamp[i]);
    // }

    // printf("Count:\t%lu\n", *buffer->count);
    // printf("Count:\t%lu\n", slice.length);

    *buffer->count += count;

    return count;
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

#undef STUB
#undef T
#undef TS
#undef RESOLUTION
#undef SLICE
#undef FIELD_PTRS
#undef TT_VECTOR
#undef TT_VECTOR_INI
#undef TT_VECTOR_DEINI
#undef TT_VECTOR_PUSH
#undef TT_VECTOR_RESET
