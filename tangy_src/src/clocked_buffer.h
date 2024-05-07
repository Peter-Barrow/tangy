#ifndef __clk__
#define __clk__

#include "base.h"
#include "vector_impls.h"

typedef struct clk_timetag {
    u64 clock;
    u64 delta;
} clk_timetag;

typedef struct clk {
    u8 channel;
    clk_timetag timestamp;
} clocked;

typedef struct clk_res {
    f64 coarse;
    f64 fine;
} clk_res;

typedef struct clk_slice {
    usize length;
    u8* channel;
    clk_timetag* timestamp;
} clk_slice;

typedef struct clk_field_ptrs clk_field_ptrs;
struct clk_field_ptrs {
    usize length;
    u8* channels;
    u64* clocks;
    u64* deltas;
};

#define VEC_T clk_timetag
typedef struct clk_timetag_slice clk_timetag_slice;
struct clk_timetag_slice {
    u64* clock;
    u64* delta;
};
#define VEC_T_PTRS clk_timetag_slice
#define VEC_NAME clk_vec
#include "multi_vector.h"

vec_clk_timetag*
clk_vec_init(size capacity) {

    vec_clk_timetag* new_vector =
      (vec_clk_timetag*)malloc(sizeof(vec_clk_timetag));
    if (new_vector != NULL) {
        new_vector->length = 0;
        new_vector->capacity = 0;
        new_vector->data.clock = NULL;
        new_vector->data.delta = NULL;
    }

    u64* new_clocks = (u64*)malloc(sizeof(u64) * capacity);
    if (new_clocks != NULL) {
        new_vector->capacity = capacity;
        new_vector->data.clock = new_clocks;
    }

    u64* new_deltas = (u64*)malloc(sizeof(u64) * capacity);
    if (new_deltas != NULL) {
        new_vector->capacity = capacity;
        new_vector->data.delta = new_deltas;
    }

    return new_vector;
}

vec_clk_timetag*
clk_vec_deinit(vec_clk_timetag* multivec) {
    free(multivec->data.clock);
    free(multivec->data.delta);
    free(multivec);
    multivec = NULL;
    return multivec;
}

void
clk_vec_reset(vec_clk_timetag* multivec) {
    multivec->length = 0;
}

#define GROWTH_FACTOR 2

bool
clk_vec_grow(vec_clk_timetag* multivec) {
    if (multivec->data.clock == NULL) {
        return false;
    }

    if (multivec->data.delta == NULL) {
        return false;
    }

    size new_capacity = multivec->capacity * GROWTH_FACTOR;
    size total_bytes = sizeof(u64) * new_capacity;

    u64* new_clocks = (u64*)realloc(multivec->data.clock, total_bytes);
    if (new_clocks == NULL) {
        return false;
    }

    u64* new_deltas = (u64*)realloc(multivec->data.delta, total_bytes);
    if (new_deltas == NULL) {
        return false;
    }

    multivec->data.clock = new_clocks;
    multivec->data.delta = new_deltas;
    multivec->capacity = new_capacity;

    return true;
}

void
clk_vec_push(vec_clk_timetag* multivec, clk_timetag value) {
    if (!((multivec->length) <= (multivec->capacity - 1))) {
        clk_vec_grow(multivec);
    }
    multivec->data.clock[multivec->length] = value.clock;
    multivec->data.delta[multivec->length] = value.delta;
    multivec->length++;
    return;
}

/* now to pass these functions as required definitions to ring_buffers.h */

// typedef struct clk_cc_result clk_cc_result;
// struct clk_cc_result {
//     clk_res resolution;
//     f64 read_time;
//     usize total_records;
//     usize n_channels;
//     u8* channels;
//     vec_clk_timetag* records;
// };

#define STUB clk
#define T clocked
#define TS clk_timetag
#define RESOLUTION clk_res
#define SLICE clk_slice
#define FIELD_PTRS clk_field_ptrs
#define TT_VECTOR vec_clk_timetag
#define TT_VECTOR_INIT(C) clk_vec_init(C)
#define TT_VECTOR_DEINIT(C) clk_vec_deinit(C)
#define TT_VECTOR_PUSH(V_PTR, E) clk_vec_push(V_PTR, E)
#define TT_VECTOR_RESET(V_PTR) clk_vec_reset(V_PTR)
// #define CC_RESULT clk_cc_result

