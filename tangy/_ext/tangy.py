import datetime
from numpy import ndarray, asarray, zeros, uint64, uint32, uint8, float64
import cython
from cython.cimports.cython import view
from cython.cimports import tangy as _tangy

import mmap
from os import dup
from os.path import getsize
# import time
from scipy.optimize import curve_fit
from numpy import log2, mean, where, exp, roll, reshape, ravel
from numpy import sum as npsum
from numpy import round as npround
from numpy import abs as nabs
from numpy import histogram as nphist
from numpy import arange, array, ndarray, asarray, zeros, empty, frombuffer
from numpy import uint, uint8, uint64, int64, float64
from cython.cimports.libc.stdlib import malloc, free
from cython.cimports.libc.stdio import FILE, fdopen, fclose, fseek
from cython.cimports.libc.stdint import uint64_t as c_uint64_t
from cython.cimports.libc.stdint import uint32_t as c_uint32_t
import struct
# from cython.cimports.numpy import npuint64_t

import numpy.typing as npt
from typing import List, Tuple, Optional, Union
from enum import Enum


# __all__ = [standard_records, clocked_records, stdbuffer, BufferClocked, PTUFile,
#            singles, coincidences, timetrace, find_zero_delay,
#            coincidence_measurement]


@cython.dataclasses.dataclass(frozen=True)
class RecordsStandard:
    """Container for Standard format Timetags

    Args:
        count (uint64):
        resolution (float):
        channels (ndarray(uint8)):
        timetags (ndarray(uint64)):
    """
    count: uint64 = cython.dataclasses.field()
    resolution: float = cython.dataclasses.field()
    channels: ndarray(uint8) = cython.dataclasses.field()
    timetags: ndarray(uint64) = cython.dataclasses.field()

    @cython.ccall
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def asTime(self):
        resolution: cython.typeof(self.resolution) = self.resolution

        timetag_view: cython.ulonglong[:] = self.timetags

        # count: cython.Py_ssize_t = len(self)
        if 1 == self.count:
            return _tangy.std_time_from_bins(resolution, timetag_view[0])

        result: float64[:] = zeros(self.count, dtype=float64)
        result_view: cython.double[:] = result
        i: cython.Py_ssize_t
        for i in range(self.count):
            result_view[i] = _tangy.std_time_from_bins(resolution,
                                                       timetag_view[i])
        return result

    def __len__(self) -> cython.Py_ssize_t:
        return len(self.channels)


@cython.dataclasses.dataclass(frozen=True)
class RecordsClocked:
    """Container for Standard format Timetags

    Args:
        count (uint64):
        resolution_coarse (float):
        resolution_fine (float):
        channels (ndarray(uint8)):
        clocks (ndarray(uint64)):
        deltas (ndarray(uint64)):
    """
    count: uint64 = cython.dataclasses.field()
    resolution_coarse: float = cython.dataclasses.field()
    resolution_fine: float = cython.dataclasses.field()
    channels: ndarray(uint8) = cython.dataclasses.field()
    clocks: ndarray(uint64) = cython.dataclasses.field()
    deltas: ndarray(uint64) = cython.dataclasses.field()

    @cython.ccall
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def asTime(self):
        record: _tangy.clocked
        resolution: _tangy.clk_res
        resolution.coarse = self.resolution_coarse
        resolution.fine = self.resolution_fine

        clocks_view: cython.ulonglong[:] = self.clocks
        deltas_view: cython.ulonglong[:] = self.deltas

        # count: cython.Py_ssize_t = len(self)
        if 1 == self.count:
            record.timestamp.clock = clocks_view[0]
            record.timestamp.delta = deltas_view[0]
            return _tangy.clk_to_time(record, resolution)

        result: float64[:] = zeros(self.count, dtype=float64)
        result_view: cython.double[:] = result
        i: cython.Py_ssize_t
        for i in range(self.count):
            record.timestamp.clock = clocks_view[i]
            record.timestamp.delta = deltas_view[i]
            result_view[i] = _tangy.clk_to_time(record, resolution)
        return result

    def __len__(self) -> cython.Py_ssize_t:
        return len(self.channels)


Resolution = cython.fused_type(_tangy.std_res, _tangy.clk_res)

Record = cython.fused_type(_tangy.standard, _tangy.clocked)

_Buffer = cython.union(
    standard=_tangy.std_buffer,
    clocked=_tangy.clk_buffer)

_Buffer_Ptr = cython.union(
    standard=cython.pointer(_tangy.std_buffer),
    clocked=cython.pointer(_tangy.clk_buffer))

TangyBuffer = cython.fused_type(_tangy.std_buffer, _tangy.clk_buffer)


