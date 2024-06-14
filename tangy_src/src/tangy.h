#ifndef __TANGY__
#define __TANGY__

#include "base.h"
#include "ring_buffer_context.h"

// include implementations of analysis functions
#include "analysis_impl_clocked.h"
#include "analysis_impl_standard.h"

typedef enum { STANDARD, CLOCKED } buffer_format;

typedef union tangy_slice tangy_slice;
union tangy_slice {
    std_slice standard;
    clk_slice clocked;
};

typedef union tangy_field_ptrs tangy_field_ptrs;
union tangy_field_ptrs {
    std_slice standard;
    clk_field_ptrs clocked;
};

typedef union tangy_record_vec tangy_record_vec;
union tangy_record_vec {
    vec_std_timetag* standard;
    vec_clk_timetag* clocked;
};

typedef struct tangy_buffer tangy_buffer;
struct tangy_buffer {
    ring_buffer buffer;
    ring_buffer_context context;
    tangy_slice slice;
    tangy_record_vec records;
    buffer_format format;
};

static inline tbResult
tangy_buffer_init(buffer_format format,
                  char* name,
                  const u64 capacity,
                  f64 resolution,
                  f64 clock_period,
                  u64 channel_count,
                  tangy_buffer* t_buffer) {

    t_buffer->format = format;

    u64 num_bytes = 0;
    char* name_full;
    switch (format) {
        case STANDARD:
            num_bytes = std_buffer_map_size(capacity);
            name_full = std_buffer_name_full(name);
            break;
        case CLOCKED:
            num_bytes = clk_buffer_map_size(capacity);
            name_full = clk_buffer_name_full(name);
            break;
    }

    u64 factor = 1;
    if (clock_period > 0) {
        factor = rb_conversion_factor(resolution, clock_period);
    }

    tbResult result = rb_init(num_bytes,
                              name_full,
                              resolution,
                              clock_period,
                              factor,
                              capacity,
                              0,
                              channel_count,
                              &t_buffer->buffer);

    ring_buffer* buf = &t_buffer->buffer;
    switch (format) {
        case STANDARD:
            t_buffer->slice.standard = std_init_base_ptrs(buf);
            t_buffer->records.standard = std_vec_init(512);
            break;
        case CLOCKED:
            t_buffer->slice.clocked = clk_init_base_ptrs(buf);
            t_buffer->records.clocked = clk_vec_init(512);
            break;
    }

    return result;
}

static inline tbResult
tangy_buffer_deinit(tangy_buffer* t_buf) {
    tbResult result = rb_deinit(&t_buf->buffer);

    switch (t_buf->format) {
        case STANDARD:
            std_vec_deinit(t_buf->records.standard);
            break;
        case CLOCKED:
            clk_vec_deinit(t_buf->records.clocked);
            break;
    }

    return result;
}

static inline tbResult
tangy_buffer_connect(char* name, tangy_buffer* t_buf) {
    tbResult result;
    char* name_full;

    ring_buffer* buf = &t_buf->buffer;
    name_full = std_buffer_name_full(name);
    result = rb_connect(name_full, &t_buf->buffer, &t_buf->context);
    if (result.Ok == true) {
        t_buf->slice.standard = std_init_base_ptrs(buf);
        t_buf->format = STANDARD;
        t_buf->records.standard = std_vec_init(512);
        return result;
    }

    free(name_full);
    name_full = clk_buffer_name_full(name);
    result = rb_connect(name_full, &t_buf->buffer, &t_buf->context);
    if (result.Ok == true) {
        t_buf->slice.clocked = clk_init_base_ptrs(buf);
        t_buf->format = CLOCKED;
        t_buf->records.clocked = clk_vec_init(512);
        return result;
    }

    result.Ok = false;

    return result;
}

static inline void tangy_clear_buffer(tangy_buffer* t_buf) {
    switch (t_buf->format) {
        case STANDARD:
            std_clear_buffer(&t_buf->buffer, &t_buf->slice.standard);
            break;
        case CLOCKED:
            clk_clear_buffer(&t_buf->buffer, &t_buf->slice.clocked);
            break;
    }
}

// buffer access

// conversions

static inline u64
tangy_bins_from_time(tangy_buffer* t_buf, f64 time) {
    u64 bins = 0;

    f64 resolution = rb_get_resolution(&t_buf->buffer);

    switch (t_buf->format) {
        case STANDARD:
            bins = std_bins_from_time(resolution, time);
            break;
        case CLOCKED:
            bins = clk_bins_from_time(resolution, time);
            break;
    }

    return bins;
}

