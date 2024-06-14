#include <cstdlib>
#ifndef stub
#error "No template supplied for 'stub'"
#endif

#ifndef slice
#error "No template supplied for 'slice'"
#endif

#ifndef field_ptrs
#error "No template supplied for 'field_ptrs'"
#endif

#ifndef record
#error "No template supplied for 'record'"
#endif

#ifndef timestamp
#error "No template supplied for 'timestamp'"
#endif

#ifndef tt_vector
#error "No template type 'tt_vector' for resolution supplied"
#endif

#ifndef tt_vector_init
#error "No template type 'tt_vector_init' for resolution supplied"
#endif

#ifndef tt_vector_deinit
#error "No template type 'tt_vector_deinit' for resolution supplied"
#endif

#ifndef tt_vector_push
#error "No template type 'tt_vector_push' for resolution supplied"
#endif

#ifndef tt_vector_reset
#error "No template type 'tt_vector_reset' for resolution supplied"
#endif

#define __ANALYSISBASE__

#include "base.h"
#include "ring_buffer_context.h"
#include "vector_impls.h"

#define _str(s) str(s)
#define str(s) #s
#define strprefix _str(stub)
#define tangy_buffer_name_len(name) (sizeof(strprefix) + strlen(name) + 2)
#define tangy_buffer_name_new(name)                                            \
    (char*)malloc(tangy_buffer_name_len(name) * sizeof(char))
#define tangy_buffer_name_init(name, name_buffer)                              \
    snprintf(name_buffer, tangy_buffer_name_len(name), "%s_%s", strprefix, name)

static inline char*
JOIN(stub, buffer_name_full)(char* name) {
    char* full_name = tangy_buffer_name_new(name);
    tangy_buffer_name_init(name, full_name);
    return full_name;
}

u64 JOIN(stub, size_of)();

static inline u64
JOIN(stub, buffer_map_size)(u64 num_elements) {
    u64 size_context = rb_context_size();
    u64 size_elems = JOIN(stub, size_of)();
    return size_context + (size_elems * num_elements);
}

// buffer access methods

slice JOIN(stub, init_base_ptrs)(ring_buffer* buf);
record JOIN(stub, record_at)(const slice* data, u64 absolute_index);
timestamp JOIN(stub, timestamp_at)(const slice* data, u64 absolute_index);
u8 JOIN(stub, channel_at)(const slice* data, u64 absolute_index);
u64 JOIN(stub, arrival_time_at)(const slice* data,
                                u64 conversion_factor,
                                u64 absolute_index);

#define absIdx(buf, idx) idx % rb_get_capacity(buf)
#define recordAt(s, idx) JOIN(stub, record_at)(s, idx)
#define timestampAt(s, idx) JOIN(stub, timestamp_at)(s, idx)
#define channelAt(s, idx) JOIN(stub, channel_at)(s, idx)
#define arrivalTimeAt(s, cf, idx) JOIN(stub, arrival_time_at)(s, cf, idx)

// conversion methods

static inline u64
JOIN(stub, bins_from_time)(f64 resolution, const f64 time) {
    return (u64)(time / resolution);
}

static inline f64
JOIN(stub, time_from_bins)(f64 resolution, const u64 bins) {
    return resolution * (f64)bins;
}

u64 JOIN(stub, as_bins)(timestamp rec, u64 conversion_factor);

f64 JOIN(stub, as_time)(timestamp rec, u64 conversion_factor, f64 resolution);

#define binsFromTime(r, t) JOIN(stub, bins_from_time)(r, t)
#define timeFromBins(r, b) JOIN(stub, time_from_bins)(r, b)
#define asBins(rec, cf) JOIN(stub, as_bins)(rec, cf)
#define asTime(rec, cf, r) JOIN(stub, as_time)(rec, cf, r)

// slice and push

u64 JOIN(stub, buffer_slice)(ring_buffer* const buf,
                             const slice* const data,
                             field_ptrs* ptrs,
                             u64 start,
                             u64 stop);

u64 JOIN(stub, buffer_push)(ring_buffer* const buf,
                            const slice* const data,
                            field_ptrs* ptrs,
                            u64 start,
                            u64 stop);

// analysis