@cython.cclass
class TagBuffer:
    """Interface to underlying ring buffer

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (Union[float, Tuple[float, float]]): Resolution \
        of timetags in seconds. A single float for the "standard timetags". A \
        pair of floats for "clocked timetags" with a "coarse" and "fine" \
        timing structure. Unused if connecting. In seconds.
        n_channels (Optional[int]): Number of channels
        length (Optional[int] = 10_000_000): Length of buffer to create. \
        Unused if connecting.

    Attributes:
        name (str): Name of buffer
        file_descriptor (int): File descriptor of underlying ring buffer
        capacity (int): Size of buffer
        resolution (Union[float, Tuple[float, float]]): Single float for \
        a buffer of ``standard timetags`` or a pair of floats for buffers of \
        ``clocked timetags`` (coarse resolution, fine resolution). Resolutions \
        are in seconds.
        count (int): Number of elements that have been written to the buffer
        index_of_reference (int): On/off marker
        n_channels (int): Number of channels the buffer can contain

    Note:
        If connecting to an existing buffer the resolution, n_channels and \
        length arguments will be ignored even if supplied.

    Note:
        For buffers using the clocked timetag format the resolution must be \
        specified as a tuple in the form (coarse resolution, fine resolution).\
        As an example a clock signal from an 80Mhz TiSapphire laser and a fine\
        resolution on-board the time timetagger would give: \
        ``resolution = (12.5e-9, 1e-12)``

    Examples:
        Creation of a TagBuffer object for both the ``Standard`` and \
        ``Clocked`` timetag formats that can hold 1,000,000 timetags for a \
        device with 4 channels. The method to connect to these buffers is also \
        shown. This method of creating new buffers and connecting to existing \
        ones allows the user to hold on to and continously read timetags from \
        a device in one process and then connect to that buffer in another to \
        perform analysis on the current data.
        === "Buffer in ``Standard`` format"
            ```python
            # Here we will create a buffer called 'standard' (imaginitive)
            # that will only except timetags in the ``Standard`` format, this is
            # selected by only supplying a single value for the resolution
            standard_buffer = tangy.TagBuffer("standard", 1e-9, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            standard_buffer_connection = tangy.TagBuffer("standard")
            ```

        === "Buffer in ``Clocked`` format"
            ```python
            # Here we will create a buffer called 'clocked' (imaginitive)
            # that will only except timetags in the ``Clocked`` format, this is
            # selected by supplying a pair of values for the resolution
            resolution = (12.5e-9, 1e-12) # 80Mhz Clock and 1ps fine resolution
            clocked_buffer = tangy.TagBuffer("clocked", resolution, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            clocked_buffer_connection = tangy.TagBuffer("clocked")
            ```
    """

    _type: _tangy.BufferType
    _buffer: _Buffer
    _ptr: _Buffer_Ptr
    _name = cython.declare(bytes)

    def __init__(self, name: str,
                 resolution: Union[float, Tuple[float, float]],
                 length: int = 10_000_000,
                 n_channels: int = 8):

        self._name = name.encode('utf-8')
        c_name: cython.p_char = self._name

        result: _tangy.tbResult

        if type(resolution) is float:
            self._type = _tangy.BufferType.Standard
            result = _tangy.std_buffer_connect(
                c_name, cython.address(self._buffer.standard))
            if True is result.Ok:
                print("connected")
                self._ptr = _Buffer_Ptr(
                    standard=cython.address(self._buffer.standard))
                return

            result = _tangy.std_buffer_init(length, resolution, n_channels, c_name,
                                            cython.address(self._buffer.standard))
            if False is result.Ok:
                # raise an error
                print("buffer creation failed")

            _tangy.std_buffer_info_init(self._buffer.standard.map_ptr,
                                        cython.address(self._buffer.standard))
            self._ptr = _Buffer_Ptr(
                standard=cython.address(self._buffer.standard))
            return

        elif type(resolution) is tuple:
            self._type = _tangy.BufferType.Clocked
            result = _tangy.clk_buffer_connect(
                c_name, cython.address(self._buffer.clocked))
            if True is result.Ok:
                self._ptr = _Buffer_Ptr(
                    clocked=cython.address(self._buffer.clocked))
                print("connected")
                return

            _resolution: _tangy.clk_res
            _resolution.coarse = resolution[0]
            _resolution.fine = resolution[1]

            result = _tangy.clk_buffer_init(length, _resolution, n_channels, c_name,
                                            cython.address(self._buffer.clocked))
            if False is result.Ok:
                # raise an error
                print("buffer creation failed")

            _tangy.clk_buffer_info_init(self._buffer.clocked.map_ptr,
                                        cython.address(self._buffer.clocked))
            self._ptr = _Buffer_Ptr(
                clocked=cython.address(self._buffer.clocked))
            return

    def __del__(self):
        result: _tangy.tbResult
        if self._type is _tangy.BufferType.Standard:
            result = _tangy.std_buffer_deinit(self._ptr.standard)
        elif self._type is _tangy.BufferType.Clocked:
            result = _tangy.clk_buffer_deinit(self._ptr.clocked)
        # TODO: check result...

    def __len__(self):
        return self.capacity

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __getitem__(self, key):
        return self._get(key)

    @cython.ccall
    def _get(self, key):
        size: cython.ulonglong = self.capacity
        count: cython.ulonglong = self.count
        tail: cython.ulonglong
        if size > count:
            tail = 0
        else:
            tail = self.count

        start: cython.ulonglong = 0
        stop: cython.ulonglong = tail
        step: cython.ulonglong = 1

        n: uint64 = 1

        if isinstance(key, slice):
            start = cython.cast(cython.ulonglong, key.start) or 0
            stop = cython.cast(cython.ulonglong, key.stop) or tail
            step = cython.cast(cython.ulonglong, key.step) or 1
            n = stop - start

        if isinstance(key, int):
            if key < 0:
                key += size
            if key < 0 or key >= size:
                raise IndexError("Index out of range")
            tail = self.count
            key = (tail + key) % size
            n = 1

        count: uint64
        channels: uint8[:] = zeros(n, dtype=uint8)
        channels_view: cython.uchar[:] = channels

        if self._type is _tangy.BufferType.Standard:
            ptrs_std: _tangy.std_slice
            ptrs_std.length = n
            ptrs_std.channel = cython.address(channels_view[0])

            timestamps: uint64[:] = zeros(n, dtype=uint64)
            timestamps_view: c_uint64_t[:] = timestamps
            ptrs_std.timestamp = cython.address(timestamps_view[0])

            count = _tangy.std_slice_buffer(self._ptr.standard,
                                            cython.address(ptrs_std),
                                            start, stop)

            return (channels[::step], timestamps[::step])

        elif self._type is _tangy.BufferType.Clocked:
            ptrs_clk: _tangy.clk_field_ptrs
            ptrs_clk.length = n
            ptrs_clk.channels = cython.address(channels_view[0])

            clocks: uint64[:] = zeros(n, dtype=uint64)
            clocks_view: c_uint64_t[:] = clocks
            ptrs_clk.clocks = cython.address(clocks_view[0])

            deltas: uint64[:] = zeros(n, dtype=uint64)
            deltas_view: c_uint64_t[:] = deltas
            ptrs_clk.deltas = cython.address(deltas_view[0])

            count = _tangy.clk_slice_buffer(self._ptr.clocked,
                                            cython.address(ptrs_clk),
                                            start, stop)
            return (channels[::step], clocks[::step], deltas[::step])

    @property
    def name(self):
        if self._type is _tangy.BufferType.Standard:
            return self._buffer.standard.name
        elif self._type is _tangy.BufferType.Clocked:
            return self._buffer.clocked.name

    @property
    def file_descriptor(self):
        if self._type is _tangy.BufferType.Standard:
            return self._buffer.standard.file_descriptor
        elif self._type is _tangy.BufferType.Clocked:
            return self._buffer.clocked.file_descriptor

    @property
    def capacity(self) -> int:
        if self._type is _tangy.BufferType.Standard:
            return self._buffer.standard.capacity[0]
        elif self._type is _tangy.BufferType.Clocked:
            return self._buffer.clocked.capacity[0]

    @property
    def resolution(self) -> Union[float, Tuple[float, float]]:
        if self._type is _tangy.BufferType.Standard:
            return self._buffer.standard.resolution[0]
        elif self._type is _tangy.BufferType.Clocked:
            return (self._buffer.clocked.resolution[0].coarse,
                    self._buffer.clocked.resolution[0].fine)

    @resolution.setter
    def resolution(self, resolution: Union[float, Tuple[float, float]]):
        if self._type is _tangy.BufferType.Standard and \
                type(resolution) is float:
            self._buffer.standard.resolution[0] = resolution
        elif self._type is _tangy.BufferType.Clocked and \
                type(resolution) is tuple:
            _res: _tangy.clk_res
            _res.coarse = resolution[0]
            _res.fine = resolution[1]
            self._buffer.clocked.resolution[0] = _res

    @property
    def count(self) -> int:
        if self._type is _tangy.BufferType.Standard:
            return self._buffer.standard.count[0]
        elif self._type is _tangy.BufferType.Clocked:
            return self._buffer.clocked.count[0]

    @property
    def index_of_reference(self) -> int:
        if self._type is _tangy.BufferType.Standard:
            return self._buffer.standard.index_of_reference[0]
        elif self._type is _tangy.BufferType.Clocked:
            return self._buffer.clocked.index_of_reference[0]

    @property
    def n_channels(self) -> int:
        if self._type is _tangy.BufferType.Standard:
            return self._buffer.standard.n_channels[0]
        elif self._type is _tangy.BufferType.Clocked:
            return self._buffer.clocked.n_channels[0]

    @cython.ccall
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
        if self._type is _tangy.BufferType.Standard:
            return _tangy.std_time_in_buffer(self._ptr.standard)
        elif self._type is _tangy.BufferType.Clocked:
            return _tangy.clk_time_in_buffer(self._ptr.clocked)

    @cython.ccall
    def push(self, channels: ndarray(uint8),
             timetags: Union[ndarray(uint64), Tuple(ndarray(uint64), ndarray(uint64))]):
        print(len(channels))

    @cython.ccall
    def bins_from_time(self, time: float) -> int:
        """ Convert amount of time to a number of time bins

        Args:
            time (float): Amount of time in seconds

        Returns:
            (int): number of bins

        Note:
            For buffers with the clocked timetag format this will be in units\
            of the fine resolution.

        """
        bins: uint64 = 0
        if self._type is _tangy.BufferType.Standard:
            bins = _tangy.std_bins_from_time(
                self._buffer.standard.resolution[0], time)
        elif self._type is _tangy.BufferType.Clocked:
            bins = _tangy.clk_bins_from_time(
                self._buffer.clocked.resolution[0], time)
        return bins

    @cython.ccall
    def lower_bound(self, time: float) -> int:
        """ Find the position in the buffer that gives the last "time" seconds\
        in the buffer

        Performs a binary search on the buffer where the location being \
        searched for is ``buffer.time_in_buffer() - time``.

        Args:
            time (float): Amount of time, in seconds, to split the buffer by

        Returns:
            (int): Index in buffer corresponding to the timetag that is greater\
            than or equal to ``buffer.time_in_buffer() - time``

        """

        bins: uint64 = self.bins_from_time(time)
        index: uint64 = 0

        if self._type is _tangy.BufferType.Standard:
            index = _tangy.std_lower_bound(self._ptr.standard, bins)
        elif self._type is _tangy.BufferType.Clocked:
            index = _tangy.clk_lower_bound(self._ptr.clocked, bins)

        return index


