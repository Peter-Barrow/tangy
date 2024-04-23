#ifndef __SHARED_MEMORY__
#define __SHARED_MEMORY__

#include "base.h"

#ifdef _WIN32
#include <Windows.h>
// typedef HANDLE fd_t;
#else
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
//typedef int fd_t;
#endif

typedef int fd_t;

typedef struct shared_mapping {
  fd_t file_descriptor;
  const char *name;
  char *data;
} shared_mapping;

/**
 * @brief Creates a new shared memory mapping.
 *
 * @param map_size Size of the mapping.
 * @param map Pointer to a shared_mapping structure for storing mapping
 * information.
 * @return shmemResult Indicating success or failure.
 */
tbResult shmem_create(u64 map_size, shared_mapping *map);

/**
 * @brief Creates a new shared memory mapping.
 *
 * @param map_size Size of the mapping.
 * @param map Pointer to a shared_mapping structure for storing mapping
 * information.
 * @return tbResult Indicating success or failure.
 */
tbResult shmem_connect(shared_mapping *map);

/**
 * @brief Closes a shared memory mapping.
 *
 * @param map Pointer to a shared_mapping structure containing mapping
 * information.
 * @return tbResult Indicating success or failure.
 */
tbResult shmem_close(shared_mapping *map);

/**
 * @brief Checks if a shared memory mapping with a given name exists.
 *
 * @param map_name Name of the mapping.
 * @return tbResult Indicating whether the mapping exists.
 */
tbResult shmem_exists(char *const map_name, bool *exists);

#endif
