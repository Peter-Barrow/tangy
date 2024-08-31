#ifndef __SHARED_MEMORY__
#define __SHARED_MEMORY__

#include "base.h"
#include <errno.h>

#ifdef _WIN32
#include <Windows.h>
// typedef HANDLE fd_t;
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
// typedef int fd_t;
#endif

typedef int fd_t;

typedef struct shared_mapping shared_mapping;
struct shared_mapping {
    fd_t file_descriptor;
    char* name;
    char* data;
};


typedef enum {
    OK,
    MAP_CREATE,
    HANDLE_TO_FD,
    FD_TO_HANDLE,
    MEMORY_MAPPING,
    FTRUNCATE,
    MAP,
    STAT,
    FSTAT,
    UNMAP,
    FD_CLOSE,
    UNLINK,
} shmem_error;


typedef struct shmem_map_result shmem_map_result;
struct shmem_map_result {
    bool Ok;
    shmem_error Error;
    int Std_Error;
    shared_mapping map;
};

typedef struct shmem_result shmem_result;
struct shmem_result {
    bool Ok;
    shmem_error Error;
    int Std_Error;
};

/**
 * @brief Creates a new shared memory mapping.
 *
 * @param map_size Size of the mapping.
 * @param map Pointer to a shared_mapping structure for storing mapping
 * information.
 * @return shmemResult Indicating success or failure.
 */
shmem_map_result
shmem_create(u64 map_size, char* name);

/**
 * @brief Creates a new shared memory mapping.
 *
 * @param map_size Size of the mapping.
 * @param map Pointer to a shared_mapping structure for storing mapping
 * information.
 * @return tbResult Indicating success or failure.
 */
shmem_map_result
shmem_connect(char* name);

/**
 * @brief Closes a shared memory mapping.
 *
 * @param map Pointer to a shared_mapping structure containing mapping
 * information.
 * @return tbResult Indicating success or failure.
 */
shmem_result
shmem_close(shared_mapping* map);

/**
 * @brief Checks if a shared memory mapping with a given name exists.
 *
 * @param map_name Name of the mapping.
 * @return tbResult Indicating whether the mapping exists.
 */
// tbResult shmem_exists(char *const map_name, bool *exists);
shmem_result
shmem_exists(char* map_name, u8* exists);

#endif
