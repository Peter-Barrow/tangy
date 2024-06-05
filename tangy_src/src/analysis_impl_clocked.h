#ifndef __IMPL_CLK__
#define __IMPL_CLK__

#include "base.h"
#include "vector_impls.h"

typedef struct aclk_timetag {
    u64 clock;
    u64 delta;
} aclk_timetag;

typedef struct aclocked {
    u8 channel;
    aclk_timetag timestamp;
} aclocked;

typedef struct aclk_res {
    f64 coarse;
    f64 fine;
} aclk_res;

typedef struct aclk_slice {
    usize length;
    u8* channel;
    aclk_timetag* timestamp;
} aclk_slice;

typedef struct aclk_field_ptrs aclk_field_ptrs;
struct aclk_field_ptrs {
    usize length;
    u8* channels;
    u64* clocks;
    u64* deltas;
};

#define VEC_T aclk_timetag
typedef struct aclk_timetag_ptrs aclk_timetag_ptrs;
struct aclk_timetag_ptrs {
    u64* clock;
    u64* delta;
};
#define VEC_T_PTRS aclk_timetag_ptrs
#define VEC_NAME aclk_vec
#include "multi_vector.h"

vec_aclk_timetag*
aclk_vec_init(size capacity) {

    vec_aclk_timetag* new_vector =
      (vec_aclk_timetag*)malloc(sizeof(vec_aclk_timetag));
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

vec_aclk_timetag*
aclk_vec_deinit(vec_aclk_timetag* multivec) {
    free(multivec->data.clock);
    free(multivec->data.delta);
    free(multivec);
    multivec = NULL;
    return multivec;
}

void
aclk_vec_reset(vec_aclk_timetag* multivec) {
    multivec->length = 0;
}

#define GROWTH_FACTOR 2

bool
aclk_vec_grow(vec_aclk_timetag* multivec) {
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
aclk_vec_push(vec_aclk_timetag* multivec, aclk_timetag value) {
    if (!((multivec->length) <= (multivec->capacity - 1))) {
        aclk_vec_grow(multivec);
    }
    multivec->data.clock[multivec->length] = value.clock;
    multivec->data.delta[multivec->length] = value.delta;
    multivec->length++;
    return;
}

#define stub aclk
#define slice aclk_slice
#define field_ptrs aclk_field_ptrs
#define record aclocked
#define timestamp aclk_timetag

#define tt_vector vec_aclk_timetag
#define tt_vector_init(C) aclk_vec_init(C)
#define tt_vector_deinit(C) aclk_vec_deinit(C)
#define tt_vector_push(V_PTR, E) aclk_vec_push(V_PTR, E)
#define tt_vector_reset(V_PTR) aclk_vec_reset(V_PTR)

#include "analysis_base.h"

inline u64
aclk_size_of() {
    u64 elem_size = sizeof(u8) + sizeof(u64) + sizeof(u64);
    return elem_size;
}

inline aclk_slice
aclk_init_base_ptrs(ring_buffer* buf) {
    aclk_slice slice = { 0 };
    u64 capacity = rb_get_capacity(buf);

    u64 channel_offset = 9 * sizeof(u64); // astd_size_of();
    slice.length = rb_get_capacity(buf);

    slice.channel = (u8*)buf->map_ptr + channel_offset;
    slice.timestamp =
      (aclk_timetag*)(&(buf->map_ptr[channel_offset + capacity + 1]));
    return slice;
}

inline aclocked
aclk_record_at(const aclk_slice* data, u64 absolute_index) {
    aclocked record = { .channel = data->channel[absolute_index],
                        .timestamp = data->timestamp[absolute_index] };
    return record;
}

inline aclk_timetag
aclk_timestamp_at(const aclk_slice* data, u64 absolute_index) {
    return data->timestamp[absolute_index];
}

inline u8
aclk_channel_at(const aclk_slice* data, u64 absolute_index) {
    return data->channel[absolute_index];
}

inline u64
aclk_arrival_time_at(const aclk_slice* data,
                     u64 conversion_factor,
                     u64 absolute_index) {
    aclk_timetag timestamp = data->timestamp[absolute_index];
    return (conversion_factor * timestamp.clock) + timestamp.delta;
}

inline f64
aclk_as_time(aclk_timetag rec, u64 conversion_factor, f64 resolution) {
    return (f64)aclk_as_bins(rec, conversion_factor) * resolution;
}

inline u64
aclk_as_bins(aclk_timetag record, u64 conversion_factor) {
    return (record.clock * conversion_factor) + record.delta;
}

inline u64
aclk_buffer_slice(ring_buffer* const buf,
                  const aclk_slice* const data,
                  aclk_field_ptrs* ptrs,
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

    usize i = iter.lower.index;
    for (usize j = 0; j < ptrs->length; j++) {
        aclk_timetag timetag = data->timestamp[i];
        ptrs->channels[j] = data->channel[i];
        ptrs->clocks[j] = timetag.clock;
        ptrs->deltas[j] = timetag.delta;
        i = next(&iter);
    }

    return i;
}

inline u64
aclk_buffer_push(ring_buffer* const buf,
                 const aclk_slice* const data,
                 aclk_field_ptrs* ptrs,
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
        aclk_timetag timestamp = { .clock = ptrs->clocks[i],
                                   .delta = ptrs->deltas[i] };
        data->timestamp[start_abs + i] = timestamp;
    }

    u64 count = i;
    if (count < total) {
        i = 0;
        for (i = 0; i < stop_abs; i++) {
            data->channel[i] = ptrs->channels[count];
            aclk_timetag timestamp = { .clock = ptrs->clocks[count],
                                       .delta = ptrs->deltas[count] };
            data->timestamp[i] = timestamp;
            count += 1;
        }
    }

    rb_set_count(buf, rb_get_count(buf) + count);
    return count;
}

inline void
aclk_records_copy(vec_aclk_timetag* records, aclk_field_ptrs* data) {

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
aclk_joint_histogram_position(aclk_slice* data,
                              u8 ch_idx_idler,
                              u8 ch_idx_signal,
                              u8 ch_idx_clock,
                              aclk_timetag* timetags) {

    histogram2D_coords point = {
        .x = timetags[ch_idx_idler].delta,
        .y = timetags[ch_idx_signal].delta,
    };

    return point;
}

#endif
