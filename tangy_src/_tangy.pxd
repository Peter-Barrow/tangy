#distutils: language = c

from numpy cimport int8_t as char

from numpy cimport uint8_t as u8
from numpy cimport uint32_t as u32
from numpy cimport uint64_t as u64
from numpy cimport int64_t as i64
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
    tbResult shmem_exists(char *const map_name, u8 *exists)

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
        char *map_ptr
        std_slice ptrs
        fd_t file_descriptor
        char *name
        std_res *resolution
        u64 *capacity
        u64 *count
        u64 *index_of_reference
        i64 *reference_count
        u8 *n_channels

    std_buffer* std_buffer_new()

    u64 std_map_size(u64 num_elements)

    u64 std_size_of()

    void std_buffer_info_init(char *data, std_buffer * buffer)

    standard std_record_at(const std_buffer *const buffer, u64 absolute_index)

    timetag std_timestamp_at(const std_buffer* const buffer, const u64 absolute_index)

    std_slice std_init_base_ptrs(const std_buffer *const buffer)

    # std_slice std_get_slice(const std_buffer *const buffer, const u64 capacity, u64 start, u64 stop)

    tbResult std_buffer_init(const u64 num_elements,
                                  const std_res resolution,
                                  const u8 n_channels,
                                  char *name,
                                  std_buffer * buffer)

    tbResult std_buffer_connect(char *name, std_buffer * buffer)

    tbResult std_buffer_deinit(std_buffer * buffer)

    usize std_oldest_index(const std_buffer* const buffer)

    u64 std_bins_from_time(const std_res resolution, const f64 time)
    f64 std_time_from_bins(const std_res resolution, const u64 bins)

    f64 std_to_time(standard record, std_res resolution)
    u64 std_as_bins(standard record, std_res resolution)

    usize std_buffer_slice(const std_buffer* const buffer,
                 std_slice* ptrs,
                 usize start,
                 usize stop)

    usize std_buffer_push(std_buffer* const buffer,
                 std_slice ptrs,
                 usize start,
                 usize stop)

    bint std_compare(standard a, standard b, std_res res_a, std_res res_b)
    bint std_equal(standard a, standard b, std_res res_a, std_res res_b)

    # void std_push(std_buffer * buffer, standard *record)

    usize std_lower_bound(const std_buffer * buffer, usize key)

    usize std_upper_bound(const std_buffer * buffer, usize key)

    f64 std_time_in_buffer(const std_buffer *buffer)

    f64 std_current_time(const std_buffer* buffer)

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

    ctypedef struct clk_field_ptrs:
        usize length
        u8* channels
        u64* clocks
        u64* deltas

    ctypedef struct clk_buffer:
        char *map_ptr
        clk_slice ptrs
        fd_t file_descriptor
        char *name
        clk_res *resolution
        u64 *capacity
        u64 *count
        u64 *index_of_reference
        i64 *reference_count
        u8 *n_channels

    clk_buffer* clk_buffer_new()

    u64 clk_map_size(u64 num_elements)

    u64 clk_size_of()

    void clk_buffer_info_init(char *data, clk_buffer * buffer)

    clocked clk_record_at(const clk_buffer *const buffer, u64 absolute_index)
    clk_timetag clk_timestamp_at(const clk_buffer* const buffer, const u64 absolute_index)
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

    usize clk_oldest_index(const clk_buffer* const buffer)

    u64 clk_bins_from_time(const clk_res resolution, const f64 time)
    f64 clk_time_from_bins(const clk_res resolution, const u64 bins)

    f64 clk_to_time(clocked record, clk_res resolution)
    u64 clk_as_bins(clocked record, clk_res resolution)

    usize clk_buffer_slice(const clk_buffer* const buffer,
                 clk_field_ptrs* ptrs,
                 usize start,
                 usize stop)

    usize clk_buffer_push(clk_buffer* const buffer,
                 clk_field_ptrs ptrs,
                 usize start,
                 usize stop)

    bint clk_compare(standard a, standard b, clk_res res_a, clk_res res_b)
    bint clk_equal(standard a, standard b, clk_res res_a, clk_res res_b)

    # void clk_push(clk_buffer * buffer, standard *record)

    usize clk_lower_bound(const clk_buffer * buffer, usize key)

    usize clk_upper_bound(const clk_buffer * buffer, usize key)

    f64 clk_time_in_buffer(const clk_buffer *buffer)

    f64 clk_current_time(const clk_buffer* buffer)

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

    u64 rb_read_next_HH2_T2(ring_buffer* buf,
                            astd_slice* data,
                            FILE* filehandle,
                            READER_STATUS* status,
                            u64 count_tags)

    u64 rb_read_next_HH2_T3(ring_buffer* buf,
                            aclk_slice* data,
                            FILE* filehandle,
                            READER_STATUS* status,
                            u64 count_tags)


