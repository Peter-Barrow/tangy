#ifndef VEC_T
#error "No template type 'VEC_T' supplied for vector"
#endif

#ifndef VEC_T_PTRS
#error "No template type 'VEC_T_PTRS' supplied for vector"
#endif

#define __MULTI_VECTOR__

#ifndef VEC_NAME
#error "No type name 'VEC_NAME' supplied"
#endif

#include "base.h"

#define GROWTH_FACTOR 2

// #define VEC_STUB JOIN(vector, VEC_T)
#define VEC_STUB VEC_NAME

#define MULTI_VECTOR JOIN(vec, VEC_T)

typedef struct MULTI_VECTOR MULTI_VECTOR;

/*! \struct vector_VEC_T
 *  \brief Struct for a vector
 */
struct MULTI_VECTOR {
    size length;     /**< Current total of items pushed */
    size capacity;   /**< Current total of elements that the vector can hold */
    VEC_T_PTRS data; /**< Struct of pointers to data */
};

/**
 * @brief Initialise a new multivector
 *
 * @param[in] capacity - the number of elements to store in vector->data
 * @return pointer to a new vector struct
 */
MULTI_VECTOR* JOIN(VEC_STUB, init)(size capacity);


/**
 * @brief Deinitialise a vector
 *
 * @param[in, out] vector pointer to vector struct
 * @return NULL
 */
MULTI_VECTOR* JOIN(VEC_STUB, deinit)(MULTI_VECTOR* multivec);

/**
 * @brief Sets length to one
 *
 * Resets the length of the vector keeping the allocated memory intact
 *
 * @param[in, out] multivec pointer
 */
void JOIN(VEC_STUB, reset)(MULTI_VECTOR* multivec);

/**
 * @brief Grows the length of vector->data to accomodate more elements
 *
 * Increases the capacity of a vector. In the case it fails this returns false
 * and sets the data pointer (vector->data) to NULL.
 *
 * @param[in, out] vector pointer to vector_VEC_T struct
 * @return true on success, false of failure
 */
bool JOIN(VEC_STUB, grow)(MULTI_VECTOR* multivec);


/**
 * @brief Pushes an element, value, to the head of the vector
 *
 * position beyond the capacity (vector->capacity) of vector->data it will
 * reallocate according to the growth factor
 *
 * @param[in, out] vector pointer to a vector_VEC_T
 * @param[in] value new element for vector of type VEC_T
 */
void JOIN(VEC_STUB, push)(MULTI_VECTOR* multivec, VEC_T value);

#undef VEC_T
#undef VEC_NAME
#undef GROWTH_FACTOR
#undef VEC_STUB
#undef VECTOR
#undef vectorGrow

// #endif
