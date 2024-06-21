
#include "./base.h"

#include "./analysis_impl_clocked.h"
#include "./analysis_impl_standard.h"
#include "./ring_buffer_context.h"

#include <stdio.h>
#ifndef __picoquant__
#define __picoquant__

// #include <stdio.h>
// #include <stdlib.h>

#include <math.h>
// #include <stdint.h>

typedef struct {
    u8 channel;
    u64 time_tag;
} Record_HH2_T2;

typedef struct {
    u8 channel;
    u64 delta_t;
    u64 sync;
} Record_HH2_T3;

typedef struct {
    int photon;
    u64 overflow;
} res;

static inline int
Parse_HH1_T2(u32 record, Record_HH2_T2* Rec_struct, res* out) {

    const u64 T2WRAPAROUND_V2 = 33552000;

    u8 sp = (u8)record >> 31;
    u8 ch = (u8)((record >> 25) & 0x3f);
    u64 tt = (u64)(record & 0x01ffffff);
    int photon = 0;

    if (sp == 1) {
        if (ch == 0x3f) {
            out->overflow += T2WRAPAROUND_V2;
            if ((ch >= 1) & (ch <= 15)) {
                tt += out->overflow;
            };
            if (ch == 0) {
                tt += out->overflow;
                ++photon;
            };
        };
    } else {
        tt += out->overflow;
        ++ch;
        ++photon;
    };

    Rec_struct->channel = (u8)ch;
    Rec_struct->time_tag = (u64)tt;

    out->photon = photon;

    return photon;
}

static inline int
Parse_HH2_T2(u32 record, Record_HH2_T2* Rec_struct, res* out) {

    const u64 T2WRAPAROUND_V2 = 33554432;

    u8 sp = (u8)(record >> 31 & 1);
    u8 ch = (u8)((record >> 25) & 0b111111);
    u64 tt = (u64)(record & 0x01ffffff);
    int photon = 0;

    if (sp == 1) {
        if (ch == 0x3f) {
            if (tt == 0) {
                out->overflow += T2WRAPAROUND_V2;
            } else {
                out->overflow += (T2WRAPAROUND_V2 * tt);
            };

            if ((ch >= 1) & (ch <= 15)) {
                // marker
                tt += out->overflow;
                ++photon;
            };
            if (ch == 0) {
                // sync
                tt += out->overflow;
                ++photon;
            };
        };

    } else {
        // photon
        tt += out->overflow;
        ++photon;
        ch += 1;
    };

    Rec_struct->channel = (u8)ch;
    Rec_struct->time_tag = (u64)tt;

    out->photon = photon;

    return photon;
}

static inline int
Parse_HH2_T3(u32 record, Record_HH2_T3* Rec_struct, res* out) {

    const u64 T3WRAPAROUND_V2 = 1024;

    // u8 sp = (u8)(record >> 31 & 1);
    // u8 ch = (u8)((record >> 25) & 0b111111);
    // u64 dt = (u64)((record >> 10) & (0xffff >> 2));
    // u64 ns = (u64)(record & 0b1111111111);

    u32 sp = (record & 0b10000000000000000000000000000000) >> 31;
    u8 ch = (u8)((record & 0b01111110000000000000000000000000) >> 25);
    u64 dt = (u64)((record & 0b00000001111111111111110000000000) >> 10);
    u64 ns = (u64)(record & 0b00000000000000000000001111111111);

    int photon = 0;

    if (sp == 1) {
        if (ch == 0x3f) {
            if (ns == 0) {
                out->overflow += T3WRAPAROUND_V2;

            } else {
                out->overflow += (T3WRAPAROUND_V2 * ns);
            }
        }
        if ((ch >= 1) & (ch <= 15)) {
            ns += out->overflow;
        }
    } else {
        ns += out->overflow;
        photon++;
    };

    Rec_struct->channel = (u8)ch;
    Rec_struct->delta_t = (u64)dt;
    Rec_struct->sync = (u64)ns;

    out->photon = photon;

    return photon;
}

