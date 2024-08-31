#include "shared_memory.h"
#include <errno.h>
#include <stdio.h>

shmem_map_result
shmem_create(u64 map_size, char* name) {

    shmem_map_result result = { 0 };

#if defined(__linux__) || defined(__unix__) || defined(__APPLE__)

    fd_t fd = shm_open(name, O_RDWR | O_CREAT | O_EXCL, 0777);

    if (-1 == fd) {
        result.Error = MAP_CREATE;
        result.Std_Error = errno;
        return result;
    }

    int ft = ftruncate(fd, map_size);
    if (-1 == ft) {
        result.Error = FTRUNCATE;
        result.Std_Error = errno;
        return result;
    }

    char* ptr = mmap(NULL, map_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

    if (-1 == *ptr) {
        result.Error = MAP;
        result.Std_Error = errno;
        return result;
    }

#elif defined(_WIN32)

    LARGE_INTEGER win_int64;
    win_int64.QuadPart = map_size;

    HANDLE handle = CreateFileMapping(INVALID_HANDLE_VALUE,
                                      NULL,
                                      PAGE_READWRITE,
                                      win_int64.HighPart,
                                      win_int64.LowPart,
                                      name);

    if (INVALID_HANDLE_VALUE == handle) {
        result.Error = MAP_CREATE;
        return result;
    }

    int fd = _open_osfhandle((intptr_t)handle, 0);
    if (-1 == fd) {
        result.Error = HANDLE_TO_FD;
        return result;
    }

    char* ptr =
      MapViewOfFile(handle, FILE_MAP_ALL_ACCESS, 0, 0, win_int64.QuadPart);

    if (-1 == *ptr) {
        result.Error = MEMORY_MAPPING;
        return result;
    }

#else
#error "Unknown platform"

#endif

    result.map.file_descriptor = fd;
    result.map.data = ptr;
    result.map.name = name;
    result.Ok = true;

    return result;
}

// shmemBufferResult shmem_connect(char *map_name, u64 expected_size) {
shmem_map_result
shmem_connect(char* name) {

    shmem_map_result result = { 0 };

#if defined(__linux__) || defined(__unix__) || defined(__APPLE__)

    fd_t fd = shm_open(name, O_RDWR, 0777);

    if (-1 == fd) {
        result.Error = MAP_CREATE;
        result.Std_Error = errno;
        return result;
    }

    struct stat file_status;

    if (-1 == fstat(fd, &file_status)) {
        result.Error = STAT;
        result.Std_Error = errno;
        return result;
    }

    char* ptr = mmap(
      NULL, file_status.st_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

    if (-1 == *ptr) {
        result.Error = MAP;
        result.Std_Error = errno;
        return result;
    }

#elif defined(_WIN32)

    HANDLE handle = OpenFileMapping(FILE_MAP_WRITE, FALSE, name);

    if (INVALID_HANDLE_VALUE == handle) {
        result.Error = MAP_CREATE;
        return result;
    }

    int fd = _open_osfhandle((intptr_t)handle, 0);
    if (-1 == fd) {
        result.Error = HANDLE_TO_FD;
        return result;
    }

    char* ptr = MapViewOfFile(handle, FILE_MAP_WRITE, 0, 0, 0);

    if (-1 == *ptr) {
        result.Error = MEMORY_MAPPING;
        return result;
    }

#else
#error "Unknown platform"

#endif

    result.map.file_descriptor = fd;
    result.map.data = ptr;
    result.map.name = name;
    result.Ok = true;

    return result;
}

// TODO: add error cases
shmem_result
shmem_close(shared_mapping* map) {

    shmem_result result = { 0 };

#if defined(__linux__) || defined(__unix__) || defined(__APPLE__)
    struct stat file_status;
    if (-1 == fstat(map->file_descriptor, &file_status)) {
        result.Error = FSTAT;
        result.Std_Error = errno;
        return result;
    }

    if (-1 == munmap(map->data, file_status.st_size)) {
        result.Error = UNMAP;
        result.Std_Error = errno;
        return result;
    }

    if (-1 == close(map->file_descriptor)) {
        result.Error = FD_CLOSE;
        result.Std_Error = errno;
        return result;
    }

    if (-1 == shm_unlink(map->name)) {
        result.Error = UNLINK;
        result.Std_Error = errno;
        return result;
    }

#elif defined(_WIN32)
    UnmapViewOfFile(map->data);
    // CloseHandle(map->file_descriptor);

    HANDLE handle = (HANDLE)_get_osfhandle(map->file_descriptor);
    if (INVALID_HANDLE_VALUE == handle) {
        result.Error = FD_TO_HANDLE;
        return result;
    }


    CloseHandle(handle);
    close(map->file_descriptor);

#else
#error "Unknown platform"

#endif

    result.Ok = true;
    return result;
}

// TODO: shm_open and close can set errno, handle it!
// tbResult shmem_exists(char *const map_name, bool *exists) {
shmem_result
shmem_exists(char* const map_name, u8* exists) {
    shmem_result result = { 0 };

#if defined(__linux__) || defined(__unix__) || defined(__APPLE__)
    fd_t shm_descriptor = shm_open(map_name, O_RDONLY, 0777);

    if (0 <= shm_descriptor) {
        *exists = 1;
    }

    if (-1 == close(shm_descriptor)) {
        result.Error = FD_CLOSE;
        result.Std_Error = errno;
        result.Ok = false;
        // TODO: need to set an error here, could raise errno
        return result;
    }

#elif defined(_WIN32)

    // int fd = _open_osfhandle((intptr_t)handle, 0);
    HANDLE shm_descriptor = OpenFileMapping(FILE_MAP_WRITE, FALSE, map_name);
    if (!shm_descriptor) {
        return result;
    }

#else
#error "Unknown platform"

#endif

    result.Ok = true;
    return result;
}
