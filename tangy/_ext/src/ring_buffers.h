#ifndef STUB
#error "No template type 'STUB' suppled for buffer_info"
#endif

#ifndef T
#error "No template type 'T' suppled for buffer_info"
#endif

#ifndef TS
#error "No template type 'T' suppled for buffer_info"
#endif

#ifndef RESOLUTION
#error "No template type 'RESOLUTION' for resolution supplied"
#endif

#ifndef SLICE
#error "No template type 'SLICE' for resolution supplied"
#endif

#ifndef TT_VECTOR
#error "No template type 'TT_VECTOR' for resolution supplied"
#endif

#ifndef TT_VECTOR_INIT
#error "No template type 'TT_VECTOR_INIT' for resolution supplied"
#endif

#ifndef TT_VECTOR_DEINIT
#error "No template type 'TT_VECTOR_DEINIT' for resolution supplied"
#endif

#ifndef TT_VECTOR_PUSH
#error "No template type 'TT_VECTOR_PUSH' for resolution supplied"
#endif

#ifndef TT_VECTOR_RESET
#error "No template type 'TT_VECTOR_RESET' for resolution supplied"
#endif

// #ifndef CC_RESULT
// #error "No template type 'CC_RESULT' for resolution supplied"
// #endif

// #ifndef REC_VEC
// #error "No template type 'REC_VEC' for resolution supplied"
// #endif

#define __RING_BUFFERS__

#include "base.h"
#include "shared_memory.h"
#include "vector_impls.h"

#define _str(s) str(s)
#define str(s) #s
#define TS_MEM_MAP_NAME str(JOIN(STUB, _tagStream))

#define alignof(x) (size) _Alignof(x)

#define name_length 10

#define BUFFER JOIN(STUB, buffer)
#define BUFFER_INFO JOIN(STUB, buffer_info)
#define BUFFER_INFO_PTRS JOIN(STUB, buffer_info_ptrs)

typedef struct {
    byte* map_ptr;
    SLICE ptrs;
    fd_t file_descriptor;
    byte* name; /* do we need a string type? */
    RESOLUTION
    *resolution; // maybe it does make sense to have setters for fields that
                 // should be constant after initialisation
    u64* capacity;
    u64* count;
    u64* index_of_reference; // pointer to index of reference record
    u8* n_channels;
} BUFFER;

typedef struct {
    RESOLUTION resolution;
    u64 capacity;
    u64 count;
    u64 index_of_reference; // pointer to index of reference record
    u8 n_channels;
} BUFFER_INFO;

u64 JOIN(STUB, size_of)();

static inline u64
JOIN(STUB, buffer_map_size)(u64 num_elements) {
    u64 info_size = sizeof(BUFFER_INFO);
    u64 elem_size = JOIN(STUB, size_of)();
    return info_size + (elem_size * num_elements);
}

static inline BUFFER*
JOIN(STUB, buffer_new)() {
    BUFFER* buf;
    buf = (BUFFER*)malloc(sizeof(BUFFER));
    return buf;
}

// setters
#define _SETFIELD JOIN(JOIN(STUB, buffer), set)
#define SETFIELD(field) JOIN(_SETFIELD, field)

// getters
#define _GETFIELD JOIN(JOIN(STUB, buffer), get)
#define GETFIELD(field) JOIN(_GETFIELD, field)

// Buffer management
static inline void
JOIN(STUB, buffer_info_init)(byte* data, BUFFER* buffer) {

    buffer->resolution = &((BUFFER_INFO*)data)->resolution;
    buffer->capacity = &((BUFFER_INFO*)data)->capacity;
    buffer->count = &((BUFFER_INFO*)data)->count;
    buffer->index_of_reference = &((BUFFER_INFO*)data)->index_of_reference;
    buffer->n_channels = &((BUFFER_INFO*)data)->n_channels;
}

SLICE JOIN(STUB, init_base_ptrs)(const BUFFER* const buffer);

