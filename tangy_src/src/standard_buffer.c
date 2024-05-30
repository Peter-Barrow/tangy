#include "standard_buffer.h"

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

std_slice
std_init_base_ptrs(const std_buffer* const buffer) {
    std_slice slice = { 0 };
    u64 num_elems = *buffer->capacity;

    u64 channel_offset = sizeof(std_buffer_info);
    // u64 timestamp_offset = channel_offset + (sizeof(u8) * num_elems);

    slice.length = num_elems;
    slice.channel = (u8*)buffer->map_ptr + channel_offset;
    // slice.timestamp = (u64*)buffer->map_ptr + (timestamp_offset / 8);
    slice.timestamp = (u64*)(&(buffer->map_ptr[channel_offset + num_elems + 1]));
    return slice;
}

usize
std_buffer_slice(const std_buffer* const buffer,
                 std_slice* ptrs,
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

    usize i = iter.lower.index;
    for (usize j = 0; j < ptrs->length; j++) {
        ptrs->channel[j] = buffer->ptrs.channel[i];
        ptrs->timestamp[j] = buffer->ptrs.timestamp[i];
        i = next(&iter);
    }

    return i;
}

usize
std_buffer_push(std_buffer* const buffer,
                std_slice slice,
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
    u64 stop_abs = stop % capacity;
    u64 total = stop - start;
    u64 mid_stop = start_abs > stop_abs ? capacity : stop_abs;

    if ((*buffer->count) == 0) {
        mid_stop = total > capacity ? capacity : total;
    }

    u64 i = 0;
    for (i = 0; (i + start_abs) < mid_stop; i++) {
        buffer->ptrs.channel[start_abs + i] = slice.channel[i];
        buffer->ptrs.timestamp[start_abs + i] = slice.timestamp[i];
    }

    u64 count = i;
    if (count < total) {
        i = 0;
        for (i = 0; i < stop_abs; i++) {
            buffer->ptrs.channel[i] = slice.channel[count];
            buffer->ptrs.timestamp[i] = slice.timestamp[count];
            count += 1;
        }
    }

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