static inline void
Parse_HH2_T3_TAGS(u32 record,
                  int* channel,
                  u64* timetag,
                  u64* overflow,
                  double* resolution) {
    const u64 T3WRAPAROUND_V2 = 16843524;

    unsigned sp = record >> 31;
    unsigned ch = (record >> 25) & 0x3f;
    unsigned dt = (record >> 10) & (0xffff >> 2);
    unsigned ns = record & (0xfff >> 2);

    if (sp == 1) {
        if (ch == 0x3f) {
            if (ns == 0) {
                *overflow += T3WRAPAROUND_V2;
            } else {
                *overflow += (T3WRAPAROUND_V2 * ns);
            }
        }
        if ((ch >= 1) & (ch <= 15)) {
            ns += *overflow;
        }
    } else {
        ns += *overflow;
    };

    *channel = ch;
    *timetag = (u64)(round((double)(ns) * *resolution)) + dt;
}

// void Parse_HH2_T3(u32 record,
//                   int * channel,
//                   u64 * delta_t,
//                   u64 * sync,
//                   u64 * overflow);

void
Parse_HH2_T3_TAGS(u32 record,
                  int* channel,
                  u64* timetag,
                  u64* overflow,
                  double* resolution);

typedef struct {
    u64 overflow;
    u64 total_records;
    u64 record_count;
    u64 photon_count;
    u64 current_count;
} READER_STATUS;

static inline READER_STATUS*
set_reader_status(u64 num_records) {

    READER_STATUS* status;
    status = (READER_STATUS*)malloc(sizeof(READER_STATUS));

    status->overflow = 0;
    status->total_records = num_records;
    status->record_count = 0;
    status->photon_count = 0;
    status->current_count = 0;

    return status;
}

static inline u64
get_overflow(const READER_STATUS* const status) {
    return status->overflow;
}

static inline u64
get_total_records(const READER_STATUS* const status) {
    return status->total_records;
}

static inline u64
get_record_count(const READER_STATUS* const status) {
    return status->record_count;
}

static inline u64
get_photon_count(const READER_STATUS* const status) {
    return status->photon_count;
}

static inline u64
get_current_count(const READER_STATUS* const status) {
    return status->current_count;
}

static inline void
delete_reader_status(const READER_STATUS* const reader_stat) {
    free((void*)reader_stat);
}

static inline int
file_seek(FILE* filehandle, long int offset) {
    return fseek(filehandle, offset, SEEK_SET);
}

// tag_buffer* picoquant_reader(u64 buffer_size);