def singles(buffer: TagBuffer, read_time: Optional[float] = None,
            start: Optional[int] = None, stop: Optional[int] = None
            ) -> Tuple[int, List[int]]:
    """Count the occurances of each channel over a region of the buffer

    Args:
        buffer (RecordBuffer): Buffer containing timetags
        read_time (Optional[float] = None): Length of time to integrate over
        start (Optional[int] = None): Buffer position to start counting from
        stop (Optional[int] = None): Buffer position to sotp counting to

    Returns:
        (int, List[int]): Total counts and list of total counts on each channel

    Examples:
        Get all of the singles in a buffer
        >>> tangy.singles(buffer, buffer.time_in_buffer())

        Count the singles in the last 1s
        >>> tangy.singles(buffer, 1)

        Count the singles in the last 1000 tags
        >>> tangy.singles(buffer, buffer.count - 1000, buffer.count)
    """

    counters: uint64[:] = zeros(buffer.n_channels, dtype=uint64)
    counters_view: c_uint64_t[::1] = counters

    if read_time:
        read_time: float64 = read_time
        start: uint64 = buffer.lower_bound(read_time)

    if stop is None:
        stop: uint64 = buffer.count - 1

    total: uint64 = 0

    if buffer._type is _tangy.BufferType.Standard:
        total = _tangy.std_singles(buffer._ptr.standard, start, stop,
                                   cython.address(counters_view[0]))

    elif buffer._type is _tangy.BufferType.Standard:
        total = _tangy.clk_singles(buffer._ptr.clocked, start, stop,
                                   cython.address(counters_view[0]))

    return (total, counters)


