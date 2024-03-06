typedef struct {
    unsigned short channel;
    unsigned long long timetag;
} standard;

typedef double std_res;

#define T standard
#define S standard_array
#define R std_res

#ifndef T
#error "No template type 'T' suppled for buffer_info"
#endif

#ifndef S
#error "No template type 'S' for slice supplied"
#endif

#ifndef R
#error "No template type 'R' for resolution supplied"
#endif


#define __RING_BUFFER__
#define INFO JOIN(info, T)
#define RESOLUTION JOIN(info, R)

#include "./tagbuffers.h"
#include "./shared_memory.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define _str(s) str(s)
#define str(s) #s
#define TS_MEM_MAP_NAME str(JOIN(T, _tagStream))

#define alignof(x) (size) _Alignof(x)

// TODO:
// - add a templated type "MAPS" to hold shared maps for each field
// - buffer info, like resolution and count can go in its own shared map
// - OPTIONALLY: convert each map into a "magic ring"
// - best way to share a string? Name fields should go at end of structs, can 
// then alloc size of struct plus size of string in bytes as map and memcpy in

typedef struct {
    u64 capacity;
    R resolution;
    u64 file_descriptor;
    u64 *count;
    u64 *index_of_reference; // pointer to index of reference record
    u8 n_channels;
} JOIN(T, buffer_info);

static inline JOIN(T, buffer_info) JOIN(T, buffer_info_from_bytes)(byte *data) {
    usize struct_size = sizeof(JOIN(T, buffer_info));
    byte *buffer = (byte *)malloc(struct_size);
    size_t i;
    for (i = 0; i < struct_size; i++) {
        buffer[i] = data[i];
    }
    JOIN(T, buffer_info) *info = (JOIN(T, buffer_info) *)buffer;
    info->count = &((u64 *)data)[offsetof(JOIN(T, buffer_info), count) / 8];
    return *info;
}

// setters

static inline void JOIN(T, buffer_set_capacity)(byte *data, u64 capacity) {
    usize offset = offsetof(JOIN(T, buffer_info), capacity) / 8;
    ((u64 *)data)[offset] = capacity;
}

void JOIN(T, buffer_set_resolution)(byte *data, R resolution);

static inline void JOIN(T, buffer_set_file_descriptor)(byte *data, u64 fd) {
    usize offset = offsetof(JOIN(T, buffer_info), file_descriptor) / 8;
    ((u64 *)data)[offset] = fd;
}

static inline void JOIN(T, buffer_set_num_channels)(byte *data, u8 n) {
    usize offset = offsetof(JOIN(T, buffer_info), n_channels) / 8;
    ((u64 *)data)[offset] = n;
}

static inline void JOIN(T, buffer_set_count)(byte *data, u64 amount) {
    usize offset = offsetof(JOIN(T, buffer_info), count) / 8;
    ((u64 *)data)[offset] = amount;
}

// getters

static inline u64 JOIN(T, buffer_count)(byte *data) {
    usize offset = offsetof(JOIN(T, buffer_info), count) / 8;
    return ((u64 *)data)[offset];
}

u64 JOIN(T, get_record)(JOIN(T, buffer) buffer, usize index);

u64 JOIN(T, map_size)(u64 num_elements);

typedef struct {
    byte *map_ptr;
    S base_ptrs;
    byte name[name_length]; /* do we need a string type? */
} JOIN(T, buffer);

u64 JOIN(T, size_of)();
S JOIN(T, init_base_ptrs)(byte *data);

// make an error payload struct here for the return type
static inline shmemResult JOIN(T, buffer_init)(u64 num_elements, byte *name,
                                               JOIN(T, buffer) * buffer) {


    // buffer is an out parameter
    u64 tag_size = JOIN(T, size_of)();
    u64 num_bytes = sizeof(JOIN(T, buffer_info)) + (tag_size * num_elements);

    shared_mapping mapping = {0};
    shmemResult result = shmem_create(num_bytes, &mapping);
    if (false == result.Ok) {
        result.Error = result.Error;
        return result;
    }

    buffer->map_ptr = mapping.data;
    buffer->name = name;
    buffer->base_ptrs = JOIN(T, init_base_ptrs)(buffer->map_ptr);

    result.Ok = true;
    return result;
}

