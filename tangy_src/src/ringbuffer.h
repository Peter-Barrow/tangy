#ifndef RBUF_T
#error "No template type 'RBUF_T' supplied for ring buffer"
#endif

#define __RINGBUFFER__

#ifndef RBUF_NAME
#error "No type name 'RBUF_NAME' supplied"
#endif

#include "base.h"

#define RB_STUB RBUF_NAME
#define RINGBUFFER JOIN(ringbuffer, RBUF_T)

#define at(rb, idx) rb->data[idx % (rb->capacity)]
#define oldest_index(rb) (rb->head > rb->capacity) ? (rb->head) % (rb->capacity) : 0
#define oldest_value(rb) at(rb, oldest_index(rb))
#define last_position(rb) (rb->head > rb->capacity) ? (rb->head) - (rb->capacity) : 0
#define next_position(rb) rb->head++

typedef struct RINGBUFFER RINGBUFFER;
struct RINGBUFFER {
    u64 capacity;
    u64 head; // position last written to
    RBUF_T* data;
};

static inline RINGBUFFER* JOIN(RB_STUB, init)(u64 capacity) {
    RINGBUFFER* rb = (RINGBUFFER*)malloc(sizeof(RINGBUFFER));
    if (rb != NULL) {
        rb->head = 0;
        rb->capacity = 0;
        rb->data = NULL;
    }

    RBUF_T* data = (RBUF_T*)malloc(sizeof(RBUF_T) * capacity);
    if (data != NULL) {
        rb->data = data;
        rb->capacity = capacity;
    }

    return rb;
}

static inline void JOIN(RB_STUB, deinit)(RINGBUFFER* rb){
    free(rb->data);
    free(rb);
}

static inline void JOIN(RB_STUB, push)(RINGBUFFER* rb, RBUF_T value) {
    at(rb, rb->head) = value;
    next_position(rb);
}

static inline RBUF_T JOIN(RB_STUB, get)(RINGBUFFER* rb, u64 index) {
    return at(rb, index);
}

#undef RBUF_T
#undef RBUF_NAME
#undef RB_STUB
#undef RINGBUFFER
#undef at
#undef oldest_index
#undef oldest_value
#undef last_position
#undef next_position
#undef __RINGBUFFER__