// static inline u64
// read_next_HH2_T2(const std_buffer* const buffer,
//                  FILE* filehandle,
//                  READER_STATUS* status,
//                  u64 n_tags) {
// 
//     unsigned int TTTRRec;
//     int rec_size = sizeof(u32);
//     int photon;
//     int n;
// 
//     status->current_count = 0;
// 
//     Record_HH2_T2 record = { 0 };
//     res out = { 0 };
//     out.photon = 0;
//     out.overflow = status->overflow;
// 
//     u64 count = ((std_buffer_info*)buffer->map_ptr)->count;
//     if ((status->total_records - count) < n_tags) {
//         n_tags = status->total_records - count;
//     };
// 
//     u64 capacity = ((std_buffer_info*)buffer->map_ptr)->capacity;
//     usize index = (count) % capacity;
//     while ((status->current_count <= n_tags) &&
//            (status->record_count <= status->total_records)) {
// 
//         // found the bottleneck, this should be called as few times as possible
//         // i.e. just read some number of pages at a time
//         n = fread(&TTTRRec, 1, rec_size, filehandle);
//         if (n != rec_size) {
//             break;
//         }
// 
//         status->record_count += 1;
//         photon = Parse_HH2_T2(TTTRRec, &record, &out);
// 
//         if (photon == 1) {
//             buffer->ptrs.channel[index] = record.channel;
//             buffer->ptrs.timestamp[index] = record.time_tag;
//             ++status->current_count;
//             index = (index + 1) % capacity;
//         };
//     };
// 
//     status->photon_count += status->current_count;
//     status->overflow = out.overflow;
// 
//     ((std_buffer_info*)buffer->map_ptr)->count = count + status->current_count;
// 
//     return 1;
// }
// 
// // TODO: implement this ...
// // static inline u64 new_read_next_HH2_T3(const clk_buffer * const buffer,
// //                                        FILE * filehandle, READER_STATUS *
// //                                        status, u64 n_tags) {
// //     u32 raw_records[1024] = {0};
// //
// //     int chunk_size = 1024;
// //     int n_chunks = n_tags % chunk_size;
// //     int n = 0;
// //
// //     // lets see if we can get the splitting done here like in [std,
// //     clk]_singles usize index = (*buffer->count) % (*buffer->capacity);
// //
// //     int i = 0;
// //     for (i = 0; i < n_chunks; i ++) {
// //         n = fread(&raw_records, chunk_size, sizeof(u32), filehandle);
// //         for (int j = 0; j < chunk_size; j ++) {
// //
// //         }
// //
// //     }
// //
// //     int count = i * n_chunks;
// //     int remainder = n_tags > count ? n_tags - count : 0;
// //
// //     if (0 != count) {
// //         n = fread(&raw_records, remainder, sizeof(u32), filehandle);
// //     }
// //
// //     return count + remainder;
// // }
// 
// static inline u64
// read_next_HH2_T3(const clk_buffer* const buffer,
//                  FILE* filehandle,
//                  READER_STATUS* status,
//                  u64 n_tags) {
// 
//     unsigned int TTTRRec;
//     int rec_size = sizeof(u32);
//     int photon;
//     int n;
// 
//     status->current_count = 0;
// 
//     Record_HH2_T3 record = { 0 };
//     res out = { 0 };
//     out.photon = 0;
//     out.overflow = status->overflow;
// 
//     u64 count = ((clk_buffer_info*)buffer->map_ptr)->count;
//     if ((status->total_records - count) < n_tags) {
//         n_tags = status->total_records - count;
//     };
// 
//     u64 capacity = ((clk_buffer_info*)buffer->map_ptr)->capacity;
//     usize index = (count) % capacity;
//     while ((status->current_count < n_tags) &&
//            (status->record_count <= status->total_records)) {
// 
//         n = fread(&TTTRRec, 1, rec_size, filehandle);
//         if (n != rec_size) {
//             break;
//         }
//         status->record_count += 1;
//         photon = Parse_HH2_T3(TTTRRec, &record, &out);
// 
//         if (photon == 1) {
//             buffer->ptrs.channel[index] = record.channel;
//             buffer->ptrs.timestamp[index] =
//               (clk_timetag){ .clock = record.sync, .delta = record.delta_t };
//             ++status->current_count;
//             index = (index + 1) % capacity;
//         };
//     };
// 
//     status->photon_count += status->current_count;
//     status->overflow = out.overflow;
// 
//     ((clk_buffer_info*)buffer->map_ptr)->count = count + status->current_count;
// 
//     return 1;
// }
// 
// static inline u64
// read_time_HH2_T2(const std_buffer* const buffer,
//                  FILE* filehandle,
//                  READER_STATUS* status,
//                  u64 max_time) {
// 
//     // does cur_sync need to have the reference subtracted?
//     // while ((cur_sync < max_time) && (count <= rec_num)){
// 
//     unsigned int TTTRRec;
//     int rec_size = sizeof(u32);
//     int photon;
//     int n;
// 
//     status->current_count = 0;
// 
//     Record_HH2_T2 record = { 0 };
//     res out = { 0 };
//     out.photon = 0;
//     out.overflow = status->overflow;
// 
//     u64 count = ((std_buffer_info*)buffer->map_ptr)->count;
//     u64 capacity = ((std_buffer_info*)buffer->map_ptr)->capacity;
//     usize index = (count) % capacity;
//     while ((record.time_tag < max_time) &&
//            (status->record_count <= status->total_records)) {
// 
//         n = fread(&TTTRRec, 1, rec_size, filehandle);
//         if (n != rec_size) {
//             break;
//         }
//         status->record_count += 1;
//         photon = Parse_HH2_T2(TTTRRec, &record, &out);
// 
//         if (photon != 0) {
// 
//             ++status->current_count;
//             buffer->ptrs.channel[index] = record.channel;
//             buffer->ptrs.timestamp[index] = record.time_tag;
//             index = (index + 1) % capacity;
//         };
//     };
// 
//     status->photon_count += status->current_count;
//     status->overflow = out.overflow;
//     ((std_buffer_info*)buffer->map_ptr)->count = count + status->current_count;
// 
//     return 1;
// }
// 
// static inline u64
// read_time_HH2_T3(const clk_buffer* const buffer,
//                  FILE* filehandle,
//                  READER_STATUS* status,
//                  u64 max_time) {
// 
//     // does cur_sync need to have the reference subtracted?
//     // while ((cur_sync < max_time) && (count <= rec_num)){
// 
//     unsigned int TTTRRec;
//     int rec_size = sizeof(u32);
//     int photon;
//     int n;
// 
//     status->current_count = 0;
// 
//     Record_HH2_T3 record = { 0 };
//     res out = { 0 };
//     out.photon = 0;
//     out.overflow = status->overflow;
// 
//     u64 count = ((clk_buffer_info*)buffer->map_ptr)->count;
//     u64 capacity = ((clk_buffer_info*)buffer->map_ptr)->capacity;
//     usize index = (count) % capacity;
//     while ((record.sync < max_time) &&
//            (status->record_count <= status->total_records)) {
// 
//         n = fread(&TTTRRec, 1, rec_size, filehandle);
//         if (n != rec_size) {
//             break;
//         }
//         status->record_count += 1;
//         photon = Parse_HH2_T3(TTTRRec, &record, &out);
// 
//         if (photon == 1) {
// 
//             ++status->current_count;
//             buffer->ptrs.channel[index] = record.channel;
//             buffer->ptrs.timestamp[index] =
//               (clk_timetag){ .clock = record.sync, .delta = record.delta_t };
//             // buffer->ptrs.clock[index] = record.sync;
//             // buffer->ptrs.delta[index] = record.delta_t;
//             index = (index + 1) % capacity;
//         };
//     };
// 
//     status->photon_count += status->current_count;
//     status->overflow = out.overflow;
//     ((clk_buffer_info*)buffer->map_ptr)->count = count + status->current_count;
// 
//     return 1;
// }

