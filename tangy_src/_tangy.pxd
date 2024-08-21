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
    ctypedef int fd_t
    tbResult shmem_exists(char *const map_name, u8 *exists)

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

    READER_STATUS* set_reader_status(u64 num_records)

    void delete_reader_status(const READER_STATUS* const reader_stat)

    u64 srb_read_next_PH_T2(shared_ring_buffer* buf,
                            std_slice* data,
                            FILE* filehandle,
                            READER_STATUS* status,
                            u64 count_tags)

    u64 srb_read_next_PH_T3(shared_ring_buffer* buf,
                            clk_slice* data,
                            FILE* filehandle,
                            READER_STATUS* status,
                            u64 count_tags)

    u64 srb_read_next_HH2_T2(shared_ring_buffer* buf,
                             std_slice* data,
                             FILE* filehandle,
                             READER_STATUS* status,
                             u64 count_tags)

    u64 srb_read_next_HH2_T3(shared_ring_buffer* buf,
                             clk_slice* data,
                             FILE* filehandle,
                             READER_STATUS* status,
                             u64 count_tags)


cdef extern from "./src/shared_ring_buffer_context.h":

    ctypedef struct shared_ring_buffer:
        char* map_ptr
        u64 length_bytes
        fd_t file_descriptor
        char* name

    ctypedef struct shared_ring_buffer_context:
        f64 resolution
        f64 clock_period
        u64 resolution_bins
        u64 clock_period_bins
        u64 conversion_factor
        u64 capacity
        u64 count
        u64 reference_count
        u64 channel_count

    u64 srb_context_size()
    u64 srb_conversion_factor(f64 resolution, f64 clock_period)

    f64 srb_get_resolution(shared_ring_buffer* buffer)
    void srb_set_resolution(shared_ring_buffer* buffer, f64 resolution)

    f64 srb_get_clock_period(shared_ring_buffer* buffer)
    void srb_set_clock_period(shared_ring_buffer* buffer, f64 clock_period)

    u64 srb_get_resolution_bins(shared_ring_buffer* buffer)
    void srb_set_resolution_bins(shared_ring_buffer* buffer, u64 resolution_bins)

    u64 srb_get_clock_period_bins(shared_ring_buffer* buffer)
    void srb_set_clock_period_bins(shared_ring_buffer* buffer, u64 clock_period_bins)

    u64 srb_get_conversion_factor(shared_ring_buffer* buffer)
    void srb_set_conversion_factor(shared_ring_buffer* buffer, u64 conversion_factor)

    u64 srb_get_capacity(shared_ring_buffer* buffer)
    void srb_set_capacity(shared_ring_buffer* buffer, u64 capacity)

    u64 srb_get_count(shared_ring_buffer* buffer)
    void srb_set_count(shared_ring_buffer* buffer, u64 count)

    u64 srb_get_reference_count(shared_ring_buffer* buffer)
    void srb_set_reference_count(shared_ring_buffer* buffer, u64 reference_count)

    u64 srb_get_channel_count(shared_ring_buffer* buffer)
    void srb_set_channel_count(shared_ring_buffer* buffer, u64 channel_count)

    tbResult srb_init(const u64 length_bytes,
                     char* name,
                     f64 resolution,
                     f64 clock_period,
                     u64 conversion_factor,
                     u64 capacity,
                     u64 count,
                     u64 reference_count,
                     u64 channel_count,
                     shared_ring_buffer* buffer)

    tbResult srb_deinit(shared_ring_buffer* buffer)

    tbResult srb_connect(char* name,
                        shared_ring_buffer* buffer,
                        shared_ring_buffer_context* context)

    void srb_set_context(shared_ring_buffer* buffer,
                        f64 resolution,
                        f64 clock_period,
                        u64 conversion_factor,
                        u64 count,
                        u64 reference_count,
                        u64 channel_count)

    void srb_get_context(shared_ring_buffer* buffer, shared_ring_buffer_context* context)

cdef extern from "./src/analysis_impl_standard.h":

    ctypedef u64 std_timetag

    ctypedef struct std:
        u8 channel
        std_timetag timestamp

    ctypedef f64 std_res

    ctypedef struct std_slice:
        usize length
        u8* channel
        std_timetag* timestamp

    ctypedef struct vec_std_timetag:
        isize length
        isize capacity
        u64* data

cdef extern from "./src/analysis_impl_clocked.h":

    ctypedef struct clk_timetag:
        u64 clock
        u64 delta

    ctypedef struct clk:
        u8 channel
        clk_timetag timestamp

    ctypedef struct clk_res:
        f64 coarse
        f64 fine

    ctypedef struct clk_slice:
        usize length
        u8* channel
        clk_timetag* timestamp

    ctypedef struct clk_field_ptrs:
        usize length
        u8* channels
        u64* clocks
        u64* deltas

    ctypedef struct clk_field_ptrs:
        u64* clock
        u64* delta

    ctypedef struct vec_clk_timetag:
        isize length
        isize capacity
        clk_field_ptrs data


cdef extern from "./src/tangy.h":

    ctypedef enum  buffer_format:
        STANDARD,
        CLOCKED

    ctypedef union tangy_slice:
        std_slice standard
        clk_slice clocked

    ctypedef union tangy_field_ptrs:
        std_slice standard
        clk_field_ptrs clocked

    ctypedef union tangy_record_vec:
        vec_std_timetag standard
        vec_clk_timetag clocked

    ctypedef struct tangy_buffer:
        shared_ring_buffer buffer
        shared_ring_buffer_context context
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

    void tangy_clear_buffer(tangy_buffer* t_buf)

    u64 tangy_buffer_slice(tangy_buffer* t_buf,
                           tangy_field_ptrs* ptrs,
                           u64 start,
                           u64 stop)

    u64 tangy_buffer_push(tangy_buffer* t_buf,
                          tangy_field_ptrs* ptrs,
                          u64 start,
                          u64 stop)

    u64 tangy_oldest_index(tangy_buffer* t_buf)

    f64 tangy_oldest_time(tangy_buffer* t_buf)

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
                                    const u8 clock,
                                    const u8 signal,
                                    const u8 idler,
                                    const u64 n_channels,
                                    const u8* channels,
                                    const f64* delays,
                                    const f64 radius,
                                    const f64 read_time,
                                    u64* intensities)

    void tangy_second_order_coherence(tangy_buffer* t_buf,
                                      const u64 start,
                                      const u64 stop,
                                      const f64 correlation_window,
                                      const f64 resolution,
                                      const u8 signal,
                                      const u8 idler,
                                      const u64 length,
                                      u64* intensities)


    void tangy_second_order_coherence_delays(tangy_buffer* t_buf,
                                             const f64 read_time,
                                             const f64 correlation_window,
                                             const f64 resolution,
                                             const u8 signal,
                                             const u8 idler,
                                             const f64* delays,
                                             const u64 length,
                                             u64* intensities)