# cdef class TangyBufferStandard:
#     cdef std_buffer _buffer
#     cdef std_buffer* _ptr
#     cdef BufferType _type
#     cdef bint _have_measurement
#     cdef std_cc_measurement* _measurement_cc

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

cdef extern from "./src/ring_buffer_context.h":

    ctypedef struct ring_buffer:
        char* map_ptr
        u64 length_bytes
        fd_t file_descriptor
        char* name

    ctypedef struct ring_buffer_context:
        f64 resolution
        f64 clock_period
        u64 resolution_bins
        u64 clock_period_bins
        u64 conversion_factor
        u64 capacity
        u64 count
        u64 reference_count
        u64 channel_count

    u64 rb_context_size()
    u64 rb_conversion_factor(f64 resolution, f64 clock_period)

    f64 rb_get_resolution(ring_buffer* buffer)
    void rb_set_resolution(ring_buffer* buffer, f64 resolution)

    f64 rb_get_clock_period(ring_buffer* buffer)
    void rb_set_clock_period(ring_buffer* buffer, f64 clock_period)

    u64 rb_get_resolution_bins(ring_buffer* buffer)
    void rb_set_resolution_bins(ring_buffer* buffer, u64 resolution_bins)

    u64 rb_get_clock_period_bins(ring_buffer* buffer)
    void rb_set_clock_period_bins(ring_buffer* buffer, u64 clock_period_bins)

    u64 rb_get_conversion_factor(ring_buffer* buffer)
    void rb_set_conversion_factor(ring_buffer* buffer, u64 conversion_factor)

    u64 rb_get_capacity(ring_buffer* buffer)
    void rb_set_capacity(ring_buffer* buffer, u64 capacity)

    u64 rb_get_count(ring_buffer* buffer)
    void rb_set_count(ring_buffer* buffer, u64 count)

    u64 rb_get_reference_count(ring_buffer* buffer)
    void rb_set_reference_count(ring_buffer* buffer, u64 reference_count)

    u64 rb_get_channel_count(ring_buffer* buffer)
    void rb_set_channel_count(ring_buffer* buffer, u64 channel_count)

    tbResult rb_init(const u64 length_bytes,
                     char* name,
                     f64 resolution,
                     f64 clock_period,
                     u64 conversion_factor,
                     u64 capacity,
                     u64 count,
                     u64 reference_count,
                     u64 channel_count,
                     ring_buffer* buffer)

    tbResult rb_deinit(ring_buffer* buffer)

    tbResult rb_connect(char* name,
                        ring_buffer* buffer,
                        ring_buffer_context* context)

    void rb_set_context(ring_buffer* buffer,
                        f64 resolution,
                        f64 clock_period,
                        u64 conversion_factor,
                        u64 count,
                        u64 reference_count,
                        u64 channel_count)

    void rb_get_context(ring_buffer* buffer, ring_buffer_context* context)

cdef extern from "./src/analysis_impl_standard.h":

    ctypedef u64 astd_timetag

    ctypedef struct astd:
        u8 channel
        astd_timetag timestamp

    ctypedef f64 astd_res

    ctypedef struct astd_slice:
        usize length
        u8* channel
        astd_timetag* timestamp

    ctypedef struct vec_astd_timetag:
        isize length
        isize capacity
        u64* data

    # tt_vector_init(C) astd_vec_init(C)
    # tt_vector_deinit(C) astd_vec_deinit(C)
    # tt_vector_push(V_PTR, E) astd_vec_push(V_PTR, E)
    # tt_vector_reset(V_PTR) astd_vec_reset(V_PTR)


