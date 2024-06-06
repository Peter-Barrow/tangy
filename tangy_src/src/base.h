#ifndef __BASE__
#define __BASE__

#include <errno.h>
#include <math.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t u8;
typedef int32_t b32;
typedef int32_t i32;
typedef int64_t i64;
typedef uint32_t u32;
typedef uint64_t u64;
typedef float f32;
typedef double f64;
typedef uintptr_t uptr;
// typedef char byte;
typedef unsigned char ubyte;
typedef ptrdiff_t size;
typedef size_t usize;

#define CAT(a, b) a##b
#define PASTE(a, b) CAT(a, b)
#define JOIN(prefix, name) PASTE(prefix, PASTE(_, name))
#define _JOIN(prefix, name) PASTE(_, PASTE(prefix, PASTE(_, name)))

#define STRINGIFY(T) #T
#define TOSTRING(T) STRINGIFY(T)

#define lengthOf(array) (sizeof(array) / sizeof(array[0]));

/** \enum Error cases for creating shared memory
 */
typedef enum {
    NONE,
    SHARED_OPEN,
    TRUNCATE_FAILED,
    MAPPING_FAILED,
    STAT_ERROR,
} tbError;

typedef struct tbResult {
    tbError Error;
    bool Ok;
} tbResult;

typedef struct index_range {
    u64 begin;
    u64 end;
} index_range;

/** @struct iterator
 * @brief simple iterator a contiguous block of memory
 */
typedef struct iterator {
    usize index; /**< current index */
    usize count; /**< number of elements remaining */
} iterator;

typedef enum iterator_state {
    lower,
    upper,
    exhausted,
} iterator_state;

/** @struct circular iterator
 * @brief struct containing a pair of iterators to handle access into a ring
 * buffer
 *
 * @see(iterator, next) This struct provides a mechanism to treat a ring buffer
 * as though it was a contiguous block of memory taking care of the wrap-around
 * case and allowing sequential access by incrementing a cursor rather than
 * needed modulo division for each access
 */
typedef struct circular_iterator {
    // iterator_state state;
    usize count;    /**< Number of elements remaining in iterator */
    iterator lower; /**< Iterator for first side of ring (before wrap-around)
                       @see{iterator} */
    iterator upper; /**< Iterator for second side of ring (after wrap-around)
                       @see{iterator} */
} circular_iterator;

/**
 * @brief next value of iterator for ring buffer
 *
 * Allows accessing items sequentially from a ring buffer without the need to
 * use modulo division (%-operator) to access each position. Decrements the
 * count for relevent iterator field and own count field on each invocation to
 * track the number of elements left to visit.
 *
 * @param[in] iter pointer to circular_iterator struct
 * @return usize next position
 */
static inline usize
next(circular_iterator* iter) {
    if (iter->lower.count > 0) {
        iter->count--;
        iter->lower.count--;
        iter->lower.index++;
        return iter->lower.index;
    }
    if (iter->upper.count > 0) {
        iter->count--;
        iter->upper.count--;
        iter->upper.index++;
        return iter->upper.index - 1;
    }
    return 0;
}

/**
 * @brief Initialise a new iterator for a ring buffer
 *
 * Takes a start and stop position of a ring buffer, these will typicall be
 * greater than the capacity of the ring buffer if it has already been in use.
 * These are then used to determine two points in the underlying array of the
 * ring buffer that need to be incremented from and to by way of modulo division
 * with the ring buffers capacity
 *
 * @param[in, out] iter pointer to circular_iterator
 * @param[in] capacity of ring buffer
 * @param[in] start index of buffer to begin iteration from
 * @param[in] stop point of buffer to terminate at
 * @return [TODO:description]
 */
static inline int
iterator_init(circular_iterator* iter,
              usize capacity,
              usize start,
              usize stop) {

    // start and stop and free running indexes into the buffer, meaning, if they
    // are less than the capacity the capacity has not been met yet. Conversely,
    // if either is greater than the capacity then the capacity has been met and
    // they require modulo division. Iteration is always forward.

    // case 1: start > stop
    //      invalid input, iteration is always forward therefore the statement
    //      start < stop always holds

    if (start >= stop) {
        iter->count = 0;
        return -1;
    }

    u64 count = stop - start; // total iterations to perform

    u64 abs_start = start % capacity;
    u64 abs_stop = stop % capacity;

    // case 2: (abs_start + count) < capacity
    //      our start point and count do not need to wrap-around
    if ((abs_start + count) < capacity) {
        iter->count = count;
        iter->lower.index = abs_start;
        iter->lower.count = count;
        iter->upper.index = 0;
        iter->upper.count = 0;
        return 0;
    }

    // case 3: (abs_start > abs_stop)
    //      wrap-around is required
    u64 distance_to_capacity = capacity - abs_start - 1;
    u64 distance_after_capacity = count - distance_to_capacity;
    if (abs_start >= abs_stop) {
        iter->count = count;
        iter->lower.index = abs_start;
        iter->lower.count = distance_to_capacity;
        iter->upper.index = 0;
        iter->upper.count = distance_after_capacity;
        return 0;
    }

    return -1;
}

// TODO: add arrival_times field
typedef struct {
    u64 length;
    u64 oldest; // not the best name for the result of argmin
    const u8* channels;
    u64* index;
    u64* limit;
    circular_iterator* iters;
} pattern_iterator;

typedef struct cc_measurement cc_measurement;
struct cc_measurement {
    u64 count;
    u64 number_of_channels;
    u8* channels;
    f64* delays;
    void* records;
};

typedef struct delay_histogram_measurement delay_histogram_measurement;
struct delay_histogram_measurement {
    bool ok;
    usize n_channels;
    u8 idx_clock;
    u8 idx_signal;
    u8 idx_idler;
    u8* channels;
};

typedef struct histogram2D_coords histogram2D_coords;
struct histogram2D_coords {
    usize x;
    usize y;
};

static inline char*
buffer_name(char* prefix, char* name) {
    usize len_prefix = strlen(prefix);
    usize len_name = strlen(name);
    usize len_buffer = len_prefix + len_name + 2; // additional "_" and "\0"

    char* buffer = (char*)malloc(sizeof(char) * len_buffer);

    snprintf(buffer, len_buffer, "%s_%s", prefix, name);

    return buffer;
}


#endif

