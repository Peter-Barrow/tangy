#distutils: language = c

from numpy cimport int8_t as byte

from numpy cimport uint8_t as u8
from numpy cimport uint32_t as u32
from numpy cimport uint64_t as u64
from numpy cimport uint64_t as usize
from numpy cimport int64_t as isize

from numpy cimport float64_t as f64

from libc.stdint cimport intptr_t
from libc.stdio cimport FILE

cpdef enum BufferType:
    Standard,
    Clocked

cdef extern from "./src/base.h":
    ctypedef enum tbError:
      NONE,
      SHARED_OPEN,
      TRUNCATE_FAILED,
      MAPPING_FAILED,
      STAT_ERROR

    ctypedef struct tbResult:
        tbError Error
        bint Ok

    ctypedef struct delay_histogram_measurement:
        bint ok
        usize n_channels
        u8 idx_clock
        u8 idx_signal
        u8 idx_idler
        u8* channels

cdef extern from "./src/vector_impls.h":
    ctypedef struct vec_u64:
        isize length
        isize capacity
        u64* data

    vec_u64* vector_u64_init(isize capacity)
    vec_u64* vector_u64_deinit(vec_u64* vector)

cdef extern from "./src/shared_memory.c":
    tbResult shmem_exists(byte *const map_name, bint *exists)

cdef extern from "./src/standard_buffer.h":

    ctypedef int fd_t

    ctypedef f64 std_res

    ctypedef u64 timetag;

    ctypedef struct standard:
        u8 channel
        timetag timestamp

    ctypedef struct std_slice:
        usize length
        u8 *channel
        timetag *timestamp

    ctypedef struct std_buffer:
        byte *map_ptr
        std_slice ptrs
        fd_t file_descriptor
        byte *name
        std_res *resolution
        u64 *capacity
        u64 *count
        u64 *index_of_reference
        u8 *n_channels

    std_buffer* std_buffer_new()

    u64 std_map_size(u64 num_elements)

    u64 std_size_of()

    void std_buffer_info_init(byte *data, std_buffer * buffer)

    standard std_record_at(const std_buffer *const buffer, u64 absolute_index)

    std_slice std_init_base_ptrs(const std_buffer *const buffer)

    # std_slice std_get_slice(const std_buffer *const buffer, const u64 capacity, u64 start, u64 stop)

    tbResult std_buffer_init(const u64 num_elements,
                                  const std_res resolution,
                                  const u8 n_channels,
                                  char *name,
                                  std_buffer * buffer)

    tbResult std_buffer_connect(char *name, std_buffer * buffer)

    tbResult std_buffer_deinit(std_buffer * buffer)

    u64 std_bins_from_time(const std_res resolution, const f64 time)
    f64 std_time_from_bins(const std_res resolution, const u64 bins)

    f64 std_to_time(standard record, std_res resolution)
    u64 std_as_bins(standard record, std_res resolution)

    bint std_compare(standard a, standard b, std_res res_a, std_res res_b)
    bint std_equal(standard a, standard b, std_res res_a, std_res res_b)

    # void std_push(std_buffer * buffer, standard *record)

    usize std_lower_bound(const std_buffer * buffer, usize key)

    usize std_upper_bound(const std_buffer * buffer, usize key)

    f64 std_time_in_buffer(const std_buffer *buffer)

    u64 std_singles(const std_buffer *buffer, const u64 start, const u64 stop, u64 *counters)

    void std_bins_from_time_delays(const std_buffer * buffer, const int length, const f64 *const delays, u64 * bins)

    u64 std_coincidences_count(const std_buffer* const buffer,
                         const usize n_channels,
                         const u8* channels,
                         const f64* delays,
                         const f64 radius,
                         const f64 read_time)

    ctypedef struct vec_timetag:
        isize length
        isize capacity
        u64* data

    ctypedef struct std_cc_measurement:
        std_res resolution
        f64 read_time
        usize total_records
        usize n_channels
        u8* channels
        vec_timetag* records

    std_cc_measurement* std_coincidence_measurement_new(std_res resolution,
                                        usize n_channels,
                                        u8* channels)

    std_cc_measurement* std_coincidence_measurement_delete(std_cc_measurement* measurement)

    usize std_coincidences_records(const std_buffer* const buffer,
                                 const f64* delays,
                                 const f64 radius,
                                 const f64 read_time,
                                 std_cc_measurement* measurement)

    delay_histogram_measurement std_dh_measurement_new(usize n_channels,
                               u8 clock,
                               u8 signal,
                               u8 idler,
                               u8* channels)

    void std_dh_measurement_delete(delay_histogram_measurement* measurement)

    usize std_joint_delay_histogram(const std_buffer* const buffer,
                                     const f64* delays,
                                     const f64 radius,
                                     const f64 read_time,
                                     delay_histogram_measurement* measurement,
                                     u64** histogram)

    u64 std_timetrace(const std_buffer *const buffer,
                      const f64 read_time,
                      const usize bin_width,
                      const u8* channels,
                      const usize n_channels,
                      const usize length,
                      vec_u64 *intensities)

    void std_find_zero_delay(const std_buffer* const buffer,
                             const f64 read_time,
                             const u64 correlation_window,
                             const u64 resolution,
                             const u8 channels_a,
                             const u8 channels_b,
                             const u64 n_bins,
                             u64* intensities)


