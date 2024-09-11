#include "./analysis_impl_standard.h"
#include "./base.h"
#include "./shared_ring_buffer_context.h"

#include <stdio.h>

#ifndef __QUTOOLS_READER__
#define __QUTOOLS_READER__

static inline u64
srb_read_header_qutools(shared_ring_buffer* buf, FILE* filehandle) {
    u8 header[40];
    fread(header, 40, 1, filehandle);

    u8* bytes[10];
    fread(bytes, 1, 10, filehandle);
    // jump back 10 bytes
    fseek(filehandle, -10, SEEK_CUR);
    return (*(uint64_t*)bytes);
}

static inline u64
srb_read_next_qutools(shared_ring_buffer* buf,
                      std_slice* data,
                      FILE* filehandle,
                      u64 timetag_offset,
                      u64 count_tags) {
    u8 channel = 0;
    u64 timetag = 0;

    u64 count_buffer = srb_get_count(buf);
    u64 capacity = srb_get_capacity(buf);
    u64 index = count_buffer % capacity;

    u8* bytes[10];
    u64 read_tags = 0;
    for (u64 i = 0; i < count_tags; i++) {
        u64 n = fread(bytes, 1, 10, filehandle);
        if (n != 10) {
            break;
        }
        read_tags += 1;
        timetag = (*(uint64_t*)bytes);
        channel = ((u8*)bytes)[8];
        data->channel[index] = channel;
        data->timestamp[index] = timetag - timetag_offset;
        index = (index + 1) % capacity;
    }

    srb_set_count(buf, count_buffer + read_tags);

    return 1;
}

#endif
