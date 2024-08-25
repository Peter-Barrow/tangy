#ifndef __MEASUREMENT__
#define __MEASUREMENT__

#include "base.h"

typedef enum {
    channels    = 1 << 0,
    delays      = 1 << 1,
    clock       = 1 << 2,
    read_time   = 1 << 3,
    start_index = 1 << 4,
    stop_index  = 1 << 5,
    radius      = 1 << 6,
    resolution  = 1 << 7,
} measurement_flags;

#define FLAGMAX 7

typedef u32 m_flag;

m_flag measurement_set_flag(const m_flag target, const measurement_flags flag);
m_flag measurement_unset_flag(const m_flag target, const measurement_flags flag);
bool measurement_contains_flag(const m_flag target, const measurement_flags flag);

typedef struct measurement measurement;
struct measurement {
    measurement_flags features;
    u64 n_channels;
    u8 *channels;
    f64 *delays;
    u8 clock;
    f64 read_time;
    u64 start_index;
    u64 stop_index;
    f64 radius;
    f64 resolution;
};

void measurement_add_channels(measurement *conf, u64 n_channels, u8 *channels);
void measurement_add_delays(measurement *conf, u64 n_channels, f64 *delays);


#endif