static inline u64
JOIN(stub, oldest_index)(ring_buffer* buf) {
    u64 count = rb_get_count(buf);
    u64 capacity = rb_get_capacity(buf);
    return count > capacity ? count - capacity : 0;
}

static inline f64
JOIN(stub, current_time)(ring_buffer* buf, slice* data) {
    u64 count = rb_get_count(buf) - 1;
    u64 capacity = rb_get_capacity(buf);
    f64 resolution = rb_get_resolution(buf);
    u64 index = count > capacity ? count - capacity : count;

    u64 conversion_factor = rb_get_conversion_factor(buf);

    // f64 current_time = timeFromBins(arrivalTimeAt(data, conversion_factor,
    // index % capacity), resolution);

    f64 current_time = asTime(
      timestampAt(data, index % capacity), conversion_factor, resolution);

    return current_time;
}

static inline u64
JOIN(stub, lower_bound)(ring_buffer* buf, const slice* data, u64 key) {
    // FIX: add bounds checks, mid should not exceed valid range
    u64 capacity = rb_get_capacity(buf);
    u64 count = rb_get_count(buf) - 1;
    u64 conversion_factor = rb_get_conversion_factor(buf);

    u64 left = count > capacity ? count - capacity : 0;
    u64 right = count;
    u64 mid = 0;
    u64 arrival_time = 0;

    while (left < right) {
        mid = left + (right - left) / 2;
        arrival_time = arrivalTimeAt(data, conversion_factor, mid % capacity);
        if (arrival_time < key) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }

    return left;
}
#define lowerBound(buf, data, key) JOIN(stub, lower_bound)(buf, data, key)

static inline f64
JOIN(stub, time_in_buffer)(ring_buffer* buf, slice* data) {
    u64 count = rb_get_count(buf);
    u64 capacity = rb_get_capacity(buf);
    f64 resolution = rb_get_resolution(buf);
    u64 conversion_factor = rb_get_conversion_factor(buf);

    u64 newest_index = count;
    u64 oldest_index = 0;

    if (count > capacity) {
        oldest_index = count - capacity;
    }
    newest_index = (newest_index - 1) % capacity;
    oldest_index = oldest_index % capacity;

    f64 newest_time =
      asTime(timestampAt(data, newest_index), conversion_factor, resolution);
    f64 oldest_time =
      asTime(timestampAt(data, oldest_index), conversion_factor, resolution);

    return newest_time - oldest_time;
}
#define timeInBuffer(buf, sl) JOIN(stub, time_in_buffer)(buf, sl)

static inline void
JOIN(stub, bins_from_time_delays)(ring_buffer* buf,
                                  const int delays_count,
                                  const f64* const delays,
                                  u64* delays_bins) {

    f64 resolution = rb_get_resolution(buf);
    i64 offset = (u64)round(delays[0] / resolution);
    i64 temp = 0;

    // BUG: delays_bins is getting overflowed
    int i = 0;
    for (i = (delays_count - 1); i >= 1; i--) {
        temp = (i64)round(delays[i] / resolution);
        if (temp > offset) {
            offset = temp;
        }
    }

    for (i = (delays_count - 1); i >= 0; i--) {
        delays_bins[i] = (u64)(offset - (i64)round(delays[i] / resolution));
    }
}
#define binsFromTimeDelays(buf, n, dt, db)                                     \
    JOIN(stub, bins_from_time_delays)(buf, n, dt, db)

static inline size
JOIN(stub, arg_min)(ring_buffer* const buf,
                    const u64* const channel_max,
                    const u64* const current,
                    const size n_channels) {

    int min_index = 0;
    u64 temp;
    u64 min_val = current[0];

    for (size i = 1; i < n_channels; i++) {
        temp = current[i];
        if (temp < min_val) {
            min_val = temp;
            min_index = i;
        }
    }
    return min_index;
}
#define argMin(buf, ch_max, cur, n) JOIN(stub, arg_min)(buf, ch_max, cur, n)