#include "ring_buffers.h"

inline u64
clk_conversion_factor(clk_res resolution) {
    u64 factor = (u64)round(resolution.coarse / resolution.fine);
    // u64 factor = (u64)round(resolution.coarse / resolution.fine);
    // printf("factor:\t%lu\n", factor);
    return factor;
}

u64
clk_size_of() {
    u64 elem_size = sizeof(u8) + sizeof(u64) + sizeof(u64);
    return elem_size;
}

clocked
clk_record_at(const clk_buffer* const buffer, u64 absolute_index) {
    clocked record = { .channel = buffer->ptrs.channel[absolute_index],
                       .timestamp = buffer->ptrs.timestamp[absolute_index] };
    return record;
}

inline clk_timetag
clk_timestamp_at(const clk_buffer* const buffer, u64 absolute_index) {
    return buffer->ptrs.timestamp[absolute_index];
}

inline u8
clk_channel_at(const clk_buffer* const buffer, u64 absolute_index) {
    return buffer->ptrs.channel[absolute_index];
}

u64
clk_arrival_time_at(const clk_buffer* const buffer, u64 absolute_index) {
    clk_timetag timestamp = buffer->ptrs.timestamp[absolute_index];

    // return ((u64)roundl((f64)timestamp.clock / buffer->resolution->coarse)) +
    //        timestamp.delta;
    // TODO: probably a micro optimisation but it should be possible to convert
    // this all to use integer multiplication and get rid of the casts. If we
    // can have "ratio" as some number of bins to convert the clocked timestamp
    // into an arrival time then this should be possible to do in a single step
    // clk_res resolution = *(buffer->resolution);
    // f64 ratio = resolution.coarse / resolution.fine;
    // return (u64)roundl((f64)timestamp.clock * ratio) + timestamp.delta;

    // NOTE: in testing this is ~3x faster for 2-fold cc counting
    return (*(buffer->conversion_factor) * timestamp.clock) + timestamp.delta;

    //         // tof = (truensync * self.sync_period + dtime * self.dtime_res)
    //         as u64;

    //         // sync_period: (sync_period? * 1e12) as u64,
    //         // dtime_res: (dtime_res? * 1e12) as u64,

    // clk_res resolution = *(buffer->resolution);
    // return timestamp.clock * (u64)(resolution.coarse * 1e12) +
    // timestamp.delta;
}

inline u64
clk_arrival_time_at_next(u64 conversion_factor, clk_timetag timestamp) {
    return (conversion_factor * timestamp.clock) + timestamp.delta;
}

clk_slice
clk_init_base_ptrs(const clk_buffer* const buffer) {
    clk_slice slice = { 0 };
    u64 num_elems = *buffer->capacity;

    u64 channel_offset = sizeof(clk_buffer_info);
    u64 timestamp_offset = channel_offset + (sizeof(u8) * num_elems);

    slice.length = num_elems;
    slice.channel = (u8*)buffer->map_ptr + channel_offset;
    slice.timestamp = (clk_timetag*)buffer->map_ptr + (timestamp_offset / 16);
    return slice;
}

// clk_slice clk_get_slice(const clk_buffer *const buffer, const u64 capacity,
//                         u64 start, u64 stop) {
//
//     clk_slice slice = clk_init_base_ptrs(buffer, capacity);
//
//     slice.length = stop - start;
//     slice.channel += start;
//     slice.timestamp += start;
//     // slice.clock += start;
//     // slice.delta += start;
//     //
//     return slice;
// }

inline u64
clk_bins_from_time(const clk_res resolution, const f64 time) {
    u64 factor = (u64)roundl(1 / resolution.fine);
    return time * factor;
    // return (u64)roundl(time / resolution.fine);
}

inline f64
clk_time_from_bins(const clk_res resolution, const u64 bins) {
    return (f64)bins * resolution.fine;
}