static inline tbResult
JOIN(STUB, buffer_init)(const u64 num_elements,
                        RESOLUTION resolution,
                        const u8 n_channels,
                        byte* name,
                        BUFFER* buffer) {

    u64 num_bytes = JOIN(STUB, buffer_map_size)(num_elements);
    shared_mapping map = { 0 };
    map.name = name;
    tbResult result = shmem_create(num_bytes, &map);
    if (false == result.Ok) {
        return result;
    }

    buffer->map_ptr = map.data;
    buffer->name = name;
    buffer->file_descriptor = map.file_descriptor;

    usize offset = 0;
    offset = offsetof(BUFFER_INFO, capacity) / 8;
    ((u64*)buffer->map_ptr)[offset] = num_elements;

    offset = offsetof(BUFFER_INFO, resolution) / sizeof(RESOLUTION);
    ((RESOLUTION*)buffer->map_ptr)[offset] = resolution;

    offset = offsetof(BUFFER_INFO, count) / 8;
    ((u64*)buffer->map_ptr)[offset] = 0;

    offset = offsetof(BUFFER_INFO, index_of_reference) / 8;
    ((u64*)buffer->map_ptr)[offset] = 0;

    offset = offsetof(BUFFER_INFO, n_channels) / 8;
    ((u64*)buffer->map_ptr)[offset] = n_channels;

    buffer->capacity = &((BUFFER_INFO*)buffer->map_ptr)->capacity;
    buffer->resolution = &((BUFFER_INFO*)buffer->map_ptr)->resolution;
    buffer->count = &((BUFFER_INFO*)buffer->map_ptr)->count;
    buffer->index_of_reference =
      &((BUFFER_INFO*)buffer->map_ptr)->index_of_reference;
    buffer->n_channels = &((BUFFER_INFO*)buffer->map_ptr)->n_channels;

    buffer->ptrs = JOIN(STUB, init_base_ptrs)(buffer);

    result.Ok = true;
    return result;
}

static inline tbResult
JOIN(STUB, buffer_connect)(byte* name, BUFFER* buffer) {

    bool exists = false;
    tbResult result = shmem_exists(name, &exists);
    if (false == result.Ok) {
        return result;
    }

    shared_mapping map = { 0 };
    map.name = name;
    result = shmem_connect(&map);
    if (false == result.Ok) {
        return result;
    }

    buffer->map_ptr = map.data;
    buffer->name = name;
    buffer->file_descriptor = map.file_descriptor;

    // JOIN(STUB, buffer_info_init)(buffer->map_ptr, info);
    JOIN(STUB, buffer_info_init)(buffer->map_ptr, buffer);
    // buffer->ptrs = JOIN(STUB, init_base_ptrs)(buffer, *info->capacity);
    buffer->ptrs = JOIN(STUB, init_base_ptrs)(buffer);

    result.Ok = true;

    return result;
}

static inline tbResult
JOIN(STUB, buffer_deinit)(BUFFER* buffer) {

    shared_mapping map = { .file_descriptor = buffer->file_descriptor,
                           .name = buffer->name,
                           .data = buffer->map_ptr };

    bool exists = false;
    tbResult result = shmem_exists(buffer->name, &exists);

    if (true == exists) {
        result = shmem_close(&map);
        if (false == result.Ok) {
            return result;
        }
    }

    result.Ok = true;
    return result;
}

// Indexing functions -> absolute index meaning idx % capacity)
T JOIN(STUB, record_at)(const BUFFER* const buffer, const u64 absolute_index);
TS JOIN(STUB, timestamp_at)(const BUFFER* const buffer,
                            const u64 absolute_index);
u8 JOIN(STUB, channel_at)(const BUFFER* const buffer, const u64 absolute_index);
u64 JOIN(STUB, arrival_time_at)(const BUFFER* const buffer,
                                const u64 absolute_index);

#define AbsIdx(BUF, IDX) IDX % (*(BUF->capacity))
#define RecordAt(BUF, ABS_IDX) JOIN(STUB, record_at)(BUF, ABS_IDX)
#define TimestampAt(BUF, ABS_IDX) JOIN(STUB, timestamp_at)(BUF, ABS_IDX)
#define ChannelAt(BUF, ABS_IDX) JOIN(STUB, channel_at)(BUF, ABS_IDX)
#define ArrivalTimeAt(BUF, ABS_IDX) JOIN(STUB, arrival_time_at)(BUF, ABS_IDX)

// tag conversion
u64 JOIN(STUB, bins_from_time)(const RESOLUTION resolution, const f64 time);
f64 JOIN(STUB, time_from_bins)(const RESOLUTION resolution, const u64 bins);
f64 JOIN(STUB, to_time)(T record, RESOLUTION resolution);
u64 JOIN(STUB, as_bins)(T record, RESOLUTION resolution);

