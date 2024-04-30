#ifndef __TANGY__
#define __TANGY__

#include "clocked_buffer.h"
#include "standard_buffer.h"

typedef enum { STANDARD, CLOCKED } tangy_buffer_tag;

typedef union {
    const std_buffer* standard;
    const clk_buffer* clocked;
} tangy_buffer_union;

typedef struct tangy_buffer tangy_buffer;
struct tangy_buffer {
    tangy_buffer_tag tag;
    tangy_buffer_union* value;
};

static inline tangy_buffer
tangy_buffer_new(tangy_buffer_tag tag) {
    tangy_buffer buffer;
    buffer.tag = tag;

    switch (buffer.tag) {
        case STANDARD:
            buffer.value->standard = std_buffer_new();
            break;
        case CLOCKED:
            buffer.value->clocked = clk_buffer_new();
            break;
    }
    return buffer;
}

typedef union {
    std_res standard;
    clk_res clocked;
} tangy_resolution;

static inline tbResult
tangy_buffer_init(u64 num_elements,
                  tangy_resolution resolution,
                  u8 n_channels,
                  char* name,
                  tangy_buffer* buffer) {

    tbResult result;
    switch (buffer->tag) {
        case STANDARD:
            result = std_buffer_init(num_elements, resolution.standard, n_channels, name, buffer->value->standard);
            break;
        case CLOCKED:
            result = clk_buffer_init(num_elements, resolution.clocked, n_channels, name, buffer->value->clocked);
            break;
    }
    return result;
}

static inline tbResult
tangy_buffer_deinit(tangy_buffer* buffer) {
    switch (buffer->tag) {
        case STANDARD:
            return std_buffer_deinit(buffer->value->standard);
        case CLOCKED:
            return clk_buffer_deinit(buffer->value->clocked);
    }
}

static inline usize
tangy_buffer_lower_bound(tangy_buffer* buffer, usize key) {
    switch (buffer->tag) {
        case STANDARD:
            return std_buffer_lower_bound(buffer->value.standard, key);
        case CLOCKED:
            return clk_buffer_lower_bound(buffer->value.clocked, key);
    }
}

// static inline f64 tangy_buffer_time_in_buffer(const tangy_buffer* buffer) {
// }

#endif