cdef extern from "./src/clocked_buffer.h":

    ctypedef struct clk_res:
        f64 coarse
        f64 fine

    ctypedef struct  clk_timetag:
        u64 clock
        u64 delta

    ctypedef struct clocked:
        u8 channel
        clk_timetag timestamp

    ctypedef struct clk_slice:
        usize length
        u8 *channel
        clk_timetag *timestamp

    ctypedef struct clk_buffer:
        byte *map_ptr
        clk_slice ptrs
        fd_t file_descriptor
        byte *name
        clk_res *resolution
        u64 *capacity
        u64 *count
        u64 *index_of_reference
        u8 *n_channels

    clk_buffer* clk_buffer_new()

    u64 clk_map_size(u64 num_elements)

    u64 clk_size_of()

    void clk_buffer_info_init(byte *data, clk_buffer * buffer)

    clocked clk_record_at(const clk_buffer *const buffer, u64 absolute_index)
    u8 clk_channel_at(const clk_buffer *const buffer, const u64 absolute_index);
    u64 clk_arrival_time_at(const clk_buffer *const buffer, const u64 absolute_index);

    clk_slice clk_init_base_ptrs(const clk_buffer *const buffer)

    # clk_slice clk_get_slice(const clk_buffer *const buffer, const u64 capacity, u64 start, u64 stop)

    tbResult clk_buffer_init(const u64 num_elements,
                                  const clk_res resolution,
                                  const u8 n_channels,
                                  char *name,
                                  clk_buffer * buffer)

    tbResult clk_buffer_connect(char *name, clk_buffer * buffer)

    tbResult clk_buffer_deinit(clk_buffer * buffer)

    u64 clk_bins_from_time(const clk_res resolution, const f64 time)
    f64 clk_time_from_bins(const clk_res resolution, const u64 bins)

    f64 clk_to_time(clocked record, clk_res resolution)
    u64 clk_as_bins(clocked record, clk_res resolution)

    bint clk_compare(standard a, standard b, clk_res res_a, clk_res res_b)
    bint clk_equal(standard a, standard b, clk_res res_a, clk_res res_b)

    # void clk_push(clk_buffer * buffer, standard *record)

    usize clk_lower_bound(const clk_buffer * buffer, usize key)

    usize clk_upper_bound(const clk_buffer * buffer, usize key)

    f64 clk_time_in_buffer(const clk_buffer *buffer)

    u64 clk_singles(const clk_buffer *buffer, const u64 start, const u64 stop, u64 *counters)

    void clk_bins_from_time_delays(const clk_buffer * buffer, const int length, const f64 *const delays, u64 * bins)

    u64 clk_coincidences_count(const clk_buffer* const buffer,
                         const usize n_channels,
                         const u8* channels,
                         const f64* delays,
                         const f64 radius,
                         const f64 read_time)

    ctypedef struct clk_timetag_slice:
        u64* clock
        u64* delta

    ctypedef struct vec_clk_timetag:
        isize length
        isize capacity
        clk_timetag_slice data

    ctypedef struct clk_cc_measurement:
        clk_res resolution
        f64 read_time
        usize total_records
        usize n_channels
        u8* channels
        vec_clk_timetag* records

    clk_cc_measurement* clk_coincidence_measurement_new(clk_res resolution,
                                        usize n_channels,
                                        u8* channels)

    clk_cc_measurement* clk_coincidence_measurement_delete(clk_cc_measurement* measurement)


    usize clk_coincidences_records(const clk_buffer* const buffer,
                                 const f64* delays,
                                 const f64 radius,
                                 const f64 read_time,
                                 clk_cc_measurement* measurement)

    delay_histogram_measurement clk_dh_measurement_new(usize n_channels,
                               u8 clock,
                               u8 signal,
                               u8 idler,
                               u8* channels)

    void clk_dh_measurement_delete(delay_histogram_measurement* measurement)

    usize clk_joint_delay_histogram(const clk_buffer* const buffer,
                                     const f64* delays,
                                     const f64 radius,
                                     const f64 read_time,
                                     delay_histogram_measurement* measurement,
                                     u64** histogram)

    u64 clk_timetrace(const clk_buffer *const buffer,
                      const f64 read_time,
                      const usize bin_width,
                      const u8* channels,
                      const usize n_channels,
                      const usize length,
                      vec_u64 *intensities)

    void clk_find_zero_delay(const clk_buffer* const buffer,
                             const f64 read_time,
                             const u64 correlation_window,
                             const u64 resolution,
                             const u8 channels_a,
                             const u8 channels_b,
                             const u64 n_bins,
                             u64* intensities)