#define BinsFromTime(RES, TIME) JOIN(STUB, bins_from_time)(RES, TIME)
#define TimeFromBins(RES, BINS) JOIN(STUB, time_from_bins)(RES, BINS)
#define ToTime(RECORD, RES) JOIN(STUB, to_time)(RECORD, RES)
#define ToBins(RECORD, RES) JOIN(STUB, as_bins)(RECORD, RES)

// comparisons
static inline bool
JOIN(STUB, compare)(T a, T b, RESOLUTION res_a, RESOLUTION res_b) {
    return JOIN(STUB, as_bins)(a, res_a) < JOIN(STUB, as_bins)(b, res_a);
}

bool JOIN(STUB, equal)(T a, T b);
// static inline bool JOIN(STUB, equal)(T a, T b) {
//     return JOIN(STUB, as_bins)(a, res_a) == JOIN(STUB, as_bins)(b, res_b);
// }

#define CMP(A, B, RES_A, RES_B) JOIN(STUB, compare)(A, B, RES_A, RES_B)
#define EQL(A, B) JOIN(STUB, equal)(A, B)

// analysis

/**
 * @brief Binary search, finds the closest value relative to the buffers head
 *
 * @param[in, out] buffer pointer to struct containing buffer
 * @param[in] key value to find in buffer
 * @return index of value closest but greater than key in buffer
 */
static inline usize
JOIN(STUB, lower_bound)(const BUFFER* buffer, usize key) {

    RESOLUTION res = *buffer->resolution;
    u64 capacity = *buffer->capacity;
    u64 count = *(buffer->count);

    u64 left = count > capacity ? count - capacity : 0;
    u64 right = count;
    u64 mid = 0;

    T record = { 0 };

    while (left < right) {
        mid = left + (right - left) / 2;
        record = RecordAt(buffer, mid % capacity);
        if (ToBins(record, res) < key) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }

    return left;
}
#define LowerBound(BUF, KEY) JOIN(STUB, lower_bound)(BUF, KEY)

static inline usize
JOIN(STUB, upper_bound)(const BUFFER* buffer, usize key) {

    RESOLUTION res = *buffer->resolution;
    u64 capacity = *buffer->capacity;
    u64 count = *buffer->count;

    u64 left = count > capacity ? count - capacity : 0;
    u64 right = count - 1;
    u64 mid = 0;

    T record = { 0 };

    while (left < right) {
        mid = (right + left) / 2;
        record = JOIN(STUB, record_at)(buffer, mid % capacity);
        if (!(JOIN(STUB, as_bins)(record, res) < key)) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }

    return left;
}

/**
 * @brief Current time held in buffer
 *
 * @param[in, out] buffer [TODO:description]
 * @return time difference between newest and oldest records
 */
static inline f64
JOIN(STUB, time_in_buffer)(const BUFFER* buffer) {
    u64 count = *buffer->count;
    u64 capacity = *buffer->capacity;
    u64 oldest_index = (count > capacity ? count - capacity : 0) % count;
    u64 newest_index = (count - 1) % capacity;

    RESOLUTION resolution = *buffer->resolution;

    f64 newest_time = ToTime(RecordAt(buffer, newest_index), resolution);
    f64 oldest_time = ToTime(RecordAt(buffer, oldest_index), resolution);

    return newest_time - oldest_time;
}
#define TimeInBuffer(BUF) JOIN(STUB, time_in_buffer)(BUF)

/**
 * @brief Converts a an array of delays in time to delays in units of time bins
 *
 * @param[in] buffer [TODO:description]
 * @param[in] length number of channels (lengths of delays and bins arrays)
 * @param[in] delays array of delays in seconds
 * @param[in, out] bins array of delays in time bins
 */
static inline void
JOIN(STUB, bins_from_time_delays)(const BUFFER* const buffer,
                                  const int length,
                                  const f64* const delays,
                                  u64* bins) {
    RESOLUTION res = *(buffer->resolution);
    size offset = BinsFromTime(res, delays[0]);
    size temp = 0;

    int i;
    for (i = (length - 1); i >= 1; i--) {
        temp = (size)BinsFromTime(res, delays[i]);
        if (temp > offset) {
            offset = temp;
        }
    }

    for (i = (length - 1); i >= 0; i--) {
        bins[i] = (u64)(offset - (size)BinsFromTime(res, delays[i]));
    }
}
#define BinsFromTimeDelays(BUF, N, DELAYS, BINS)                               \
    JOIN(STUB, bins_from_time_delays)(BUF, N, DELAYS, BINS)

