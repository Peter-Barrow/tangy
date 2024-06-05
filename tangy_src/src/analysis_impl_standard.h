#ifndef __IMPL_STD__
#define __IMPL_STD__

#include "base.h"

typedef u64 astd_timetag;

typedef struct astandard {
    u8 channel;
    astd_timetag timestamp;
} astandard;

typedef f64 astd_res;

typedef struct astd_slice {
    usize length;
    u8* channel;
    astd_timetag* timestamp;
} astd_slice;

#define stub astd
#define slice astd_slice
#define field_ptrs astd_slice
#define record astandard
#define timestamp astd_timetag

#define VEC_T astd_timetag
#define VEC_NAME astd_vec
#include "vector.h"

#define tt_vector vec_astd_timetag
#define tt_vector_init(C) astd_vec_init(C)
#define tt_vector_deinit(C) astd_vec_deinit(C)
#define tt_vector_push(V_PTR, E) astd_vec_push(V_PTR, E)
#define tt_vector_reset(V_PTR) astd_vec_reset(V_PTR)

#include "analysis_base.h"

inline u64
astd_size_of() {
    u64 elem_size = sizeof(uint8_t) + sizeof(uint64_t);
    return elem_size;
}

inline astd_slice
astd_init_base_ptrs(ring_buffer* buf) {
    astd_slice slice = { 0 };
    u64 capacity = rb_get_capacity(buf);

    u64 channel_offset = 9 * sizeof(u64); // astd_size_of();
    slice.length = capacity;

    slice.channel = (u8*)buf->map_ptr + channel_offset;
    slice.timestamp =
      (astd_timetag*)(&(buf->map_ptr[channel_offset + capacity + 1]));
    return slice;
}

inline astandard
astd_record_at(const astd_slice* data, u64 absolute_index) {
    astandard record = { .channel = data->channel[absolute_index],
                         .timestamp = data->timestamp[absolute_index] };
    return record;
}

inline astd_timetag
astd_timestamp_at(const astd_slice* data, u64 absolute_index) {
    return data->timestamp[absolute_index];
}

inline u8
astd_channel_at(const astd_slice* data, u64 absolute_index) {
    return data->channel[absolute_index];
}

inline u64
astd_arrival_time_at(const astd_slice* data,
                     u64 conversion_factor,
                     u64 absolute_index) {
    return data->timestamp[absolute_index];
}

inline f64
astd_as_time(astd_timetag rec, u64 conversion_factor, f64 resolution) {
    return (f64)astd_as_bins(rec, conversion_factor) * resolution;
}

inline u64
astd_as_bins(astd_timetag record, u64 conversion_factor) {
    return (u64)record;
}

inline u64
astd_buffer_slice(ring_buffer* const buf,
                  const astd_slice* const data,
                  astd_slice* ptrs,
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
        ptrs->channel[j] = data->channel[i];
        ptrs->timestamp[j] = data->timestamp[i];
        i = next(&iter);
    }

    return i;
}

inline u64
astd_buffer_push(ring_buffer* const buf,
                 const astd_slice* const data,
                 astd_slice* ptrs,
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
        data->channel[start_abs + i] = ptrs->channel[i];
        data->timestamp[start_abs + i] = ptrs->timestamp[i];
    }

    u64 count = i;
    if (count < total) {
        i = 0;
        for (i = 0; i < stop_abs; i++) {
            data->channel[i] = ptrs->channel[count];
            data->timestamp[i] = ptrs->timestamp[count];
            count += 1;
        }
    }

    rb_set_count(buf, rb_get_count(buf) + count);
    return count;
}

inline void
astd_records_copy(vec_astd_timetag* records, astd_slice* data) {
    if (records->length == 0) {
        return;
    }

    data->length = records->length;

    for (int i = 0; i < records->length; i++) {
        data->timestamp[i] = records->data[i];
    }
}

histogram2D_coords
astd_joint_histogram_position(astd_slice* data,
                              u8 ch_idx_idler,
                              u8 ch_idx_signal,
                              u8 ch_idx_clock,
                              astd_timetag* timetags) {

    u64 arrival_clock = timetags[ch_idx_clock];
    u64 arrival_signal = timetags[ch_idx_signal];
    u64 arrival_idler = timetags[ch_idx_idler];

    u64 delta_idler = (arrival_clock > arrival_idler)
                        ? arrival_clock - arrival_idler
                        : arrival_idler - arrival_clock;

    u64 delta_signal = (arrival_clock > arrival_signal)
                        ? arrival_clock - arrival_signal
                        : arrival_signal - arrival_clock;

    histogram2D_coords point = { .x = delta_idler, .y = delta_signal };

    return point;
}

#endif