static inline u64
rb_read_next_HH2_T2(ring_buffer* buf,
                    std_slice* data,
                    FILE* filehandle,
                    READER_STATUS* status,
                    u64 count_tags) {

    u32 tttr_rec;
    u64 tttr_rec_size = sizeof(tttr_rec);
    int photon;
    u64 n;

    status->current_count = 0;
    Record_HH2_T2 record = { 0 };
    res out = { 0 };
    out.photon = 0;
    out.overflow = status->overflow;

    u64 count_buffer = rb_get_count(buf);

    if ((status->total_records - count_buffer) < count_tags) {
        count_tags = status->total_records - count_buffer;
    }

    u64 capacity = rb_get_capacity(buf);
    u64 index = count_buffer % capacity;

    while ((status->current_count <= count_tags) &&
           (status->record_count <= status->total_records)) {

        n = fread(&tttr_rec, 1, tttr_rec_size, filehandle);
        if (n != tttr_rec_size) {
            break;
        }

        status->record_count += 1;
        photon = Parse_HH2_T2(tttr_rec, &record, &out);

        if (photon == 1) {
            data->channel[index] = record.channel;
            data->timestamp[index] = record.time_tag;
            ++status->current_count;
            index = (index + 1) % capacity;
        }
    }

    status->photon_count += status->current_count;
    status->overflow = out.overflow;

    rb_set_count(buf, count_buffer + status->current_count);

    return 1;
}

static inline u64
rb_read_next_HH2_T3(ring_buffer* buf,
                    clk_slice* data,
                    FILE* filehandle,
                    READER_STATUS* status,
                    u64 count_tags) {

    u32 tttr_rec;
    u64 tttr_rec_size = sizeof(tttr_rec);
    int photon;
    u64 n;

    status->current_count = 0;
    Record_HH2_T3 record = { 0 };
    res out = { 0 };
    out.photon = 0;
    out.overflow = status->overflow;

    u64 count_buffer = rb_get_count(buf);

    if ((status->total_records - count_buffer) < count_tags) {
        count_tags = status->total_records - count_buffer;
    }

    u64 capacity = rb_get_capacity(buf);
    u64 index = count_buffer % capacity;

    while ((status->current_count < count_tags) &&
           (status->record_count <= status->total_records)) {

        n = fread(&tttr_rec, 1, tttr_rec_size, filehandle);
        if (n != tttr_rec_size) {
            break;
        }

        status->record_count += 1;
        photon = Parse_HH2_T3(tttr_rec, &record, &out);

        if (photon == 1) {
            data->channel[index] = record.channel;
            data->timestamp[index] =
              (clk_timetag){ .clock = record.sync, .delta = record.delta_t };
            status->current_count++;
            index = (index + 1) % capacity;
        }
    }

    status->photon_count += status->current_count;
    status->overflow = out.overflow;

    rb_set_count(buf, count_buffer + status->current_count);

    return 1;
}

#endif