// slice and push

static inline u64
tangy_buffer_slice(tangy_buffer* t_buf,
                   tangy_field_ptrs* ptrs,
                   u64 start,
                   u64 stop) {
    u64 count = 0;
    switch (t_buf->format) {
        case STANDARD:
            count = std_buffer_slice(&t_buf->buffer,
                                     &t_buf->slice.standard,
                                     &ptrs->standard,
                                     start,
                                     stop);
            break;
        case CLOCKED:
            count = clk_buffer_slice(&t_buf->buffer,
                                     &t_buf->slice.clocked,
                                     &ptrs->clocked,
                                     start,
                                     stop);
            break;
    }
    return count;
}

static inline u64
tangy_buffer_push(tangy_buffer* t_buf,
                  tangy_field_ptrs* ptrs,
                  u64 start,
                  u64 stop) {

    u64 count = 0;
    switch (t_buf->format) {
        case STANDARD:
            count = std_buffer_push(&t_buf->buffer,
                                    &t_buf->slice.standard,
                                    &ptrs->standard,
                                    start,
                                    stop);
            break;
        case CLOCKED:
            count = clk_buffer_push(&t_buf->buffer,
                                    &t_buf->slice.clocked,
                                    &ptrs->clocked,
                                    start,
                                    stop);
            break;
    }
    return count;
}

// analysis

static inline u64
tangy_oldest_index(tangy_buffer* t_buf) {
    u64 index;

    switch (t_buf->format) {
        case STANDARD:
            index = std_oldest_index(&t_buf->buffer);
            break;
        case CLOCKED:
            index = clk_oldest_index(&t_buf->buffer);
            break;
    }
    return index;
}

static inline f64 tangy_oldest_time(tangy_buffer* t_buf) {

    f64 resolution = rb_get_resolution(&t_buf->buffer);
    u64 conversion_factor = rb_get_conversion_factor(&t_buf->buffer);
    u64 index = tangy_oldest_index(t_buf);

    u64 arrival_time = 0;
    f64 oldest_time = 0.0;
    switch (t_buf->format) {
        case STANDARD:
            arrival_time = std_arrival_time_at(&t_buf->slice.standard, conversion_factor, index);
            oldest_time = std_time_from_bins(resolution, arrival_time);
            return oldest_time;
        case CLOCKED:
            arrival_time = clk_arrival_time_at(&t_buf->slice.clocked, conversion_factor, index);
            oldest_time = clk_time_from_bins(resolution, arrival_time);
            return oldest_time;
    }

    return oldest_time;
}

static inline f64
tangy_current_time(tangy_buffer* t_buf) {
    f64 current_time = 0;

    switch (t_buf->format) {
        case STANDARD:
            current_time =
              std_current_time(&t_buf->buffer, &t_buf->slice.standard);
            break;
        case CLOCKED:
            current_time =
              clk_current_time(&t_buf->buffer, &t_buf->slice.clocked);
            break;
    }
    return current_time;
}

static inline f64
tangy_time_in_buffer(tangy_buffer* t_buf) {
    f64 time_in_buffer = 0;

    switch (t_buf->format) {
        case STANDARD:
            time_in_buffer =
              std_time_in_buffer(&t_buf->buffer, &t_buf->slice.standard);
            break;
        case CLOCKED:
            time_in_buffer =
              clk_time_in_buffer(&t_buf->buffer, &t_buf->slice.clocked);
            break;
    }

    return time_in_buffer;
}

static inline u64
tangy_lower_bound(tangy_buffer* t_buf, u64 key) {
    u64 position = 0;

    switch (t_buf->format) {
        case STANDARD:
            position =
              std_lower_bound(&t_buf->buffer, &t_buf->slice.standard, key);
            break;
        case CLOCKED:
            position =
              clk_lower_bound(&t_buf->buffer, &t_buf->slice.clocked, key);
            break;
    }

    return position;
}

static inline u64
tangy_singles(tangy_buffer* t_buf, u64 start, u64 stop, u64* counters) {
    u64 count = 0;

    switch (t_buf->format) {
        case STANDARD:
            count = std_singles(
              &t_buf->buffer, &t_buf->slice.standard, start, stop, counters);
            break;
        case CLOCKED:
            count = clk_singles(
              &t_buf->buffer, &t_buf->slice.clocked, start, stop, counters);
            break;
    }
    return count;
}

