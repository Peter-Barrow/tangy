#include "base.h"
#include "shared_ring_buffer_context.h"
#include "tangy.h"

typedef struct tangy_measurement tangy_measurement;
struct tangy_measurement {
    f64 window;
    f64 read_time;
    u64 start;
    u64 stop;
    tangy_buffer* buffers;
    u8* channels;
    f64* delays;
};