static inline u64
JOIN(stub, singles)(ring_buffer* const buf,
                    const slice* data,
                    const u64 start,
                    const u64 stop,
                    u64* counters) {

    u64 count = rb_get_count(buf);
    u64 capacity = rb_get_capacity(buf);
    u64 start_abs = start % capacity;
    u64 stop_abs = stop % capacity;

    u64 total = stop - start;

    u64 mid_stop = start_abs >= stop_abs ? capacity : stop_abs;

    if (count == 0) {
        mid_stop = total > capacity ? capacity : total;
    }

    u64 i = 0;
    for (i = 0; (i + start_abs) < mid_stop; i++) {
        counters[data->channel[start_abs + i]] += 1;
    }

    u64 count_current = i;
    if (count_current < total) {
        i = 0;
        for (i = 0; i < stop_abs; i++) {
            counters[data->channel[i]] += 1;
        }
        count_current += i;
    }

    return count_current;
}

// TODO: replace read_time with a length, this way the user can choose to convert
// a read time to bins or alternatively just pick some number of bins
static inline pattern_iterator
JOIN(stub, pattern_init)(ring_buffer* const buf,
                         const slice* data,
                         const u32 n,
                         const u8* const channels,
                         const f64* const time_delays,
                         const f64 read_time) {

    u64* delays = (u64*)malloc(sizeof(u64) * n);
    binsFromTimeDelays(buf, n, time_delays, delays);
    // printf("Delays:");
    // for (u32 d = 0; d < n; d++) {
    //     printf("%.5e\t", time_delays[d]);
    // }
    // printf("\n");
    // printf("Delays:");
    // for (u32 d = 0; d < n; d++) {
    //     printf("%.lu\t", delays[d]);
    // }
    // printf("\n");

    u64 count = rb_get_count(buf);
    u64 capacity = rb_get_capacity(buf);
    f64 res = rb_get_resolution(buf);
    u64 read_bins = binsFromTime(res, read_time);

    u64* channel_max = (u64*)malloc(sizeof(u64) * n);
    u64* index = (u64*)malloc(sizeof(u64) * n);
    circular_iterator* iters =
      (circular_iterator*)malloc(sizeof(circular_iterator) * n);

    // potentially index could be unatialised, doubt it but the compiler says so
    for (usize j = 0; j < n; j++) {
        index[j] = 0;
    }

    u64 channel_min;
    u64 most_recent = asBins(timestampAt(data, (count - 1) % capacity),
                             rb_get_conversion_factor(buf));

    for (usize i = 0; i < n; i++) {
        if (most_recent <= delays[i]) {
            channel_max[i] = most_recent;
        } else {
            channel_max[i] = most_recent - delays[i];
        }

        if (channel_max[i] <= read_bins) {
            channel_min = 0;
        } else {
            channel_min = channel_max[i] - read_bins;
        }

        index[i] = lowerBound(buf, data, channel_min);

        while (channelAt(data, index[i] % capacity) != channels[i]) {
            index[i] += 1;
        }

        iterator_init(&iters[i], capacity, index[i], count);
        index[i] = iters[i].lower.index;
    }

    free(delays);

    pattern_iterator pattern_iter = { 0 };
    pattern_iter.length = n;
    pattern_iter.oldest = argMin(buf, channel_max, index, n);
    pattern_iter.channels = channels;
    pattern_iter.index = index;
    pattern_iter.limit = channel_max;
    pattern_iter.iters = iters;

    return pattern_iter;
}
#define patternIteratorInit(buf, s, n, ch, delays, rt)                         \
    JOIN(stub, pattern_init)(buf, s, n, ch, delays, rt)

static inline void
JOIN(stub, pattern_deinit)(pattern_iterator* pattern) {
    // free(pattern->channels);
    free(pattern->index);
    free(pattern->limit);
    free(pattern->iters);
}
#define patternIteratorDeinit(PTTRN) JOIN(stub, pattern_deinit)(PTTRN)

static inline bool
JOIN(stub, next_for_channel)(const slice* data,
                             circular_iterator* iter,
                             u8 channel,
                             u64* index) {

    usize i = next(iter);
    while ((channelAt(data, i) != channel) & (iter->count != 0)) {
        i = next(iter);
    }
    *index = i;

    if (iter->count == 0) {
        return false;
    }

    return true;
}
#define nextForChannel(s, iter, ch, idx)                                       \
    JOIN(stub, next_for_channel)(s, iter, ch, idx)