/**
 * @brief Determines which channel has the oldest record
 *
 * For each channel at a given index, calculates the arrival time of the record
 * for the channel at that index, whichever is the oldest (smallest) value has
 * its position returned.
 *
 * @param[in] buffer
 * @param[in] channel_max newest possible value for each channel
 * @param[in] index current position each channel is being iterated at
 * @param[in] n_channels total number of channels being tested
 * @return index of minimum element in index array
 */
static inline size
JOIN(STUB, arg_min)(const BUFFER* const buffer,
                    const u64* const channel_max,
                    const u64* const index,
                    const size n_channels) {
    usize capacity = *(buffer->capacity);
    int min_index = 0;
    u64 temp;
    u64 min_val = ArrivalTimeAt(buffer, index[0] % capacity);

    for (int i = 1; i < n_channels; i++) {
        temp = ArrivalTimeAt(buffer, index[i] % capacity);
        if (temp < min_val) {
            min_val = temp;
            min_index = i;
        }
    }
    return min_index;
}
#define ArgMin(BUF, CH_MAX, IDX, N_CH)                                         \
    JOIN(STUB, arg_min)(BUF, CH_MAX, IDX, N_CH)

// measurements

/**
 * @brief Counts the number of occurances of each channel between two points
 *
 * @param[in] buffer [TODO:description]
 * @param[in] start index to begin counting from
 * @param[in] stop index to terminate at
 * @param[out] counters number of occurances of each channel
 * @return [TODO:description]
 */
static inline u64
JOIN(STUB, singles)(const BUFFER* const buffer,
                    const u64 start,
                    const u64 stop,
                    u64* counters) {
    u64 capacity = *buffer->capacity;
    u64 start_abs = start % capacity;
    u64 stop_abs = stop % capacity;

    u64 total = stop - start;

    u64 mid_stop = start_abs > stop_abs ? capacity : stop_abs;

    u64 i = 0;
    for (i = 0; (i + start_abs) < mid_stop; i++) {
        counters[buffer->ptrs.channel[start_abs + i]] += 1;
    }

    u64 count = i;
    if (count < total) {
        i = 0;
        for (i = 0; i < stop_abs; i++) {
            counters[buffer->ptrs.channel[stop_abs + i]] += 1;
        }
        count += i;
    }

    return count;
}

static inline pattern_iterator
JOIN(STUB, pattern_init)(const BUFFER* const buffer,
                         const usize n,
                         u8* const channels,
                         const f64* const time_delays,
                         const f64 read_time) {

    u64* delays = (u64*)malloc(sizeof(u64) * n);
    BinsFromTimeDelays(buffer, n, time_delays, delays);

    u64 count = *(buffer->count) - 1;
    u64 capacity = *(buffer->capacity);
    RESOLUTION res = *(buffer->resolution);
    u64 read_bins = BinsFromTime(res, read_time);

    u64* channel_max = (u64*)malloc(sizeof(u64) * n);
    u64* index = (u64*)malloc(sizeof(u64) * n);
    circular_iterator* iters =
      (circular_iterator*)malloc(sizeof(circular_iterator) * n);

    // potentially index could be unatialised, doubt it but the compiler says so
    for (usize j = 0; j < n; j++) {
        index[j] = 0;
    }

    u64 channel_min;
    u64 time_in_buffer = ArrivalTimeAt(buffer, count % capacity);
    for (usize i = 0; i < n; i++) {
        if (time_in_buffer <= delays[i]) {
            channel_max[i] = 0;
        } else {
            channel_max[i] = time_in_buffer - delays[i];
        }

        if (channel_max[i] <= read_bins) {
            channel_min = 0;
        } else {
            channel_min = channel_max[i] - read_bins;
        }

        index[i] = LowerBound(buffer, channel_min);

        while (ChannelAt(buffer, index[i] % capacity) != channels[i] &&
               ArrivalTimeAt(buffer, index[i] % capacity) >= channel_min) {
            index[i] += 1;
        }

        iterator_init(&iters[i], capacity, index[i], count);
        index[i] = iters[i].lower.index;
    }

    pattern_iterator pattern_iter = { 0 };
    pattern_iter.length = n;
    pattern_iter.oldest = ArgMin(buffer, channel_max, index, n);
    pattern_iter.channels = channels;
    pattern_iter.index = index;
    pattern_iter.limit = channel_max;
    pattern_iter.iters = iters;
    return pattern_iter;
}
#define PatternIteratorInit(BUF, N, CH, DELAYS, RT)                            \
    JOIN(STUB, pattern_init)(BUF, N, CH, DELAYS, RT)

