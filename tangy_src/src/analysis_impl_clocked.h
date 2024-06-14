#ifndef __IMPL_CLK__
#define __IMPL_CLK__

#include "base.h"
#include "vector_impls.h"

typedef struct clk_timetag {
    u64 clock;
    u64 delta;
} clk_timetag;

typedef struct aclocked {
    u8 channel;
    clk_timetag timestamp;
} aclocked;

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
typedef struct clk_timetag_ptrs clk_timetag_ptrs;
struct clk_timetag_ptrs {
    u64* clock;
    u64* delta;
};
#define VEC_T_PTRS clk_timetag_ptrs
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

#define stub clk
#define slice clk_slice
#define field_ptrs clk_field_ptrs
#define record aclocked
#define timestamp clk_timetag

#define tt_vector vec_clk_timetag
#define tt_vector_init(C) clk_vec_init(C)
#define tt_vector_deinit(C) clk_vec_deinit(C)
#define tt_vector_push(V_PTR, E) clk_vec_push(V_PTR, E)
#define tt_vector_reset(V_PTR) clk_vec_reset(V_PTR)

#include "analysis_base.h"

inline u64
clk_size_of() {
    u64 elem_size = sizeof(u8) + sizeof(u64) + sizeof(u64);
    return elem_size;
}

inline void
clk_clear_buffer(ring_buffer* buf, clk_slice* data) {
    u64 capacity = rb_get_capacity(buf);
    for (u64 i = 0; i < capacity; i++) {
        data->channel[i] = 0;
        data->timestamp[i].clock = 0;
        data->timestamp[i].delta = 0;
    }
    rb_set_count(buf, 0);
}

inline clk_slice
clk_init_base_ptrs(ring_buffer* buf) {
    clk_slice slice = { 0 };
    u64 capacity = rb_get_capacity(buf);

    u64 channel_offset = 9 * sizeof(u64); // astd_size_of();
    slice.length = rb_get_capacity(buf);

    slice.channel = (u8*)buf->map_ptr + channel_offset;
    slice.timestamp =
      (clk_timetag*)(&(buf->map_ptr[channel_offset + capacity + 1]));
    return slice;
}

inline aclocked
clk_record_at(const clk_slice* data, u64 absolute_index) {
    aclocked record = { .channel = data->channel[absolute_index],
                        .timestamp = data->timestamp[absolute_index] };
    return record;
}

inline clk_timetag
clk_timestamp_at(const clk_slice* data, u64 absolute_index) {
    return data->timestamp[absolute_index];
}

inline u8
clk_channel_at(const clk_slice* data, u64 absolute_index) {
    return data->channel[absolute_index];
}

inline u64
clk_arrival_time_at(const clk_slice* data,
                     u64 conversion_factor,
                     u64 absolute_index) {
    clk_timetag timestamp = data->timestamp[absolute_index];
    return (conversion_factor * timestamp.clock) + timestamp.delta;
}

inline f64
clk_as_time(clk_timetag rec, u64 conversion_factor, f64 resolution) {
    return (f64)clk_as_bins(rec, conversion_factor) * resolution;
}

inline u64
clk_as_bins(clk_timetag record, u64 conversion_factor) {
    return (record.clock * conversion_factor) + record.delta;
}

inline u64
clk_buffer_slice(ring_buffer* const buf,
                  const clk_slice* const data,
                  clk_field_ptrs* ptrs,
                  u64 start,
                  u64 stop) {

    if (ptrs->length == 0) {
        return 0;
    }

    if ((stop - start) != ptrs->length) {
        return 0;
    }

    usize capacity = rb_get_capacity(buf);
    circular_iterator iter = { 0 };
    if (iterator_init(&iter, capacity, start, stop) == -1) {
        return 0;
    }

    u64 count = 0;
    u64 i = iter.lower.index;
    for (u64 j = 0; j < ptrs->length; j++) {
        clk_timetag timetag = data->timestamp[i];
        ptrs->channels[j] = data->channel[i];
        ptrs->clocks[j] = timetag.clock;
        ptrs->deltas[j] = timetag.delta;
        i = next(&iter);
        count += 1;
    }

    return count;
}

inline u64
clk_buffer_push(ring_buffer* const buf,
                 const clk_slice* const data,
                 clk_field_ptrs* ptrs,
                 u64 start,
                 u64 stop) {

    if (ptrs->length == 0) {
        return 0;
    }

    if ((stop - start) != ptrs->length) {
        return 0;
    }

    u64 capacity = rb_get_capacity(buf);
    u64 start_abs = start % capacity;
    u64 stop_abs = stop % capacity;

    u64 total = stop - start;
    u64 mid_stop = start_abs > stop_abs ? capacity : stop_abs;

    if (rb_get_count(buf) == 0) {
        mid_stop = total > capacity ? capacity : total;
    }

    u64 i = 0;

    for (i = 0; (i + start_abs) < mid_stop; i++) {
        data->channel[start_abs + i] = ptrs->channels[i];
        clk_timetag timestamp = { .clock = ptrs->clocks[i],
                                   .delta = ptrs->deltas[i] };
        data->timestamp[start_abs + i] = timestamp;
    }

    u64 count = i;
    if (count < total) {
        i = 0;
        for (i = 0; i < stop_abs; i++) {
            data->channel[i] = ptrs->channels[count];
            clk_timetag timestamp = { .clock = ptrs->clocks[count],
                                       .delta = ptrs->deltas[count] };
            data->timestamp[i] = timestamp;
            count += 1;
        }
    }

    rb_set_count(buf, rb_get_count(buf) + count);
    return count;
}

inline void
clk_records_copy(vec_clk_timetag* records, clk_field_ptrs* data) {

    if (records->length == 0) {
        return;
    }

    data->length = records->length;

    for (int i = 0; i < records->length; i++) {
        // printf("%d ->\t{%lu, %lu}", i, records->data.clock[i],
        // records->data.delta[i]);

        data->clocks[i] = records->data.clock[i];
        data->deltas[i] = records->data.delta[i];
    }
}

histogram2D_coords
clk_joint_histogram_position(const clk_slice* data,
                              const u8 ch_idx_idler,
                              const u8 ch_idx_signal,
                              const u8 ch_idx_clock,
                              const clk_timetag* timetags) {

    histogram2D_coords point = {
        .x = timetags[ch_idx_idler].delta,
        .y = timetags[ch_idx_signal].delta,
    };

    return point;
}

#endif