static inline u64
JOIN(stub, channels_in_coincidence)(const u8 n_channels,
                                    const u64* current_times,
                                    const u64* const channel_max,
                                    const u64* const index,
                                    const u64 diameter,
                                    const u64 min_index) {

    usize oldest = channel_max[min_index] - current_times[min_index];
    usize in_coincidence = 0;

    usize j = 0;
    usize newer = 0;
    for (j = 0; j < min_index; j++) {
        newer = channel_max[j] - current_times[j];
        if ((oldest - newer) < diameter) {
            in_coincidence++;
        } else {
            // break;
            return 0;
        }
        // if (!(oldest + diameter < newer)) {
        //     return 0;
        // } else {
        //     in_coincidence += 1;
        // }
    }

    for (j = min_index + 1; j < n_channels; j++) {
        newer = channel_max[j] - current_times[j];
        if ((oldest - newer) < diameter) {
            in_coincidence++;
        } else {
            // break;
            return 0;
        }
        // if (!(oldest + diameter < newer)) {
        //     return 0;
        // } else {
        //     in_coincidence += 1;
        // }
    }

    usize coincidence_size = (usize)n_channels - 1;
    return (in_coincidence == coincidence_size) ? 1 : 0;
}
#define inCoincidence(n, cur, ch_max, idx, dia, min)                           \
    JOIN(stub, channels_in_coincidence)(n, cur, ch_max, idx, dia, min)

static inline u64
JOIN(stub, coincidence_count)(ring_buffer* const buf,
                              const slice* data,
                              const u64 n_channels,
                              u8* channels,
                              const f64* delays,
                              const f64 radius,
                              const f64 read_time) {

    // TODO: add singles counters

    pattern_iterator pattern =
      patternIteratorInit(buf, data, n_channels, channels, delays, read_time);

    u64 conversion_factor = rb_get_conversion_factor(buf);
    u64* current_times = (u64*)malloc(n_channels * sizeof(u64));
    for (usize i = 0; i < n_channels; i++) {
        current_times[i] =
          arrivalTimeAt(data, conversion_factor, pattern.index[i]);
    }

    f64 res = rb_get_resolution(buf);
    u64 radius_bins = binsFromTime(res, radius); // TODO: should this be doubled
    u64 diameter_bins = radius_bins + radius_bins;

    bool in_range = true;
    u64 count = 0;
    while (in_range == true) {

        pattern.oldest = argMin(buf, pattern.limit, current_times, n_channels);

        count += inCoincidence(n_channels,
                               current_times,
                               pattern.limit,
                               pattern.index,
                               diameter_bins,
                               pattern.oldest);

        in_range = nextForChannel(data,
                                  &pattern.iters[pattern.oldest],
                                  channels[pattern.oldest],
                                  &pattern.index[pattern.oldest]);

        current_times[pattern.oldest] =
          arrivalTimeAt(data, conversion_factor, pattern.index[pattern.oldest]);
    }

    patternIteratorDeinit(&pattern);
    free(current_times);

    return count;
}

static inline u64
JOIN(stub, coincidence_collect)(ring_buffer* const buf,
                                const slice* data,
                                const u64 n_channels,
                                u8* channels,
                                const f64* delays,
                                const f64 radius,
                                const f64 read_time,
                                tt_vector* records) {

    if (records == NULL) {
        return 0;
    }

    tt_vector_reset(records);

    // TODO: add singles counters

    pattern_iterator pattern =
      patternIteratorInit(buf, data, n_channels, channels, delays, read_time);

    u64 conversion_factor = rb_get_conversion_factor(buf);
    u64* current_times = (u64*)malloc(n_channels * sizeof(u64));
    for (usize i = 0; i < n_channels; i++) {
        current_times[i] =
          arrivalTimeAt(data, conversion_factor, pattern.index[i]);
    }

    f64 res = rb_get_resolution(buf);
    u64 radius_bins = binsFromTime(res, radius); // TODO: should this be doubled
    u64 diameter_bins = radius_bins + radius_bins;

    bool in_range = true;
    u64 check = 0;
    u64 count = 0;
    while (in_range == true) {

        pattern.oldest = argMin(buf, pattern.limit, current_times, n_channels);

        check = inCoincidence(n_channels,
                              current_times,
                              pattern.limit,
                              pattern.index,
                              diameter_bins,
                              pattern.oldest);

        if (check == 1) {
            for (u64 i = 0; i < n_channels; i++) {
                tt_vector_push(records, timestampAt(data, pattern.index[i]));
            }
        }
        count += check;

        in_range = nextForChannel(data,
                                  &pattern.iters[pattern.oldest],
                                  channels[pattern.oldest],
                                  &pattern.index[pattern.oldest]);

        current_times[pattern.oldest] =
          arrivalTimeAt(data, conversion_factor, pattern.index[pattern.oldest]);
    }

    patternIteratorDeinit(&pattern);
    free(current_times);

    return count;
}