static inline void
JOIN(STUB, pattern_deinit)(pattern_iterator* pattern) {
    // free(pattern->channels);
    free(pattern->index);
    free(pattern->limit);
    free(pattern->iters);
}
#define PatternIteratorDeinit(PTTRN) JOIN(STUB, pattern_deinit)(PTTRN)

static inline bool
JOIN(STUB, next_for_channel)(const BUFFER* const buffer,
                             circular_iterator* iter,
                             u8 channel,
                             usize* index) {

    usize i = next(iter);
    if (i == 0) {
        return false;
    }
    while (ChannelAt(buffer, i) != channel) {
        i = next(iter);
        if (i == 0) {
            return false;
        }
    }

    *index = i;

    if (iter->count == 0) {
        return false;
    }

    return true;
}
#define NextForChannel(BUF, ITER, CH, IDX)                                     \
    JOIN(STUB, next_for_channel)(BUF, ITER, CH, IDX)

/**
 * @brief Test if a set of channels are within a coincidence window
 *
 * @param[in] buffer [TODO:description]
 * @param[in] n_channels [TODO:description]
 * @param[in] channel_max [TODO:description]
 * @param[in] index [TODO:description]
 * @param[in] radius [TODO:description]
 * @param[in] diameter [TODO:description]
 * @param[in] min_index [TODO:description]
 * @return 1 if all channels are in coincidence, 0 otherwise
 */
static inline u64
JOIN(STUB, channels_in_coincidence)(const BUFFER* const buffer,
                                    const u8 n_channels,
                                    const u64* const channel_max,
                                    const u64* const index,
                                    const u64 radius,
                                    const u64 diameter,
                                    const u64 min_index) {

    usize oldest =
      channel_max[min_index] - ArrivalTimeAt(buffer, index[min_index]);
    usize in_coincidence = 0;

    usize j = 0;
    usize newer = 0;
    for (j = 0; j < min_index; j++) {
        newer = channel_max[j] - ArrivalTimeAt(buffer, index[j]);
        if ((newer + radius - oldest) < diameter) {
            in_coincidence++;
        } else {
            break;
        }
    }

    for (j = min_index + 1; j < n_channels; j++) {
        newer = channel_max[j] - ArrivalTimeAt(buffer, index[j]);
        if ((newer + radius - oldest) < diameter) {
            in_coincidence++;
        } else {
            break;
        }
    }

    usize coincidence_size = (usize)n_channels - 1;
    return (in_coincidence == coincidence_size) ? 1 : 0;
}
#define InCoincidence(BUF, N, CH_MAX, IDX, RAD, DIA, MIN)                      \
    JOIN(STUB, channels_in_coincidence)(BUF, N, CH_MAX, IDX, RAD, DIA, MIN)

// are the const qualifiers really needed, I guess they are good for signalling
// intent but, that s a lot of extra visual noise
/**
 * @brief Counts number of occurences a set of channels were within a
 * coincidence window
 *
 * @param[in] buffer [TODO:description]
 * @param[in] n_channels [TODO:description]
 * @param[in] channels [TODO:description]
 * @param[in] delays [TODO:description]
 * @param[in] radius [TODO:description]
 * @param[in] read_time [TODO:description]
 * @return number of coincidences found
 */
static inline u64
JOIN(STUB, coincidences_count)(const BUFFER* const buffer,
                               const usize n_channels,
                               u8* channels,
                               const f64* delays,
                               const f64 radius,
                               const f64 read_time) {

    pattern_iterator pattern =
      PatternIteratorInit(buffer, n_channels, channels, delays, read_time);

    RESOLUTION res = *(buffer->resolution);
    u64 radius_bins = BinsFromTime(res, radius);
    u64 diameter_bins = radius_bins + radius_bins;

    bool in_range = true;
    u64 count = 0;
    while (in_range == true) {
        pattern.oldest =
          ArgMin(buffer, pattern.limit, pattern.index, n_channels);

        count += InCoincidence(buffer,
                               n_channels,
                               pattern.limit,
                               pattern.index,
                               radius_bins,
                               diameter_bins,
                               pattern.oldest);

        in_range = NextForChannel(buffer,
                                  &pattern.iters[pattern.oldest],
                                  channels[pattern.oldest],
                                  &pattern.index[pattern.oldest]);
    }

    PatternIteratorDeinit(&pattern);

    return count;
}

