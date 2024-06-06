#ifndef __RINGBUFFER__
#define __RINGBUFFER__

#include "base.h"
#include "shared_memory.h"

typedef struct ring_buffer ring_buffer;
struct ring_buffer {
    char* map_ptr;
    u64 length_bytes;
    fd_t file_descriptor;
    char* name;
};

typedef struct ring_buffer_context ring_buffer_context;
struct ring_buffer_context {
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

static inline u64 rb_context_size() {
    return 9 * sizeof(u64);
}

static inline u64 rb_conversion_factor(f64 resolution, f64 clock_period) {
    u64 factor = (u64)round(clock_period / resolution);
    return factor;
}

static inline f64
rb_get_resolution(ring_buffer* buffer) {
    return ((f64*)buffer->map_ptr)[0];
}

static inline void
rb_set_resolution(ring_buffer* buffer, f64 resolution) {
    ((f64*)buffer->map_ptr)[0] = resolution;
}

static inline f64
rb_get_clock_period(ring_buffer* buffer) {
    return ((f64*)buffer->map_ptr)[1];
}

static inline void
rb_set_clock_period(ring_buffer* buffer, f64 clock_period) {
    ((f64*)buffer->map_ptr)[1] = clock_period;
}

static inline f64
rb_get_resolution_bins(ring_buffer* buffer) {
    return ((f64*)buffer->map_ptr)[2];
}

static inline void
rb_set_resolution_bins(ring_buffer* buffer, f64 resolution_bins) {
    ((f64*)buffer->map_ptr)[2] = resolution_bins;
}

static inline u64
rb_get_clock_period_bins(ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[3];
}

static inline void
rb_set_clock_period_bins(ring_buffer* buffer, u64 clock_period_bins) {
    ((u64*)buffer->map_ptr)[3] = clock_period_bins;
}

static inline u64
rb_get_conversion_factor(ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[4];
}

static inline void
rb_set_conversion_factor(ring_buffer* buffer, u64 conversion_factor) {
    ((u64*)buffer->map_ptr)[4] = conversion_factor;
}

static inline u64
rb_get_capacity(ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[5];
}

static inline void
rb_set_capacity(ring_buffer* buffer, u64 capacity) {
    ((u64*)buffer->map_ptr)[5] = capacity;
}

static inline u64
rb_get_count(ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[6];
}

static inline void
rb_set_count(ring_buffer* buffer, u64 count) {
    ((u64*)buffer->map_ptr)[6] = count;
}

static inline u64
rb_get_reference_count(ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[7];
}

static inline void
rb_set_reference_count(ring_buffer* buffer, u64 reference_count) {
    ((u64*)buffer->map_ptr)[7] = reference_count;
}

static inline u64
rb_get_channel_count(ring_buffer* buffer) {
    return ((u64*)buffer->map_ptr)[8];
}

static inline void
rb_set_channel_count(ring_buffer* buffer, u64 channel_count) {
    ((u64*)buffer->map_ptr)[8] = channel_count;
}

static inline void rb_reference_count_increment(ring_buffer* buffer) {
    u64 rc = rb_get_reference_count(buffer);
    rb_set_reference_count(buffer, rc + 1);
}

static inline void rb_reference_count_decrement(ring_buffer* buffer) {
    u64 rc = rb_get_reference_count(buffer);
    if (rc > 0) {
        rb_set_reference_count(buffer, rc - 1);
    }
}

static inline tbResult
rb_init(const u64 length_bytes,
        char* name,
        f64 resolution,
        f64 clock_period,
        u64 conversion_factor,
        u64 capacity,
        u64 count,
        u64 channel_count,
        ring_buffer* buffer) {

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

    rb_set_resolution(buffer, resolution);
    rb_set_resolution_bins(buffer, (u64)roundl(1 / resolution));
    rb_set_clock_period(buffer, clock_period);
    rb_set_clock_period_bins(buffer, (u64)roundl(1 / clock_period));
    rb_set_conversion_factor(buffer, conversion_factor);
    rb_set_capacity(buffer, capacity);
    rb_set_count(buffer, count);
    rb_set_reference_count(buffer, 1);
    rb_set_channel_count(buffer, channel_count);

    return result;
}

static inline tbResult
rb_deinit(ring_buffer* buffer) {
    shared_mapping map = { .file_descriptor = buffer->file_descriptor,
                           .name = buffer->name,
                           .data = buffer->map_ptr };
    u8 exists = 0;
    tbResult result = shmem_exists(buffer->name, &exists);
    if (result.Ok == false) {
        return result;
    }

    rb_reference_count_decrement(buffer);

    u64 reference_count = rb_get_reference_count(buffer);
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
rb_connect(char* name, ring_buffer* buffer, ring_buffer_context* context) {
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
    rb_reference_count_increment(buffer);
    return result;
}

static inline void
rb_set_context(ring_buffer* buffer,
               f64 resolution,
               f64 clock_period,
               u64 conversion_factor,
               u64 count,
               u64 reference_count,
               u64 channel_count) {

    rb_set_resolution(buffer, resolution);
    rb_set_resolution_bins(buffer, (u64)roundl(1 / resolution));
    rb_set_clock_period(buffer, clock_period);
    rb_set_clock_period_bins(buffer, (u64)roundl(1 / clock_period));
    rb_set_conversion_factor(buffer, conversion_factor);
    rb_set_count(buffer, count);
    rb_set_reference_count(buffer, reference_count);
    rb_set_channel_count(buffer, channel_count);
}

static inline void
rb_get_context(ring_buffer* buffer, ring_buffer_context* context) {
    context->resolution = rb_get_resolution(buffer);
    context->resolution_bins = rb_get_resolution_bins(buffer);
    context->clock_period = rb_get_clock_period(buffer);
    context->clock_period_bins = rb_get_clock_period_bins(buffer);
    context->conversion_factor = rb_get_conversion_factor(buffer);
    context->count = rb_get_count(buffer);
    context->reference_count = rb_get_reference_count(buffer);
    context->channel_count = rb_get_channel_count(buffer);
}

#endif