static inline void JOIN(stub, records_copy)(tt_vector* records,
                                            field_ptrs* data);

static inline u64
JOIN(stub, timetrace)(ring_buffer* buf,
                      const slice* data,
                      const u64 start,
                      const u64 stop,
                      const u64 bin_width,
                      const u8* channels,
                      const u64 n_channels,
                      const u64 length,
                      u64* intensities) {

    u64 count = rb_get_count(buf);
    u64 capacity = rb_get_capacity(buf);

    if (start > count) {
        return 0;
    }

    if (stop > count) {
        return 0;
    }

    if (start > stop) {
        return 0;
    }

    circular_iterator iter = { 0 };
    iterator_init(&iter, capacity, start, stop);

    u64 index = iter.lower.index;
    u64 conversion_factor = rb_get_conversion_factor(buf);
    u64 end_of_bin = arrivalTimeAt(data, conversion_factor, index) + bin_width;

    u64 i = 0;
    u64 offset = 1;
    u8 current_channel = 0;
    u64 intensity = 0;

    while (iter.count != 0) {
        current_channel = channelAt(data, index);
        for (u64 c = 0; c < n_channels; c++) {
            if (current_channel == channels[c]) {
                intensity += 1;
                break;
            }
        }

        if (arrivalTimeAt(data, conversion_factor, index) > end_of_bin) {
            intensities[i] = intensity;
            intensity = 0;
            i += 1;
            end_of_bin += bin_width;
        }

        offset = next(&iter);
        index = offset;
    }

    return i;
}

static inline void
JOIN(stub, relative_delay)(ring_buffer* buf,
                           const slice* data,
                           const u64 start,
                           const u64 stop,
                           const u64 correlation_window,
                           const u64 resolution,
                           const u8 channels_a,
                           const u8 channels_b,
                           const u64 length,
                           u64* intensities) {

    u64 count = rb_get_count(buf);
    u64 capacity = rb_get_capacity(buf);

    if (start > count) {
        return;
    }

    if (stop > count) {
        return;
    }

    if (start > stop) {
        return;
    }

    circular_iterator iter = { 0 };
    iterator_init(&iter, capacity, start, stop);
    u64 index = iter.lower.index;
    u64 conversion_factor = rb_get_conversion_factor(buf);

    u64 central_bin = length / 2;
    u64 time_of_arrival_a_previous = 0;
    u64 time_of_arrival_b_previous = 0;
    u64 delta;
    u64 hist_index = 0;

    while (iter.count != 0) {
        u8 current_channel = channelAt(data, index);
        u64 time_of_arrival = arrivalTimeAt(data, conversion_factor, index);

        if (current_channel == channels_a) {
            time_of_arrival_a_previous = time_of_arrival;
            delta = time_of_arrival - time_of_arrival_b_previous;

            if (delta < correlation_window) {
                hist_index = (central_bin - delta / resolution) - 1;
                intensities[hist_index] += 1;
            }

        } else if (current_channel == channels_b) {
            time_of_arrival_b_previous = time_of_arrival;
            delta = time_of_arrival - time_of_arrival_a_previous;

            if (delta < correlation_window) {
                hist_index = central_bin + delta / resolution;
                intensities[hist_index] += 1;
            }
        }

        index = next(&iter);
    }
}

histogram2D_coords JOIN(stub,
                        joint_histogram_position)(const slice* data,
                                                  const u8 ch_idx_idler,
                                                  const u8 ch_idx_signal,
                                                  const u8 ch_idx_clock,
                                                  const timestamp* timetags);