#define CC_MEASUREMENT JOIN(STUB, cc_measurement)
typedef struct CC_MEASUREMENT CC_MEASUREMENT;
struct CC_MEASUREMENT {
    RESOLUTION resolution;
    f64 read_time;
    usize total_records;
    usize n_channels;
    u8* channels;
    TT_VECTOR* records;
};

static inline CC_MEASUREMENT*
JOIN(STUB, coincidence_measurement_new)(RESOLUTION resolution,
                                        usize n_channels,
                                        u8* channels) {

    CC_MEASUREMENT* measurement =
      (CC_MEASUREMENT*)malloc(sizeof(CC_MEASUREMENT));
    measurement->resolution = resolution;
    measurement->read_time = 0;
    measurement->total_records = 0;
    measurement->n_channels = n_channels;
    measurement->channels = channels;
    measurement->records = TT_VECTOR_INIT(128);

    return measurement;
}

static inline CC_MEASUREMENT*
JOIN(STUB, coincidence_measurement_delete)(CC_MEASUREMENT* measurement) {
    TT_VECTOR_DEINIT(measurement->records);
    free(measurement);
    measurement = NULL;
    return measurement;
}

/**
 * @brief Collect records found to be in coincidence according to channels in
 * measurement
 *
 * @param[in, out] buffer
 * @param[in] delays
 * @param[in] radius
 * @param[in] read_time integration time: t(head) - t(head - bins(read_time))
 * @param[in, out] measurement pointer to struct
 * @return number of coincidences found
 */
static inline usize
JOIN(STUB, coincidences_records)(const BUFFER* const buffer,
                                 const f64* delays,
                                 const f64 radius,
                                 const f64 read_time,
                                 CC_MEASUREMENT* measurement) {

    if (measurement == NULL) {
        // TODO: error message here
        return 0;
    }

    measurement->resolution = *(buffer->resolution);
    measurement->read_time = read_time;

    pattern_iterator pattern = PatternIteratorInit(buffer,
                                                   measurement->n_channels,
                                                   measurement->channels,
                                                   delays,
                                                   read_time);

    RESOLUTION res = *(buffer->resolution);
    u64 radius_bins = BinsFromTime(res, radius);
    u64 diameter_bins = radius_bins + radius_bins;

    bool in_range = true;
    u64 check = 0;
    u64 count = 0;

    while (in_range == true) {
        pattern.oldest =
          ArgMin(buffer, pattern.limit, pattern.index, measurement->n_channels);

        check = InCoincidence(buffer,
                              measurement->n_channels,
                              pattern.limit,
                              pattern.index,
                              radius_bins,
                              diameter_bins,
                              pattern.oldest);

        if (check == 1) {
            for (usize i = 0; i < measurement->n_channels; i++) {
                TT_VECTOR_PUSH(measurement->records,
                               TimestampAt(buffer, pattern.index[i]));
            }
        }

        count += check;

        in_range = NextForChannel(buffer,
                                  &pattern.iters[pattern.oldest],
                                  measurement->channels[pattern.oldest],
                                  &pattern.index[pattern.oldest]);
    }

    PatternIteratorDeinit(&pattern);
    measurement->total_records = count * measurement->n_channels;

    return count;
}

/**
 * @brief [TODO:summary]
 *
 * @param[in] buffer [TODO:description]
 * @param[in] read_time [TODO:description]
 * @param[in] bin_width [TODO:description]
 * @param[in] channels [TODO:description]
 * @param[in] n_channels [TODO:description]
 * @param[in, out] intensities [TODO:description]
 * @return [TODO:description]
 */
