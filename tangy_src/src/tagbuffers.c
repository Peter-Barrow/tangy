
typedef struct {
    unsigned short channel;
    unsigned long long timetag;
} standard;

typedef double std_res;

typedef struct {
    unsigned short *channel;
    unsigned long long *timetag;
} base_ptrs;

#define T standard
#define RESOLUTION std_res
#define BASE_PTR base_ptrs

#include "ring_buffers.h"

void standard_buffer_set_resolution(char* data, std_res resolution) {
    union {
        std_res as_double;
        char* as_bytes[sizeof(std_res)];
    } converter;

    unsigned long long size = sizeof(std_res);

    memcpy(&converter.as_double, &resolution, size);

    unsigned long long offset = offsetof(standard_buffer_info, resolution);
    memcpy(&data[offset], converter.as_bytes, size);
}

u64 standard_size_of() {
    u64 elem_size = sizeof(uint8_t) + sizeof(uint64_t);
    return elem_size;
}

u64 standard_buffer_map_size(u64 num_elements) {
    u64 info_size = sizeof(standard_buffer_info);
    u64 elem_size = standard_size_of();
    return info_size + (elem_size * num_elements);
}

standard standard_get_record(const standard_buffer *const buffer,
                             const standard_buffer_info *const info,
                             u64 index) {
    u64 idx = index % info->capacity;
    standard record = {
        .channel = buffer->base_ptrs.channel[idx],
        .timetag = buffer->base_ptrs.timetag[idx]
    };
    return record;
}