static inline u64
tangy_coincidence_count(tangy_buffer* t_buf,
                        u64 channel_count,
                        u8* channels,
                        f64* delays,
                        f64 time_coincidence_radius,
                        f64 time_read) {
    u64 count = 0;

    switch (t_buf->format) {
        case STANDARD:
            count = std_coincidence_count(&t_buf->buffer,
                                          &t_buf->slice.standard,
                                          channel_count,
                                          channels,
                                          delays,
                                          time_coincidence_radius,
                                          time_read);
            break;
        case CLOCKED:
            count = clk_coincidence_count(&t_buf->buffer,
                                          &t_buf->slice.clocked,
                                          channel_count,
                                          channels,
                                          delays,
                                          time_coincidence_radius,
                                          time_read);
            break;
    }
    return count;
}

static inline u64
tangy_coincidence_collect(tangy_buffer* t_buf,
                          u64 channel_count,
                          u8* channels,
                          f64* delays,
                          f64 time_coincidence_radius,
                          f64 time_read,
                          tangy_record_vec* records) {
    u64 count = 0;

    switch (t_buf->format) {
        case STANDARD:
            count = std_coincidence_collect(&t_buf->buffer,
                                            &t_buf->slice.standard,
                                            channel_count,
                                            channels,
                                            delays,
                                            time_coincidence_radius,
                                            time_read,
                                            records->standard);
            break;
        case CLOCKED:
            count = clk_coincidence_collect(&t_buf->buffer,
                                            &t_buf->slice.clocked,
                                            channel_count,
                                            channels,
                                            delays,
                                            time_coincidence_radius,
                                            time_read,
                                            records->clocked);
            break;
    }
    return count;
}

static inline void
tangy_records_copy(buffer_format format,
                   tangy_record_vec* records,
                   tangy_field_ptrs* slice) {

    switch (format) {
        case STANDARD:
            std_records_copy(records->standard, &slice->standard);
            return;

        case CLOCKED:
            clk_records_copy(records->clocked, &slice->clocked);
            return;
    }
}

static inline u64
tangy_timetrace(tangy_buffer* t_buf,
                const u64 start,
                const u64 stop,
                const u64 bin_width,
                const u8* channels,
                const u64 n_channels,
                const u64 length,
                u64* intensities) {

    u64 count = 0;

    switch (t_buf->format) {
        case STANDARD:
            count = std_timetrace(&t_buf->buffer,
                                  &t_buf->slice.standard,
                                  start,
                                  stop,
                                  bin_width,
                                  channels,
                                  n_channels,
                                  length,
                                  intensities);
            break;

        case CLOCKED:
            count = clk_timetrace(&t_buf->buffer,
                                  &t_buf->slice.clocked,
                                  start,
                                  stop,
                                  bin_width,
                                  channels,
                                  n_channels,
                                  length,
                                  intensities);
            break;
    }

    return count;
}

static inline void
tangy_relative_delay(tangy_buffer* t_buf,
                     const u64 start,
                     const u64 stop,
                     const u64 correlation_window,
                     const u64 resolution,
                     const u8 channels_a,
                     const u8 channels_b,
                     const u64 length,
                     u64* intensities) {

    switch (t_buf->format) {
        case STANDARD:
            std_relative_delay(&t_buf->buffer,
                               &t_buf->slice.standard,
                               start,
                               stop,
                               correlation_window,
                               resolution,
                               channels_a,
                               channels_b,
                               length,
                               intensities);
            break;
        case CLOCKED:
            clk_relative_delay(&t_buf->buffer,
                               &t_buf->slice.clocked,
                               start,
                               stop,
                               correlation_window,
                               resolution,
                               channels_a,
                               channels_b,
                               length,
                               intensities);
            break;
    }
}

static inline u64
tangy_joint_delay_histogram(tangy_buffer* t_buf,
                            const u8 clock,
                            const u8 signal,
                            const u8 idler,
                            const u64 n_channels,
                            const u8* channels,
                            const f64* delays,
                            const f64 radius,
                            const f64 read_time,
                            u64* intensities) {
    u64 count = 0;

    switch (t_buf->format) {
        case STANDARD:
            count = std_joint_delay_histogram(&t_buf->buffer,
                                              &t_buf->slice.standard,
                                              clock,
                                              signal,
                                              idler,
                                              n_channels,
                                              channels,
                                              delays,
                                              radius,
                                              read_time,
                                              intensities);
            break;
        case CLOCKED:
            count = clk_joint_delay_histogram(&t_buf->buffer,
                                              &t_buf->slice.clocked,
                                              clock,
                                              signal,
                                              idler,
                                              n_channels,
                                              channels,
                                              delays,
                                              radius,
                                              read_time,
                                              intensities);
            break;
    }

    return count;
}

#endif