static inline u64
JOIN(STUB, timetrace)(const BUFFER* const buffer,
                      const f64 read_time,
                      const usize bin_width,
                      const u8* channels,
                      const usize n_channels,
                      u64* intensities) {
    RESOLUTION res = *(buffer->resolution);
    u64 start_time = BinsFromTime(res, TimeInBuffer(buffer) - read_time);
    usize index = LowerBound(buffer, start_time);

    circular_iterator iter = { 0 };
    u64 capacity = *(buffer->capacity);
    u64 count = *(buffer->count);
    iterator_init(&iter, capacity, index, count);
    index = iter.lower.index;

    usize i = 0;
    usize j = 0;
    u64 offset = 1;
    u8 current_channel = 0;
    u64 intensity = 0;
    u64 end_of_bin = ArrivalTimeAt(buffer, index);
    while (0 != offset) {

        current_channel = ChannelAt(buffer, index);
        for (i = 0; i < n_channels; i++) {
            if (current_channel == channels[i]) {
                intensity++;
                break;
            }
        }

        if (ArrivalTimeAt(buffer, index) > end_of_bin) {
            intensities[j] = intensity;
            j++;
            intensity = 0;
            end_of_bin += bin_width;
        }

        offset = next(&iter);
        if (0 == offset) {
            break;
        }
        index = offset;
    }

    return j;
}
#define Timetrace(BUF, RT, BW, CHs, INTENS)                                    \
    JOIN(STUB, timetrace)(BUF, RT, BW, CHs, INTENS)

/*! \fn Find zero delay between a pair of channels
 * \param buffer
 * \param read_time
 * \param correlation_window
 * \param resolution
 * \param channels_a
 * \param channels_b
 * \param n_bins
 * \param intensities
 */
static inline void
JOIN(STUB, find_zero_delay)(const BUFFER* const buffer,
                            const f64 read_time,
                            const u64 correlation_window,
                            const u64 resolution,
                            const u8 channels_a,
                            const u8 channels_b,
                            const u64 n_bins,
                            u64* intensities) {
    RESOLUTION res = *(buffer->resolution);
    u64 start_time = BinsFromTime(res, TimeInBuffer(buffer) - read_time);
    usize index = LowerBound(buffer, start_time);

    circular_iterator iter = { 0 };
    u64 capacity = *(buffer->capacity);
    u64 count = *(buffer->count);
    iterator_init(&iter, capacity, index, count);
    index = iter.lower.index;

    u64 central_bin = n_bins / 2;

    u8 current_channel = 0;
    u64 time_of_arrival = 0;
    u64 previous_a = 0;
    u64 previous_b = 0;
    u64 delta = 0;
    u64 offset = 1;
    u64 hist_index = 0;
    while (0 != offset) {
        current_channel = ChannelAt(buffer, index);
        time_of_arrival = ArrivalTimeAt(buffer, index);

        if (channels_a == current_channel) {
            previous_a = time_of_arrival;
            delta = time_of_arrival - previous_b;
            if (delta < correlation_window) {
                hist_index = central_bin - (delta / resolution) - 1;
                intensities[hist_index] += 1;
            }
        } else if (channels_b == current_channel) {
            previous_b = time_of_arrival;
            delta = time_of_arrival - previous_a;
            if (delta < correlation_window) {
                hist_index = central_bin + (delta / resolution);
                intensities[hist_index] += 1;
            }
        }

        offset = next(&iter);
        if (0 == offset) {
            break;
        }
        index = offset;
    }
}
#define FindZeroDelay(BUF, RT, CW, RES, CH_A, CH_B, N, INTENS)                 \
    JOIN(STUB, find_zero_delay)(BUF, RT, CW, RES, CH_A, CH_B, N, INTENS)

#undef STUB
#undef T
#undef TS
#undef RESOLUTION
#undef SLICE
#undef TT_VECTOR
#undef TT_VECTOR_INIT
#undef TT_VECTOR_DEINIT
#undef TT_VECTOR_PUSH
#undef TT_VECTOR_RESET
// #undef CC_RESULT
//
// #undef REC_VEC
#undef BUFFER
#undef BUFFER_INFO
#undef _SETFIELD
#undef SETFIELD
#undef GETFIELD
#undef _GETFIELD

#undef AbsIdx
#undef RecordAt
#undef ChannelAt
#undef ArrivalTimeAt
#undef BinsFromTime
#undef TimeFromBins
#undef ToTime
#undef ToBins
#undef CMP
#undef EQL
#undef LowerBound
#undef BinsFromTimeDelays
#undef TimeInBuffer
#undef ArgMin
#undef PatternIteratorInit
#undef PatternIteratorDeinit
#undef NextForChannel
#undef InCoincidence
#undef Timetrace
