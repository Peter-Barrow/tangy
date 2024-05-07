#ifndef __TANGY__
#define __TANGY__

#include "clocked_buffer.h"
#include "standard_buffer.h"

typedef enum { STANDARD, CLOCKED } tangy_buffer_tag;

typedef union {
    const std_buffer* standard;
    const clk_buffer* clocked;
} tangy_buffer_union;

// typedef struct tangy_buffer tangy_buffer;
// struct tangy_buffer {
//     tangy_buffer_tag tag;
//     tangy_buffer_union* value;
// };

typedef u64 (singles_function)(const void* const buffer, const u64 start, const u64 stop, u64* counters);

typedef struct TangyBuffer TangyBuffer;
struct TangyBuffer {
    void* buffer;
    tangy_buffer_tag format;
    // u64 (*singles)(const void* const buffer,
    //                      const u64 start,
    //                      const u64 stop,
    //                      u64* counters);
    singles_function* singles;
};

static inline TangyBuffer
new_buffer(tangy_buffer_tag type, char* name) {

    tbResult result;
    void* buffer;
    TangyBuffer tangy_buffer;
    switch (type) {
        case STANDARD:
            buffer = malloc(sizeof(std_buffer));
            result = std_buffer_init(1024, 10e-9, 8, name, (std_buffer*)buffer);

            tangy_buffer.buffer = buffer;
            tangy_buffer.format = type;
            tangy_buffer.singles = std_void_singles;
            break;
        case CLOCKED:

            buffer = malloc(sizeof(std_buffer));
            result = clk_buffer_init(1024, { 10e-9, 1e-12 }, 8, name, (clk_buffer*)buffer);

            tangy_buffer.buffer = buffer;
            tangy_buffer.format = type;
            tangy_buffer.singles = clk_void_singles;
            break;
    }
    return tangy_buffer;
}

static inline const clk_buffer* into_clocked(void* vbuf){
    return (const clk_buffer*)(vbuf);
}

#endif

// #define _str(s) str(s)
// #define str(s) #s
// 
// static inline int test() {
//     tangy_buffer_tag type = CLOCKED;
//     char name[5] = "new";
//     TangyBuffer buf = new_buffer(type, name);
// 
//     clk_buffer clocked = *into_clocked(buf.buffer);
// 
//     return 0;
// }
