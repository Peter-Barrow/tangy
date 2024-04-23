#ifdef __CLOCKED__
#define __CLOCKED__

#include "base.h"

typedef struct {
    u8 channel;
    u64 clock;
    u64 delta;
} clocked;

typedef double clk_res[2];

typedef struct {
    usize length;
    u8 *channel;
    u64 *clock;
    u64 *delta;
} clk_slice;

#define T clocked
#define RESOLUTION clk_res
#define SLICE clk_slice

#include "ring_buffers.h"

#endif