inline f64
clk_to_time(clocked record, clk_res resolution) {
    return clk_as_bins(record, resolution) * resolution.fine;
}

inline u64
clk_as_bins(clocked record, clk_res resolution) {
    f64 ratio = resolution.coarse / resolution.fine;
    return (u64)roundl((f64)record.timestamp.clock * ratio) +
           record.timestamp.delta;
    // u64 factor = clk_conversion_factor(resolution);
    // return (factor * record.timestamp.clock) + record.timestamp.delta;
}

bool
clk_equal(clocked a, clocked b) {
    return ((true == (a.timestamp.clock == b.timestamp.clock)) &&
            (true == (a.timestamp.delta == b.timestamp.delta)));
}

usize
clk_buffer_slice(const clk_buffer* const buffer,
                 FIELD_PTRS* ptrs,
                 usize start,
                 usize stop) {
    if (ptrs->length == 0) {
        return 0;
    }

    if ((stop - start) != ptrs->length) {
        return 0;
    }

    usize capacity = *(buffer->capacity);
    circular_iterator iter = { 0 };
    if (iterator_init(&iter, capacity, start, stop) == -1) {
        return 0;
    }

    usize i = next(&iter);
    for (usize j = 0; j < ptrs->length; j++) {
        clk_timetag timetag = buffer->ptrs.timestamp[i];
        ptrs->channels[j] = buffer->ptrs.channel[i];
        ptrs->clocks[j] = timetag.clock;
        ptrs->deltas[j] = timetag.delta;
        i = next(&iter);
    }

    return i;
}

usize
clk_buffer_push(const clk_buffer* const buffer,
                FIELD_PTRS slice,
                usize start,
                usize stop) {
    if (slice.length == 0) {
        return 0;
    }

    if ((stop - start) != slice.length) {
        return 0;
    }

    usize capacity = *(buffer->capacity);
    circular_iterator iter = { 0 };
    if (iterator_init(&iter, capacity, start, stop) == -1) {
        return 0;
    }

    int j = 0;
    usize i = iter.lower.index;
    clk_timetag timestamp = { .clock = slice.clocks[j],
                              .delta = slice.deltas[j] };
    buffer->ptrs.timestamp[i] = timestamp;
    buffer->ptrs.channel[i] = slice.channels[j];
    while ((i = next(&iter)) != 0) {
        j += 1;
        clk_timetag timestamp = { .clock = slice.clocks[j],
                                  .delta = slice.deltas[j] };
        buffer->ptrs.timestamp[i] = timestamp;
        buffer->ptrs.channel[i] = slice.channels[j];
    }

    return j;
}

histogram2D_coords
clk_calculate_joint_histogram_coordinates(
  delay_histogram_measurement* measurement,
  clk_timetag* timetags) {
    histogram2D_coords point = { .x = timetags[measurement->idx_idler].delta,
                                 .y = timetags[measurement->idx_signal].delta };
    return point;
}

void
clk_dh_measurement_check(usize n_channels,
                         u8 clock,
                         u8 signal,
                         u8 idler,
                         u8* channels,
                         delay_histogram_measurement* config) {
    bool has_signal = false;
    bool has_idler = false;

    u8 idx_signal = 0;
    u8 idx_idler = 0;

    for (usize i = 0; i < n_channels; i++) {
        if (channels[i] == signal) {
            has_signal = true;
            idx_signal = i;
        }

        if (channels[i] == idler) {
            has_idler = true;
            idx_idler = i;
        }
    }

    if (!(has_signal == true && has_idler == true)) {
        config->ok = false;
        return;
    }

    config->idx_signal = idx_signal;
    config->idx_idler = idx_idler;
    return;
}

u64
void_singles(const void* const buffer,
             const u64 start,
             const u64 stop,
             u64* counters);

#undef STUB
#undef T
#undef TS
#undef RESOLUTION
#undef SLICE
// #undef FIELD_PTRS
// #undef TT_VECTOR
// #undef TT_VECTOR_INI
// #undef TT_VECTOR_DEINI
// #undef TT_VECTOR_PUSH
// #undef TT_VECTOR_RESET

#endif