cdef extern from "./src/analysis_impl_clocked.h":

    ctypedef struct aclk_timetag:
        u64 clock
        u64 delta

    ctypedef struct clk:
        u8 channel
        aclk_timetag timestamp

    ctypedef struct aclk_res:
        f64 coarse
        f64 fine

    ctypedef struct aclk_slice:
        usize length
        u8* channel
        aclk_timetag* timestamp

    ctypedef struct aclk_field_ptrs:
        usize length
        u8* channels
        u64* clocks
        u64* deltas

    ctypedef struct aclk_field_ptrs:
        u64* clock
        u64* delta

    ctypedef struct vec_aclk_timetag:
        isize length
        isize capacity
        aclk_field_ptrs data


cdef extern from "./src/tangy.h":

    ctypedef enum  buffer_format:
        STANDARD,
        CLOCKED

    ctypedef union tangy_slice:
        astd_slice standard
        aclk_slice clocked

    ctypedef union tangy_field_ptrs:
        astd_slice standard
        aclk_field_ptrs clocked

    ctypedef union tangy_record_vec:
        vec_astd_timetag standard
        vec_aclk_timetag clocked

    ctypedef struct tangy_buffer:
        ring_buffer buffer
        ring_buffer_context context
        tangy_slice slice
        tangy_record_vec records
        buffer_format format

    tbResult tangy_buffer_init(buffer_format format,
                      char* name,
                      const u64 capacity,
                      f64 resolution,
                      f64 clock_period,
                      u64 channel_count,
                      tangy_buffer* t_buffer)

    tbResult tangy_buffer_deinit(tangy_buffer* t_buf)

    tbResult tangy_buffer_connect(char* name, tangy_buffer* t_buf)

    u64 tangy_bins_from_time(tangy_buffer* t_buf, f64 time)

    u64 tangy_buffer_slice(tangy_buffer* t_buf,
                           tangy_field_ptrs* ptrs,
                           u64 start,
                           u64 stop)

    u64 tangy_buffer_push(tangy_buffer* t_buf,
                          tangy_field_ptrs* ptrs,
                          u64 start,
                          u64 stop)

    u64 tangy_oldest_index(tangy_buffer* t_buf)

    f64 tangy_current_time(tangy_buffer* t_buf)

    f64 tangy_time_in_buffer(tangy_buffer* t_buf)

    u64 tangy_lower_bound(tangy_buffer* t_buf, u64 key)

    u64 tangy_singles(tangy_buffer* t_buf, u64 start, u64 stop, u64* counters)

    u64 tangy_coincidence_count(tangy_buffer* t_buf,
                                u64 channel_count,
                                u8* channels,
                                f64* delays,
                                f64 time_coincidence_radius,
                                f64 time_read)

    u64 tangy_coincidence_collect(tangy_buffer* t_buf,
                                  u64 channel_count,
                                  u8* channels,
                                  f64* delays,
                                  f64 time_coincidence_radius,
                                  f64 time_read,
                                  tangy_record_vec* records)

    void tangy_records_copy(buffer_format format,
                            tangy_record_vec* records,
                            tangy_field_ptrs* slice)

    u64 tangy_timetrace(tangy_buffer* t_buf,
                        const u64 start,
                        const u64 stop,
                        const u64 bin_width,
                        const u8* channels,
                        const u64 n_channels,
                        const u64 length,
                        u64* intensities)

    void tangy_relative_delay(tangy_buffer* t_buf,
                              const u64 start,
                              const u64 stop,
                              const u64 correlation_window,
                              const u64 resolution,
                              const u8 channels_a,
                              const u8 channels_b,
                              const u64 length,
                              u64* intensities)

    u64 tangy_joint_delay_histogram(tangy_buffer* t_buf,
                                    u8 clock,
                                    u8 signal,
                                    u8 idler,
                                    u64 n_channels,
                                    u8* channels,
                                    f64* delays,
                                    f64 radius,
                                    f64 read_time,
                                    u64* intensities)
