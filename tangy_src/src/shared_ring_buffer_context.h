#ifndef __SHARED_RINGBUFFER__
#define __SHARED_RINGBUFFER__

#include "base.h"
#include "shared_memory.h"

typedef struct shared_ring_buffer shared_ring_buffer;
struct shared_ring_buffer {
    char* map_ptr;
    u64 length_bytes;
    fd_t file_descriptor;
    char* name;
};

typedef struct shared_ring_buffer_context shared_ring_buffer_context;
struct shared_ring_buffer_context {
    f64 resolution;
    f64 clock_period;
    u64 resolution_bins;
    u64 clock_period_bins;
    u64 conversion_factor;
    u64 capacity;
    u64 count;
    u64 reference_count;
    u64 channel_count;
};

static inline u64 srb_context_size() {
    return 9 * sizeof(u64);
}

static inline u64 srb_conversion_factor(f64 resolution, f64 clock_period) {
    u64 factor = (u64)round(clock_period / resolution);
    return factor;
}

static inline f64
srb_get_resolution(shared_ring_buffer* buffer) {
    return ((f64*)buffer->map_ptr)[0];
}

static inline void
srb_set_resolution(shared_ring_buffer* buffer, f64 resolution) {
    ((f64*)buffer->map_ptr)[0] = resolution;
}

static inline f64
srb_get_clock_period(shared_ring_buffer* buffer) {
    return ((f64*)buffer->map_ptr)[1];
}

static inline void
srb_set_clock_period(shared_ring_buffer* buffer, f64 clock_period) {
    ((f64*)buffer->map_ptr)[1] = clock_period;
}

static inline f64
srb_get_resolution_bins(shared_ring_buffer* buffer) {
    return ((f64*)buffer->map_ptr)[2];
}

static inline void
srb_set_resolution_bins(shared_ring_buffer* buffer, f64 resolution_bins) {
    ((f64*)buffer->map_ptr)[2] = resolution_bins;
}

static inline u64
srb_get_clock_period_bins(shared_ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[3];
}

static inline void
srb_set_clock_period_bins(shared_ring_buffer* buffer, u64 clock_period_bins) {
    ((u64*)buffer->map_ptr)[3] = clock_period_bins;
}

static inline u64
srb_get_conversion_factor(shared_ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[4];
}

static inline void
srb_set_conversion_factor(shared_ring_buffer* buffer, u64 conversion_factor) {
    ((u64*)buffer->map_ptr)[4] = conversion_factor;
}

static inline u64
srb_get_capacity(shared_ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[5];
}

static inline void
srb_set_capacity(shared_ring_buffer* buffer, u64 capacity) {
    ((u64*)buffer->map_ptr)[5] = capacity;
}

static inline u64
srb_get_count(shared_ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[6];
}

static inline void
srb_set_count(shared_ring_buffer* buffer, u64 count) {
    ((u64*)buffer->map_ptr)[6] = count;
}

static inline u64
srb_get_reference_count(shared_ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[7];
}

static inline void
srb_set_reference_count(shared_ring_buffer* buffer, u64 reference_count) {
    ((u64*)buffer->map_ptr)[7] = reference_count;
}

static inline u64
srb_get_channel_count(shared_ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[8];
}

static inline void
srb_set_channel_count(shared_ring_buffer* buffer, u64 channel_count) {
    ((u64*)buffer->map_ptr)[8] = channel_count;
}

static inline void srb_reference_count_increment(shared_ring_buffer* buffer) {
    u64 rc = srb_get_reference_count(buffer);
    srb_set_reference_count(buffer, rc + 1);
}

static inline void srb_reference_count_decrement(shared_ring_buffer* buffer) {
    u64 rc = srb_get_reference_count(buffer);
    if (rc > 0) {
        srb_set_reference_count(buffer, rc - 1);
    }
}

static inline tbResult
srb_init(const u64 length_bytes,
        char* name,
        f64 resolution,
        f64 clock_period,
        u64 conversion_factor,
        u64 capacity,
        u64 count,
        u64 channel_count,
        shared_ring_buffer* buffer) {

    shared_mapping map = { 0 };
    map.name = name;
    tbResult result = shmem_create(length_bytes, &map);
    if (false == result.Ok) {
        return result;
    }

    buffer->map_ptr = map.data;
    buffer->length_bytes = length_bytes;
    buffer->file_descriptor = map.file_descriptor;
    buffer->name = name;

    srb_set_resolution(buffer, resolution);
    srb_set_resolution_bins(buffer, (u64)roundl(1 / resolution));
    srb_set_clock_period(buffer, clock_period);
    srb_set_clock_period_bins(buffer, (u64)roundl(1 / clock_period));
    srb_set_conversion_factor(buffer, conversion_factor);
    srb_set_capacity(buffer, capacity);
    srb_set_count(buffer, count);
    srb_set_reference_count(buffer, 1);
    srb_set_channel_count(buffer, channel_count);

    return result;
}

static inline tbResult
srb_deinit(shared_ring_buffer* buffer) {
    shared_mapping map = { .file_descriptor = buffer->file_descriptor,
                           .name = buffer->name,
                           .data = buffer->map_ptr };
    u8 exists = 0;
    tbResult result = shmem_exists(buffer->name, &exists);
    if (result.Ok == false) {
        return result;
    }

    srb_reference_count_decrement(buffer);

    u64 reference_count = srb_get_reference_count(buffer);
    if ((exists == 1) & (reference_count <= 0)) {
        result = shmem_close(&map);
        if (result.Ok == false) {
            return result;
        }
    }
    free((char*)map.name);
    result.Ok = true;
    return result;
}

static inline tbResult
srb_connect(char* name, shared_ring_buffer* buffer, shared_ring_buffer_context* context) {
    u8 exists = 0;
    tbResult result = shmem_exists(name, &exists);
    if (result.Ok == false) {
        return result;
    }

    shared_mapping map = {0};
    map.name = name;
    result = shmem_connect(&map);
    if (result.Ok == false) {
        return result;
    }

    buffer->map_ptr = map.data;
    buffer->file_descriptor = map.file_descriptor;
    buffer->name = map.name;

    result.Ok = true;
    srb_reference_count_increment(buffer);
    return result;
}

static inline void
srb_set_context(shared_ring_buffer* buffer,
               f64 resolution,
               f64 clock_period,
               u64 conversion_factor,
               u64 count,
               u64 reference_count,
               u64 channel_count) {

    srb_set_resolution(buffer, resolution);
    srb_set_resolution_bins(buffer, (u64)roundl(1 / resolution));
    srb_set_clock_period(buffer, clock_period);
    srb_set_clock_period_bins(buffer, (u64)roundl(1 / clock_period));
    srb_set_conversion_factor(buffer, conversion_factor);
    srb_set_count(buffer, count);
    srb_set_reference_count(buffer, reference_count);
    srb_set_channel_count(buffer, channel_count);
}

static inline void
srb_get_context(shared_ring_buffer* buffer, shared_ring_buffer_context* context) {
    context->resolution = srb_get_resolution(buffer);
    context->resolution_bins = srb_get_resolution_bins(buffer);
    context->clock_period = srb_get_clock_period(buffer);
    context->clock_period_bins = srb_get_clock_period_bins(buffer);
    context->conversion_factor = srb_get_conversion_factor(buffer);
    context->count = srb_get_count(buffer);
    context->reference_count = srb_get_reference_count(buffer);
    context->channel_count = srb_get_channel_count(buffer);
}

#endif