#define jointHistogramPosition(s, i_i, i_s, i_c, ts)                           \
    JOIN(stub, joint_histogram_position)(s, i_i, i_s, i_c, ts)

static inline u64
JOIN(stub, joint_delay_histogram)(ring_buffer* const buf,
                                  const slice* data,
                                  const u8 clock,
                                  const u8 signal,
                                  const u8 idler,
                                  const u64 n_channels,
                                  const u8* channels,
                                  const f64* delays,
                                  const f64 radius,
                                  const f64 read_time,
                                  u64* intensities) {

    bool has_signal = false;
    bool has_idler = false;

    u8 idx_signal = 0;
    u8 idx_idler = 0;
    u8 idx_clock = 0;

    for (u64 i = 0; i < n_channels; i++) {
        if (channels[i] == signal) {
            has_signal = true;
            idx_signal = i;
        }
        if (channels[i] == idler) {
            has_idler = true;
            idx_idler = i;
        }
        if (channels[i] == clock) {
            idx_clock = i;
        }
    }

    if (!(has_signal == true && has_idler == true)) {
        return 0;
    }

    //     if (idx_signal == idx_idler) {
    //         return 0;
    //     }

    pattern_iterator pattern =
      patternIteratorInit(buf, data, n_channels, channels, delays, read_time);

    u64 conversion_factor = rb_get_conversion_factor(buf);
    u64* current_times = (u64*)malloc(n_channels * sizeof(u64));
    timestamp* current_timetags =
      (timestamp*)malloc(n_channels * sizeof(timestamp));
    for (usize i = 0; i < n_channels; i++) {
        current_times[i] =
          arrivalTimeAt(data, conversion_factor, pattern.index[i]);
    }

    f64 res = rb_get_resolution(buf);
    u64 radius_bins = binsFromTime(res, radius); // TODO: should this be doubled
    u64 diameter_bins = radius_bins + radius_bins;

    bool in_range = true;
    u64 check = 0;
    u64 count = 0;
    u64 offset = 0;
    histogram2D_coords point = { 0 };
    while (in_range == true) {

        pattern.oldest = argMin(buf, pattern.limit, current_times, n_channels);

        check = inCoincidence(n_channels,
                              current_times,
                              pattern.limit,
                              pattern.index,
                              diameter_bins,
                              pattern.oldest);

        if (check == 1) {
            point = jointHistogramPosition(
              data, idx_signal, idx_idler, idx_clock, current_timetags);
            if ((point.x < diameter_bins) & (point.y < diameter_bins)) {
                // histogram_2d[point.y][point.x] += 1;
                // signal -> rows -> x
                // idler -> columns -> y
                offset = (point.x * diameter_bins) + (point.y);
                // printf("POINT:->{%lu,\t%lu} -> %lu | Limit:%lu\n",
                // point.x, point.y, offset, diameter_bins * diameter_bins);
                intensities[offset] += 1;
            }
        }

        count += check;

        in_range = nextForChannel(data,
                                  &pattern.iters[pattern.oldest],
                                  channels[pattern.oldest],
                                  &pattern.index[pattern.oldest]);

        current_timetags[pattern.oldest] =
          timestampAt(data, pattern.index[pattern.oldest]);

        current_times[pattern.oldest] =
          arrivalTimeAt(data, conversion_factor, pattern.index[pattern.oldest]);
    }

    patternIteratorDeinit(&pattern);
    free(current_times);
    free(current_timetags);

    return count;
}

#undef stub
#undef slice
#undef field_ptrs
#undef record
#undef timestamp

#undef tt_vector
#undef tt_vector_init
#undef tt_vector_deinit
#undef tt_vector_push
#undef tt_vector_reset

// #undef _str
// #undef str
// #undef prefix
// #undef buffer_name_len
// #undef buffer_name_new
// #undef buffer_name_init

#undef absIdx
#undef recordAt
#undef timestampAt
#undef channelAt
#undef arrivalTimeAt

#undef binsFromTime
#undef timeFromBins
#undef asBins
#undef asTime

#undef lowerBound
#undef timeInBuffer
#undef binsFromTimeDelays
#undef argMin
#undef patternIteratorInit
#undef patternIteratorDeinit
#undef nextForChannel
#undef inCoincidence
#undef jointHistogramPosition
