#ifndef VEC_T
#error "No template type 'VEC_T' supplied for vector"
#endif

#define __VECTOR__
// #ifndef JOIN(VECTOR, VEC_T)
// #define JOIN(VECTOR, VEC_T)

#ifndef VEC_NAME
#error "No type name 'VEC_NAME' supplied"
#endif

#include "base.h"

#define GROWTH_FACTOR 2

// #define VEC_STUB JOIN(vector, VEC_T)
#define VEC_STUB VEC_NAME

#define VECTOR JOIN(vec, VEC_T)

typedef struct VECTOR VECTOR;

/*! \struct vector_VEC_T
 *  \brief Struct for a vector
 */
struct VECTOR {
    size length;   /**< Current total of items pushed */
    size capacity; /**< Current total of elements that the vector can hold */
    VEC_T* data;   /**< Pointer to data */
};

/**
 * @brief Initialise a new of vector
 *
 * @param[in] capacity - the number of elements to store in vector->data
 * @return pointer to a new vector struct
 */
static inline VECTOR*
JOIN(VEC_STUB, init)(size capacity) {

    VECTOR* new_vector = (VECTOR*)malloc(sizeof(VECTOR));
    if (new_vector != NULL) {
        new_vector->length = 0;
        new_vector->capacity = 0;
        new_vector->data = NULL;
    }

    VEC_T* new_data = (VEC_T*)malloc(sizeof(VEC_T) * capacity);
    if (new_data != NULL) {
        new_vector->capacity = capacity;
        new_vector->data = new_data;
    }

    return new_vector;
}

/**
 * @brief Deinitialise a vector
 *
 * @param[in, out] vector pointer to vector struct
 * @return NULL
 */
static inline VECTOR*
JOIN(VEC_STUB, deinit)(VECTOR* vector) {
    free(vector->data);
    free(vector);
    vector = NULL;
    return vector;
}

/**
 * @brief Sets length to one
 *
 * Resets the length of the vector keeping the allocated memory intact
 *
 * @param[in, out] VECTOR pointer
 */
static inline void JOIN(VEC_STUB, reset)(VECTOR* vector) {
    vector->length = 0;
}

/**
 * @brief Grows the length of vector->data to accomodate more elements
 *
 * Increases the capacity of a vector. In the case it fails this returns false
 * and sets the data pointer (vector->data) to NULL.
 *
 * @param[in, out] vector pointer to vector_VEC_T struct
 * @return true on success, false of failure
 */
static inline bool
JOIN(VEC_STUB, grow)(VECTOR* vector) {
    if (vector->data == NULL) {
        return false;
    }

    size new_capacity = vector->capacity * GROWTH_FACTOR;
    size total_bytes = sizeof(VEC_T) * new_capacity;
    VEC_T* new_data = (VEC_T*)realloc(vector->data, total_bytes);

    if (new_data == NULL) {
        return false;
    }

    vector->data = new_data;
    vector->capacity = new_capacity;

    return true;
}
#define vectorGrow(V) JOIN(VEC_STUB, grow)(V)

/**
 * @brief Pushes an element, value, to the head of the vector
 *
 * position beyond the capacity (vector->capacity) of vector->data it will
 * reallocate according to the growth factor
 *
 * @param[in, out] vector pointer to a vector_VEC_T
 * @param[in] value new element for vector of type VEC_T
 */
static inline void
JOIN(VEC_STUB, push)(VECTOR* vector, VEC_T value) {

    if (!((vector->length) <= (vector->capacity - 1))) {
        JOIN(VEC_STUB, grow)(vector);
    }
    vector->data[vector->length] = value;
    vector->length++;
    return;
}


#undef VEC_T
#undef VEC_NAME
#undef GROWTH_FACTOR
#undef VEC_STUB
#undef VECTOR
#undef vectorGrow

// #endif