static inline shmemResult JOIN(T, buffer_connect)(byte *buffer_name,
                                                  JOIN(T, buffer) * buffer,
                                                  JOIN(T, buffer_info) * info) {
    shmemResult result = {0};
    result = shmem_exists(buffer_name);
    if (false == result.Ok) {
        return result;
    }

    shmemBufferResult connect_result = shmem_connect(buffer_name);
    if (false == connect_result.Ok) {
        result.Error = connect_result.Error;
        return result;
    }

    buffer->map_ptr = connect_result.map_ptr;
    buffer->name = buffer_name;
    buffer->base_ptrs = JOIN(T, init_base_ptrs)(buffer->map_ptr);

    JOIN(T, buffer_info)
    new_info = JOIN(T, buffer_info_from_bytes)(buffer->map_ptr);

    info->count = new_info.count;
    info->capacity = new_info.capacity;
    info->n_channels = new_info.n_channels;
    info->resolution = new_info.resolution;
    info->file_descriptor = connect_result.file_descriptor;

    result.Ok = true;
    return result;
}

static inline shmemResult JOIN(T, buffer_deinit)(JOIN(T, buffer) * buffer,
                                                 JOIN(T, buffer_info) * info) {

    shmemResult result = {0};
    result = shmem_close(info->file_descriptor, buffer->map_ptr);
    if (false == result.Ok) {
        return result;
    }

    free(buffer->name);
    free(buffer);
    free(info);

    result.Ok = true;
    return result;
}

// tag conversions
u64 JOIN(T, to_time)(T record, R resolution);
u64 JOIN(T, as_bins)(T record, R resolution);

static inline bool JOIN(T, compare)(T a, T b) {
    return JOIN(T, to_time)(a) < JOIN(T, to_time)(b);
}

static inline bool JOIN(T, equal)(T a, T b) {
    return JOIN(T, to_time)(a) == JOIN(T, to_time)(b);
}

// write to buffer
void JOIN(T, push)(JOIN(T, buffer) * buffer, JOIN(T, buffer_info) * info);
void JOIN(T, push_array)(JOIN(T, buffer) * buffer, JOIN(T, buffer_info) * info);

// Binary search
// static inline usize JOIN(T, lower_bound)(const JOIN(T, buffer) * buffer,
//                                          JOIN(T, buffer_info) info,
//                                          usize start_index, usize bins) {
// 
//     if (0 == bins) {
//         return start_index;
//     };
// 
//     if (!(start_index < *info.count)) {
//         return 0;
//     }
// 
//     usize min_index =
//         *info.count > info.capacity ? *info.count - info.capacity : 0;
// 
//     if (!(start_index >= min_index)) {
//         return 0;
//     }
// 
//     T record = {0};
//     record = JOIN(T, get_record)(buffer, min_index);
// 
//     usize right = start_index;
//     if ((bins + JOIN(T, as_bins)(record, info.resolution)) >=
//         JOIN(T, as_bins)(JOIN(T, get_record)(buffer, right), info.resolution)) {
//         return right - min_index;
//     };
// 
//     usize index = JOIN(T, get_record)(buffer, start_index) - bins;
//     usize left = min_index;
// 
//     if (!(left <= right)) {
//         return 0;
//     };
// 
//     usize temp;
//     while ((right - left) > 1) {
//         temp = (left - right) / 2;
//         record = JOIN(T, get_record)(buffer, temp);
//         if (JOIN(T, as_bins)(record, info.resolution) < index) {
//             left = temp + 1;
//         } else {
//             right = temp;
//         }
//     };
// 
//     record = JOIN(T, get_record)(buffer, left);
//     if (JOIN(T, as_bins)(record, info.resolution) < index) {
//         return start_index - right;
//     };
// 
//     return start_index - left;
// }

#undef T
#undef S
#undef R
