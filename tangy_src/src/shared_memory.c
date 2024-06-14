#include "shared_memory.h"
#include <stdio.h>

tbResult shmem_create(u64 map_size, shared_mapping *map) {

    tbResult result = {0};

#ifdef __linux__

    fd_t fd = shm_open(map->name, O_RDWR | O_CREAT | O_EXCL, 0777);

    if (-1 == fd) {
        result.Error = SHARED_OPEN;
        return result;
    }

    int ft = ftruncate(fd, map_size);
    if (-1 == ft) {
        result.Error = TRUNCATE_FAILED;
        return result;
    }

    char *ptr = mmap(NULL, map_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

    if (-1 == *ptr) {
        result.Error = MAPPING_FAILED;
        return result;
    }

#elif _WIN32

    LARGE_INTEGER win_int64;
    win_int64.QuadPart = map_size;

    // fd_t fd = CreateFileMapping(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE,
    //                        win_int64.HighPart, win_int64.LowPart, mem_map_name);
    // if (-1 == fd) {
    //     result.Error = SHARED_OPEN;
    //     return result;
    // }

    HANDLE handle = CreateFileMapping(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE,
                           win_int64.HighPart, win_int64.LowPart, map->name);

    if (INVALID_HANDLE_VALUE == handle) {
        result.Error = SHARED_OPEN;
        return result;
    }

    int fd = _open_osfhandle((intptr_t)handle, 0);
    if (-1 == fd) {
        result.Error = SHARED_OPEN;
        return result;
    }

    // int ft = ftruncate(fd, map_size);
    // if (-1 == ft) {
    //     result.Error = TRUNCATE_FAILED;
    //     return result;
    // }

    char *ptr =
        MapViewOfFile(handle, FILE_MAP_ALL_ACCESS, 0, 0, win_int64.QuadPart);

    if (-1 == *ptr) {
        result.Error = MAPPING_FAILED;
        return result;
    }

#endif

    map->file_descriptor = fd;
    map->data = ptr;
    result.Ok = true;

    return result;
}

//shmemBufferResult shmem_connect(char *map_name, u64 expected_size) {
tbResult shmem_connect(shared_mapping *map) {

    tbResult result = {0};

#ifdef __linux__

    fd_t fd = shm_open(map->name, O_RDWR, 0777);

    if (-1 == fd) {
        result.Error = SHARED_OPEN;
        return result;
    }

    struct stat file_status;

    if (-1 == fstat(fd, &file_status)) {
        result.Error = STAT_ERROR;
        return result;
    }


    char *ptr = mmap(NULL, file_status.st_size, PROT_READ | PROT_WRITE,
                     MAP_SHARED, fd, 0);

    if (-1 == *ptr) {
        result.Error = MAPPING_FAILED;
        return result;
    }

#elif _WIN32

    // fd_t fd = OpenFileMapping(FILE_MAP_WRITE, FALSE, map->name);

    // if (-1 == fd) {
    //     result.Error = SHARED_OPEN;
    //     return result;
    // }

    HANDLE handle = OpenFileMapping(FILE_MAP_WRITE, FALSE, map->name);

    if (INVALID_HANDLE_VALUE == handle) {
        result.Error = SHARED_OPEN;
        return result;
    }

    int fd = _open_osfhandle((intptr_t)handle, 0);
    if (-1 == fd) {
        result.Error = SHARED_OPEN;
        return result;
    }

    char *ptr = MapViewOfFile(handle, FILE_MAP_WRITE, 0, 0, 0);

    if (-1 == *ptr) {
        result.Error = MAPPING_FAILED;
        return result;
    }

#endif

    map->file_descriptor = fd;
    map->data = ptr;
    result.Ok = true;

    return result;
}

// TODO: add error cases
tbResult shmem_close(shared_mapping *map) {

    tbResult result = {0};

#ifdef __linux__
    struct stat file_status;
    if (-1 == fstat(map->file_descriptor, &file_status)) {
        return result;
    }

    if (-1 == munmap(map->data, file_status.st_size)) {
        return result;
    }

    if (-1 == close(map->file_descriptor)) {
        return result;
    }

    if (-1 == shm_unlink(map->name)) {
        return result;
    }
#elif _WIN32
    UnmapViewOfFile(map->data);
    //CloseHandle(map->file_descriptor);

    HANDLE handle = (HANDLE)_get_osfhandle(map->file_descriptor);
    if (INVALID_HANDLE_VALUE == handle) {
        //TODO: need close error for conversion from file to handle
        return result;
    }

    CloseHandle(handle);
    close(map->file_descriptor);

#endif

    result.Ok = true;
    return result;
}

// TODO: shm_open and close can set errno, handle it!
// tbResult shmem_exists(char *const map_name, bool *exists) {
tbResult shmem_exists(char *const map_name, u8 *exists) {
    tbResult result = {0};

#ifdef __linux__
    fd_t shm_descriptor = shm_open(map_name, O_RDONLY, 0777);

    if (0 <= shm_descriptor) {
        *exists = 1;
    }

    if (-1 == close(shm_descriptor)) {
        result.Ok = false;
        //TODO: need to set an error here, could raise errno
        return result;
    }

#elif _WIN32

    //int fd = _open_osfhandle((intptr_t)handle, 0);
    HANDLE shm_descriptor = OpenFileMapping(FILE_MAP_WRITE, FALSE, map_name);
    if (!shm_descriptor) {
        return result;
    }

#endif

    result.Ok = true;
    return result;
}