@cython.ccall
def timetrace(buffer: TagBuffer, channels: List[int], read_time: float,
              resolution: float = 10):

    n_channels: uint64 = len(channels)
    # channels: uint8[:] = asarray(channels, dtype=uint8)
    channels_view: cython.uchar[::1] = asarray(channels, dtype=uint8)
    channels_ptr: cython.pointer(cython.uchar) = cython.address(
        channels_view[0])

    buffer_resolution: float64 = 0
    if buffer._type is _tangy.BufferType.Standard:
        buffer_resolution = buffer.resolution
    elif buffer._type is _tangy.BufferType.Clocked:
        buffer_resolution = buffer.resolution[1]    # fine resolution

    bin_width: uint64 = round(resolution / buffer_resolution)

    n: cython.int = 1
    if resolution < read_time:
        n = int(read_time // resolution) + 1

    intensity_vec: cython.pointer(_tangy.vec_u64) = _tangy.vector_u64_init(n)

    intensities: uint64[:] = zeros(n, dtype=uint64)
    # intensities = zeros(n, dtype=uint64)
    intensities_view: c_uint64_t[::1] = intensities
    if buffer._type is _tangy.BufferType.Standard:
        total: uint64 = _tangy.std_timetrace(buffer._ptr.standard,
                                             read_time,
                                             bin_width,
                                             channels_ptr,
                                             n_channels,
                                             n,
                                             intensity_vec)
    elif buffer._type is _tangy.BufferType.Clocked:
        total: uint64 = _tangy.clk_timetrace(buffer._ptr.clocked,
                                             read_time,
                                             bin_width,
                                             channels_ptr,
                                             n_channels,
                                             n,
                                             intensity_vec)

    intensities: uint64[:] = zeros(intensity_vec.length, dtype=uint64)
    intensities_view: c_uint64_t[::1] = intensities
    for i in range(intensity_vec.length):
        intensities_view[i] = intensity_vec.data[i]

    intensity_vec = _tangy.vector_u64_deinit(intensity_vec)

    return intensities


def double_decay(time, tau1, tau2, t0, max_intensity):
    tau = where(time < t0, tau1, tau2)
    decay = max_intensity * exp(-nabs(time - t0) / tau)
    return decay


@cython.dataclasses.dataclass(frozen=True)
class zero_delay_result:
    # TODO: add a "central_delay" field
    times: ndarray(float64) = cython.dataclasses.field()
    intensities: ndarray(uint64) = cython.dataclasses.field()
    fit: ndarray(float64) = cython.dataclasses.field()
    tau1: cython.double = cython.dataclasses.field()
    tau2: cython.double = cython.dataclasses.field()
    t0: cython.double = cython.dataclasses.field()
    central_delay: cython.double = cython.dataclasses.field()
    max_intensity: cython.double = cython.dataclasses.field()


@cython.ccall
def find_zero_delay(buffer: TagBuffer, channel_a: int, channel_b: int,
                    read_time: float, resolution: float = 1e-9,
                    window: Optional[float] = None
                    ) -> zero_delay_result:

    trace_res: float64 = 5e-2
    trace: uint64[:] = timetrace(
        buffer, [channel_a, channel_b], read_time, trace_res)

    avrg_intensity = mean(trace) / trace_res

    if window is None:
        correlation_window = 2 / avrg_intensity * 2

    correlation_window = float64(window)

    if resolution is None:
        resolution = (2 / avrg_intensity) / 8000

    res: float64 = 0
    if buffer._type is _tangy.BufferType.Standard:
        res = buffer._buffer.standard.resolution[0]
    elif buffer._type is _tangy.BufferType.Clocked:
        res = buffer._buffer.clocked.resolution[0].fine

    n_bins: uint64 = round(correlation_window / resolution) - 1
    correlation_window = correlation_window / res

    measurement_resolution: uint64 = uint64(
        correlation_window / float64(n_bins))

    correlation_window = n_bins * measurement_resolution
    n_bins = n_bins * 2
    intensities: uint64[:] = zeros(int(n_bins), dtype=uint64)
    intensities_view: c_uint64_t[::1] = intensities

    if buffer._type is _tangy.BufferType.Standard:
        _tangy.std_find_zero_delay(buffer._ptr.standard,
                                   read_time,
                                   uint64(correlation_window),
                                   measurement_resolution,
                                   channel_a,
                                   channel_b,
                                   n_bins,
                                   cython.address(intensities_view[0]))

    elif buffer._type is _tangy.BufferType.Clocked:
        _tangy.clk_find_zero_delay(buffer._ptr.clocked,
                                   read_time,
                                   uint64(correlation_window),
                                   measurement_resolution,
                                   channel_a,
                                   channel_b,
                                   n_bins,
                                   cython.address(intensities_view[0]))

    times = (arange(n_bins) - (n_bins // 2)) * resolution
    max_idx = intensities.argmax()
    # intensities[max_idx] = 0
    # intensities[n_bins // 2] = intensities[(n_bins // 2) - 1]
    t0 = times[intensities.argmax()]

    tau = 2 / avrg_intensity
    max_intensity = intensities.max()

    guess = [tau, tau, t0, max_intensity]

    [opt, cov] = curve_fit(double_decay, times, intensities, p0=guess)
    hist_fit = double_decay(times, *opt)

    central_delay = t0

    if buffer._type is _tangy.BufferType.Clocked:
        index = buffer.lower_bound(buffer.time_in_buffer() - 1)
        channels, clocks, deltas = buffer[index:buffer.count - 1]
        temporal_window = int(buffer.resolution[0] / buffer.resolution[1])
        bins = arange(temporal_window)
        hist_a, edges = nphist(deltas[channels == channel_a], bins)
        central_delay += mean(bins[:-1][hist_a > (0.5 * max(hist_a))]) * (1e-12)

    result = zero_delay_result(
        times=times,
        intensities=intensities,
        fit=hist_fit,
        tau1=opt[0],
        tau2=opt[1],
        t0=opt[2],
        central_delay=central_delay,
        max_intensity=opt[3])

    return result


_Coinc_Measurement = cython.union(
    standard=cython.pointer(_tangy.std_cc_measurement),
    clocked=cython.pointer(_tangy.clk_cc_measurement))


@ cython.cclass
class Coincidences:
    """Coincidence measurement

    Args:
        buffer (TagBuffer) :
        channels (List[int]):
        delays (Optional[List[float]] = None):
    """

    _type: _tangy.BufferType
    _buffer_ptr: _Buffer_Ptr
    _measurement = cython.declare(_Coinc_Measurement)

    _n: uint64

    channels: ndarray(uint8)
    delays: ndarray(float64)

    _channels_view: cython.uchar[:]
    _delays_view: cython.double[:]

    def __init__(self, buffer: TagBuffer, channels: List[int],
                 delays: Optional[List[float]] = None):

        n: uint64 = len(channels)
        self._n = n

        self.channels = asarray(channels, dtype=uint8)
        self.delays = zeros(n, dtype=float64)

        if delays:
            for i in range(n):
                self.delays[i] = delays[i]

        self._channels_view = self.channels
        self._delays_view = self.delays

        channels_ptr = cython.address(self._channels_view[0])

        resolution = buffer.resolution

        if type(resolution) is float:
            self._type = _tangy.BufferType.Standard
            _res_std: _tangy.std_res = resolution
            self._measurement = _Coinc_Measurement(
                standard=_tangy.std_coincidence_measurement_new(
                    _res_std, n, channels_ptr))
            self._buffer_ptr = _Buffer_Ptr(standard=buffer._ptr.standard)

        elif type(resolution) is tuple:
            self._type = _tangy.BufferType.Clocked
            _res_clk: _tangy.clk_res
            _res_clk.coarse = resolution[0]
            _res_clk.fine = resolution[1]
            self._measurement = _Coinc_Measurement(
                clocked=_tangy.clk_coincidence_measurement_new(
                    _res_clk, n, channels_ptr))
            self._buffer_ptr = _Buffer_Ptr(clocked=buffer._ptr.clocked)

        return

    def __del__(self):
        if self._type is _tangy.BufferType.Standard:
            _tangy.std_coincidence_measurement_delete(self._measurement.standard)
        elif self._type is _tangy.BufferType.Clocked:
            _tangy.clk_coincidence_measurement_delete(self._measurement.clocked)
        return

    @ cython.ccall
    def count(self, radius: float, read_time: float) -> int:
        """ Count number of coincidences
        Args:
            raduis (float):
            read_time (float):
        Returns:
            (int): Total coincidences found
        """
        result: uint64 = 0
        if self._type is _tangy.BufferType.Standard:
            result = _tangy.std_coincidences_count(self._buffer_ptr.standard,
                                                   self._n,
                                                   cython.address(self._channels_view[0]),
                                                   cython.address(self._delays_view[0]),
                                                   radius, read_time)
        elif self._type is _tangy.BufferType.Clocked:
            result = _tangy.clk_coincidences_count(self._buffer_ptr.clocked,
                                                   self._n,
                                                   cython.address(self._channels_view[0]),
                                                   cython.address(self._delays_view[0]),
                                                   radius, read_time)
        return result

    @ cython.ccall
    def collect(self, radius: float, read_time: float):
        """ Collect timetags for coincidences

        Returns:
            (Union[RecordsStandard, RecordsClocked]):
        """
        count: uint64 = 0
        total: uint64 = 0

        if self._type is _tangy.BufferType.Standard:
            count = _tangy.std_coincidences_records(
                self._buffer_ptr.standard,
                cython.address(self._delays_view[0]),
                radius,
                read_time,
                self._measurement.standard)

            total = self._measurement.standard.total_records
            records: ndarray(uint64) = zeros(total, dtype=uint64)
            for i in range(total):
                records[i] = self._measurement.standard.records.data[i]

            return RecordsStandard(total, self._measurement.standard.resolution,
                                   asarray(self.channels), records)

        elif self._type is _tangy.BufferType.Clocked:
            count = _tangy.clk_coincidences_records(
                self._buffer_ptr.clocked,
                cython.address(self._delays_view[0]),
                radius,
                read_time,
                self._measurement.clocked)

            total = self._measurement.clocked.total_records

            clocks: ndarray(uint64) = zeros(total, dtype=uint64)
            deltas: ndarray(uint64) = zeros(total, dtype=uint64)
            for i in range(total):
                clocks[i] = self._measurement.clocked.records.data.clock[i]
                deltas[i] = self._measurement.clocked.records.data.delta[i]

            return RecordsClocked(total,
                                  self._measurement.clocked.resolution.coarse,
                                  self._measurement.clocked.resolution.fine,
                                  asarray(self.channels), clocks, deltas)


@ cython.dataclasses.dataclass(frozen=True)
class JointHistogram:
    """JSI result
    """

    data: ndarray(uint64) = cython.dataclasses.field()
    marginal_idler: ndarray(uint64) = cython.dataclasses.field()
    marginal_signal: ndarray(uint64) = cython.dataclasses.field()
    # axis_idler: ndarray(float64) = cython.dataclasses.field()
    # axis_signal: ndarray(float64) = cython.dataclasses.field()


@ cython.cclass
class JointDelayHistogram:
    """Coincidence measurement

    TODO:
        testing

    Args:
        buffer (TagBuffer) :
        channels (List[int]):
        delays (Optional[List[float]] = None):
    """

    _type: _tangy.BufferType
    _buffer_ptr: _Buffer_Ptr
    _measurement = cython.declare(_tangy.delay_histogram_measurement)
    _measurement_ptr = cython.declare(cython.pointer(_tangy.delay_histogram_measurement))
    _radius: float
    _central_bin: int

    _n: uint64

    channels: ndarray(uint8)
    delays: ndarray(float64)

    _channels_view: cython.uchar[:]
    _delays_view: cython.double[:]

    _histogram: ndarray(uint64)
    _temporal_window: int
    _histogram_view: c_uint64_t[:, ::1]
    _histogram_ptrs: cython.pointer(cython.pointer(c_uint64_t))

    def __init__(self, buffer: TagBuffer, channels: List[int], signal: int,
                 idler: int, radius: cython.double, clock: Optional[int] = 0,
                 delays: Optional[List[float]] = None):

        n: uint64 = len(channels)
        self._n = n

        self.channels = asarray(channels, dtype=uint8)
        self.delays = zeros(n, dtype=float64)

        if delays:
            for i in range(n):
                self.delays[i] = delays[i]

        self._channels_view = self.channels
        self._delays_view = self.delays

        self._radius = radius
        radius_bins = buffer.bins_from_time(radius)

        self._temporal_window = radius_bins * 2
        self._central_bin = radius_bins
        # self.histogram = zeros(self._temporal_window * self._temporal_window, dtype=uint32)
        # self._histogram_view = self.histogram

        self._histogram = zeros([self._temporal_window, self._temporal_window],
                                dtype=uint64, order='C')
        self._histogram_view = self._histogram

        channels_ptr = cython.address(self._channels_view[0])

        resolution = buffer.resolution

        if type(resolution) is float:
            self._type = _tangy.BufferType.Standard
            self._measurement = _tangy.std_dh_measurement_new(n, clock, signal, idler, channels_ptr)
            self._measurement_ptr = cython.address(self._measurement)
            self._buffer_ptr = _Buffer_Ptr(standard=buffer._ptr.standard)

        elif type(resolution) is tuple:
            self._type = _tangy.BufferType.Clocked
            self._measurement = _tangy.clk_dh_measurement_new(n, clock, signal, idler, channels_ptr)
            self._measurement_ptr = cython.address(self._measurement)
            self._buffer_ptr = _Buffer_Ptr(clocked=buffer._ptr.clocked)

        return

    def __del__(self):
        # BUG: double free? Invalid pointer either way...
        # if self._type is _tangy.BufferType.Standard:
        #     _tangy.std_dh_measurement_delete(self._measurement_ptr)
        # elif self._type is _tangy.BufferType.Clocked:
        #     _tangy.clk_dh_measurement_delete(self._measurement_ptr)
        # free(self._histogram_ptrs)
        return

    @ cython.ccall
    def histogram(self, bin_width: Optional[int] = 1,
                  centre: bool = False) -> JointHistogram:
        # TODO: add an inplace option, default to false and create new memory
        # on each call

        if bin_width < 1:
            raise ValueError("bin_width must be >= 1")

        temporal_window = self._temporal_window
        central_bin = self._central_bin
        if bin_width != 1:
            temporal_window_scaled = self._temporal_window // bin_width
            temporal_window = temporal_window_scaled
            central_bin = temporal_window // 2

            hist = zeros([temporal_window_scaled, temporal_window_scaled],
                         dtype=uint64)

            i: cython.Py_ssize_t
            i_start: cython.Py_ssize_t
            i_stop: cython.Py_ssize_t
            j: cython.Py_ssize_t
            j_start: cython.Py_ssize_t
            j_stop: cython.Py_ssize_t
            # TODO: should be able to accumulate marginals in this loop
            # PERF: will make this quicker when binning the histogram
            for i in range(temporal_window_scaled):
                i_start = i * bin_width
                i_stop = i_start + bin_width
                for j in range(temporal_window_scaled):
                    j_start = j * bin_width
                    j_stop = j_start + bin_width
                    hist[i][j] = npsum(self._histogram[i_start:i_stop, j_start:j_stop])
        else:
            hist = asarray(self._histogram.copy(), dtype=uint64)

        marginal_idler = npsum(hist, axis=0)
        marginal_signal = npsum(hist, axis=1)

        if centre:
            bins = arange(temporal_window) - central_bin

            offset_idler: int = int(npround(
                mean(bins[marginal_idler > (0.1 * marginal_idler.max())])))
            offset_signal: int = int(npround(
                mean(bins[marginal_signal > (0.1 * marginal_signal.max())])))

            offset_idler *= (-1)
            offset_signal *= (-1)

            return JointHistogram(
                roll(roll(hist, offset_idler, axis=0), offset_signal, axis=1),
                marginal_idler,
                marginal_signal)

        return JointHistogram(hist, marginal_idler, marginal_signal)

    @ cython.ccall
    def collect(self, read_time: float):
        """ Collect timetags for coincidences

        Returns:
            (Union[RecordsStandard, RecordsClocked]):
        """
        count: uint64 = 0
        total: uint64 = 0

        self._histogram_ptrs = cython.cast(
            cython.pointer(cython.pointer(c_uint64_t)),
            malloc(self._temporal_window * cython.sizeof(c_uint64_t)))

        int: cython.Py_ssize_t = 0
        for i in range(self._temporal_window):
            self._histogram_ptrs[i] = cython.address(self._histogram_view[i, 0])

        print("entry point")
        if self._type is _tangy.BufferType.Standard:
            print("making call (std)")
            count = _tangy.std_joint_delay_histogram(
                self._buffer_ptr.standard,
                cython.address(self._delays_view[0]),
                self._radius,
                read_time,
                self._measurement_ptr,
                cython.address(self._histogram_ptrs[0]))
            print("done (std)")

        elif self._type is _tangy.BufferType.Clocked:
            print("making call (clk)")
            count = _tangy.clk_joint_delay_histogram(
                self._buffer_ptr.clocked,
                cython.address(self._delays_view[0]),
                self._radius,
                read_time,
                self._measurement_ptr,
                cython.address(self._histogram_ptrs[0]))
            print("done (clk)")

        # free(self._measurement_ptr)
        print("returning")
        return count


_ptu_header_tag_types = {
    "tyEmpty8": 0xFFFF0008,
    "tyBool8": 0x00000008,
    "tyInt8": 0x10000008,
    "tyBitSet64": 0x11000008,
    "tyColor8": 0x12000008,
    "tyFloat8": 0x20000008,
    "tyTDateTime": 0x21000008,
    "tyFloat8Array": 0x2001FFFF,
    "tyAnsiString": 0x4001FFFF,
    "tyWideString": 0x4002FFFF,
    "tyBinaryBlob": 0xFFFFFFFF,
}
_ptu_header_tag_types_reversed = {v: k
                                  for k, v in _ptu_header_tag_types.items()}
_ptu_record_types = {
    'PicoHarpT3': 66307,
    'PicoHarpT2': 66051,
    'HydraHarpT3': 66308,
    'HydraHarpT2': 66052,
    'HydraHarp2T3': 16843524,
    'HydraHarp2T2': 16843268,
    'TimeHarp260NT3': 66309,
    'TimeHarp260NT2': 66053,
    'TimeHarp260PT3': 66310,
    'TimeHarp260PT2': 66054,
    'MultiHarpNT3': 66311,
    'MultiHarpNT2': 66055,
}
_ptu_record_types_reversed = {v: k for k, v in _ptu_record_types.items()}

_wraparound = {
    "PT2_0": 210698240,
    "PT3_0": 65536,
    "HT2_1": 33552000,
    "HT2_2": 33554432,
    "HT3_1": 1024,
    "HT3_2": 1024,
}

_read_conf = {
    "PicoHarpT3": {
        "isT2": False,
        "version": 0,
        "wraparound": _wraparound["PT3_0"],
    },
    "PicoHarpT2": {
        "isT2": True,
        "version": 0,
        "wraparound": _wraparound["PT2_0"],
    },
    "HydraHarpT3": {
        "isT2": False,
        "version": 1,
        "wraparound": _wraparound["HT3_1"],
    },
    "HydraHarpT2": {
        "isT2": True,
        "version": 1,
        "wraparound": _wraparound["HT2_1"],
    },
    "HydraHarp2T3": {
        "isT2": False,
        "version": 2,
        "wraparound": _wraparound["HT3_2"],
    },
    "HydraHarp2T2": {
        "isT2": True,
        "version": 2,
        "wraparound": _wraparound["HT2_2"],
    },
    "TimeHarp260NT3": {
        "isT2": False,
        "version": 2,
        "wraparound": _wraparound["HT3_2"],
    },
    "TimeHarp260NT2": {
        "isT2": True,
        "version": 2,
        "wraparound": _wraparound["HT2_2"],
    },
    "TimeHarp260PT3": {
        "isT2": False,
        "version": 2,
        "wraparound": _wraparound["HT3_2"],
    },
    "TimeHarp260PT2": {
        "isT2": True,
        "version": 2,
        "wraparound": _wraparound["HT2_2"],
    },
    "MultiHarpNT3": {
        "isT2": False,
        "version": 2,
        "wraparound": _wraparound["HT3_2"],
    },
    "MultiHarpNT2": {
        "isT2": True,
        "version": 2,
        "wraparound": _wraparound["HT2_2"],
    },
}


@ cython.cfunc
def _read_header(data):
    tags: dict = {}
    inc: cython.Py_ssize_t = 8
    offset: cython.Py_ssize_t = 0
    # magic = s[0: offset + inc].decode("utf-8").rstrip("\0")
    # offset += inc
    # if magic != "PQTTTR":
    #     print("ERROR: Magic invalid, this is not a PTU file.")
    #     # this should be a try except block returning a ValueError(?)
    #     # inputfile.close()
    #     # sys.exit(0)
    #     return None
    offset = 8

    version = data[offset: offset + inc].decode("utf-8").rstrip("\0")
    tags["Version"] = version
    offset += inc
    tag_end_offset: cython.Py_ssize_t = data.find("Header_End".encode())

    inc = 48
    while offset < tag_end_offset:
        name, idx, kind, val = struct.unpack("32s i I q",
                                             data[offset: offset + inc])
        offset += inc
        tag_type = _ptu_header_tag_types_reversed[kind]
        # tag = {"idx": idx, "type": tag_type, "value": int(val)}

        if tag_type == "tyInt8":
            value = int64(val)
        elif tag_type == "tyFloat8":
            value = int64(val).view("float64")
        elif tag_type == "tyBool8":
            value = bool(val)
        elif tag_type == "tyTDateTime":
            # ...
            pass
        elif tag_type == "tyAnsiString":
            value = data[offset: offset + val].rstrip(b"\0").decode()
            offset += val
        elif tag_type == "tyFloat8Array":
            value = frombuffer(data, dtype="float", count=val / 8)
            offset += val
        elif tag_type == "tyWideString":
            value = data[offset: offset + val * 2].decode("utf16")
            offset += val
        elif tag_type == "tyBinaryBlob":
            value = data[offset: offset + val]
            offset += val

        tag = {"idx": idx, "type": tag_type, "value": value}
        tag_name = name.strip(b"\0").decode()
        tags[tag_name] = tag

    return tags, offset + 48, tag_end_offset


@ cython.cclass
class PTUFile():
    """Class to read data from Picoquant PTU file and write into buffer.

    Args:
        file_path (str): Path to Picoquant PTU file.
        name (str): Name of buffer to be created (or connected to).
        length (int = 1000):

    Attributes:
        buffer: Buffer being written to
        header (dict): Dictionary containing information found in the file header
        record_count (int): Total number of records processed from PTU file
        count (int): Total number of timetags written into the buffer

    Examples:
        Open a .ptu file and create a new buffer with a name
        >>> ptu = tangy.PTUFile("my_measurement.ptu", "measurement", int(1e8))

        Get the underlying buffer and count the singles from it
        >>> (total, singles) = tangy.singles(ptu.buffer, 1)

    """

    _status = cython.declare(cython.pointer(_tangy.READER_STATUS))
    _c_file_handle = cython.declare(cython.pointer(FILE))
    _file_path: str
    _file_handle: object
    _mem_map: object
    _header: dict

    _tag_end: uint64
    _offset: uint64

    _buffer_type: _tangy.BufferType
    _buffer: TagBuffer

    def __init__(self, file_path: str, name: str, length: int = 1000):

        self._file_path = file_path
        self._file_handle = open(self._file_path, "rb")

        _file_no = self._file_handle.fileno()
        _mem_map = mmap.mmap(_file_no, 0, access=mmap.ACCESS_READ)

        self._header, self._offset, self._tag_end = _read_header(_mem_map)

        _mem_map.close()
        self._file_handle.flush()

        self._c_file_handle = fdopen(dup(_file_no), "rb".encode("ascii"))
        _tangy.file_seek(self._c_file_handle, self._offset)

        num_records_in_file = self._header["TTResult_NumberOfRecords"]["value"]

        if num_records_in_file == 0:
            file_size = getsize(file_path)
            possible_num_records = (
                file_size - self._offset) // 4  # 4 bytes in a u32
            num_records_in_file = int(possible_num_records)

        self._status = _tangy.set_reader_status(num_records_in_file)

        n_ch: int = int(self._header["HW_InpChannels"]["value"])
        glob_res: float64 = self._header["MeasDesc_GlobalResolution"]['value']
        sync_res: float64 = self._header["MeasDesc_Resolution"]['value']

        record_type = self._header["TTResultFormat_TTTRRecType"]["value"]
        key = _ptu_record_types_reversed[record_type].upper()

        if "T2" in key:
            self._buffer_type = _tangy.BufferType.Standard
            self._buffer = TagBuffer(name, sync_res, length, n_ch)
            return

        if "T3" in key:
            self._buffer_type = _tangy.BufferType.Clocked
            self._buffer = TagBuffer(name, (glob_res, sync_res), length, n_ch)
            return

        raise ValueError

    def __del__(self):
        fclose(self._c_file_handle)
        self._file_handle.close()

    # def __repr__(self):
    #     if _tangy.BufferType.Standard == self._buffer_type:
    #         return self._std_buffer.__repr__()
    #     if _tangy.BufferType.Clocked == self._buffer_type:
    #         return self._clk_buffer.__repr__()

    def buffer(self):
        return self._buffer

    @ property
    def record_count(self):
        return self._status.record_count

    @ property
    def header(self):
        return self._header

    # def __getitem__(self, index):
    #     if _tangy.BufferType.Standard == self._buffer_type:
    #         return self._std_buffer[index]

    #     elif _tangy.BufferType.Clocked == self._buffer_type:
    #         return self._clk_buffer[index]

    def __len__(self):
        return len(self._buffer)

    @ property
    def count(self):
        x: uint64 = self._buffer.count
        return x

    # def records(self, index):
    #     if _tangy.BufferType.Standard == self._buffer_type:
    #         (channels, timetags) = self._std_buffer[index]
    #         n = len(channels)
    #         return RecordsStandard(n, self._std_buffer.resolution, channels,
    #                                 timetags)
    #     elif _tangy.BufferType.Clocked == self._buffer_type:
    #         (channels, clocks, deltas) = self._clk_buffer[index]
    #         (coarse, fine) = self._clk_buffer.resolution
    #         n = len(channels)
    #         return RecordsClocked(n, coarse, fine, channels, clocks, deltas)

    def read(self, n: uint64):
        """
        Read an amount of tags from the target file

        :param n: [TODO:description]
        """
        if _tangy.BufferType.Standard == self._buffer_type:
            res: uint64 = _tangy.read_next_HH2_T2(
                self._buffer._ptr.standard, self._c_file_handle,
                self._status, n)

        if _tangy.BufferType.Clocked == self._buffer_type:
            res: uint64 = _tangy.read_next_HH2_T3(
                self._buffer._ptr.clocked, self._c_file_handle,
                self._status, n)

        return res

    # def read_seconds(self, t: float64):
    #     if _tangy.BufferType.Standard == self._buffer_type:
    #         ch_last: uint8
    #         tt_last: uint64
    #         (ch_last, tt_last) = self._std_buffer[-1]

    #         bins: uint64 = _tangy.std_as_bins(
    #             new_standard_record(ch_last, tt_last),
    #             self._std_buffer._resolution())

    #         res: uint64 = _tangy.read_next_HH2_T2(
    #             cython.address(self._std_buffer._buffer), self._c_file_handle,
    #             self._status, bins)

    #     if _tangy.BufferType.Clocked == self._buffer_type:
    #         (ch_last, cl_last, d_last) = self._clk_buffer[-1]

    #         bins: uint64 = _tangy.clk_as_bins(
    #             new_clocked_record(ch_last, cl_last, d_last),
    #             self._clk_buffer._resolution())

    #         res: uint64 = _tangy.read_next_HH2_T3(
    #             cython.address(self._clk_buffer._buffer), self._c_file_handle,
    #             self._status, bins)

    #     return res