cdef extern from './src/picoquant_reader.h':

    ctypedef struct READER_STATUS:
        u64 overflow
        u64 total_records
        u64 record_count
        u64 photon_count
        u64 current_count

    u64 get_overflow(const READER_STATUS* const reader_stat)

    u64 get_total_records(const READER_STATUS* const reader_stat)

    u64 get_record_count(const READER_STATUS* const reader_stat)

    u64 get_photon_count(const READER_STATUS* const reader_stat)

    u64 get_current_count(const READER_STATUS* const reader_stat)

    int file_seek(FILE *filehandle, long int offset)

    u64 read_time_HH2_T2(
           const std_buffer* const buffer,
           FILE* filehandle,
           READER_STATUS* reader_stat,
           u64 max_time)

    u64 read_time_HH2_T3(
           const clk_buffer* const buffer,
           FILE* filehandle,
           READER_STATUS* reader_stat,
           u64 max_time)

    u64 read_next_HH2_T2(
           const std_buffer* const buffer,
           FILE* filehandle,
           READER_STATUS* reader_stat,
           u64 n_tags)

    u64 read_next_HH2_T3(
           const clk_buffer* const buffer,
           FILE* filehandle,
           READER_STATUS* reader_stat,
           u64 n_tags)

    READER_STATUS* set_reader_status(u64 num_records)

    void delete_reader_status(const READER_STATUS* const reader_stat)

# cimport numpy as cnp
# 
# cnp.import_array()
# 
# def move_array(length, data):
#     cdef cnp.npy_intp dims[2]
#     dims[0] = 1
#     dims[1] = length
#     cdef object res = cnp.PyArray_SimpleNew(1, dims, cnp.NPY_UINT64, data)
#     return res
