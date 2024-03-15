import datetime
from numpy import ndarray, asarray, zeros, uint64, uint8, float64
import cython
from cython.cimports.cython import view
from cython.cimports import tangy as _tangy

import mmap
from os import dup
from os.path import getsize
import time
from scipy.optimize import curve_fit
from numpy import log2, mean, where, exp
from numpy import abs as nabs
from numpy import arange, array, ndarray, asarray, zeros, empty, frombuffer
from numpy import uint, uint8, uint64, int64, float64
from cython.cimports.libc.stdio import FILE, fdopen, fclose, fseek
from cython.cimports.libc.stdint import uint64_t as c_uint64_t
import struct
# from cython.cimports.numpy import npuint64_t

import numpy.typing as npt
from typing import List, Tuple, Optional, Union
from enum import Enum


# __all__ = [standard_records, clocked_records, stdbuffer, BufferClocked, PTUFile,
#            singles, coincidences, timetrace, find_zero_delay,
#            coincidence_measurement]


@cython.dataclasses.dataclass(frozen=True)
class standard_records:
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
class clocked_records:
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


@cython.cclass
class BufferStandard:
    """Interface to underlying ring buffer

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (Optional[Union[float, Tuple[float, float]]]): Resolution \
        of timetags in seconds. A single float for the "standard timetags". A \
        pair of floats for "clocked timetags" with a "coarse" and "fine" \
        timing structure. Unused if connecting.
        n_channels (int): Number of channels
        length (Optional[int] = 1000): Length of buffer to create. Unused if \
        connecting.

    Examples:
        Creating a new buffer can be done like so:
        >>> my_buffer = tangy.buffer("my_buffer", 1e-9, 4, int(1e6))

        Buffers can also be connected to since they are backed by shared \
        memory they can be created in one python instance that is for example \
        reading from a timetagger and then connected to in another instance to\
        analyse the timetags in that buffer without interfering with the \
        device connection.
        >>> my_connected_buffer = tangy.buffer("my_buffer")
    """


    _buffer = cython.declare(_tangy.std_buffer)
    _name = cython.declare(bytes)

    def __init__(self, name: str, length: int = 1000, resolution: float = 1e-9,
                 n_channels: int = 8):

        self._name = name.encode('utf-8')
        c_name: cython.p_char = self._name

        result: _tangy.tbResult
        result = _tangy.std_buffer_connect(
            c_name, cython.address(self._buffer))
        if True is result.Ok:
            print("connected")
            return

        result = _tangy.std_buffer_init(length, resolution, n_channels, c_name,
                                        cython.address(self._buffer))
        if False is result.Ok:
            # raise an error
            print("buffer creation failed")

        _tangy.std_buffer_info_init(self._buffer.map_ptr,
                                    cython.address(self._buffer))
        return

    def __del__(self):
        result: _tangy.tbResult = _tangy.std_buffer_deinit(
            cython.address(self._buffer))

    def __repr__(self):
        out_str = """Details:
    Name:            %s
    File Descriptor: %d
    Capacity:        %d
    Resolution:      %.2g
    Count:           %d
    Reference Index: %d
    #-channels:      %d""" % (
            self._buffer.name,
            self._buffer.file_descriptor,
            self._buffer.capacity[0],
            self._buffer.resolution[0],
            self._buffer.count[0],
            self._buffer.index_of_reference[0],
            self._buffer.n_channels[0])

        return out_str

    def __len__(self):
        return self.capacity

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __getitem__(self, key):
        return self._get(key)

    @cython.ccall
    def _get(self, key):
        size: int = self._buffer.capacity[0]
        count: int = self._buffer.count[0]
        tail: int
        if size > count:
            tail = 0
        else:
            tail = self._buffer.count[0]

        if isinstance(key, slice):
            start: int = key.start or 0
            stop: int = key.stop or tail
            step: int = key.step or 1

            indices = zeros(abs(stop) - abs(start), dtype=int)
            if step == -1:
                indices = asarray([i % size for i in range(
                    stop - 1, start, step)], dtype=int)
            else:
                indices = asarray(
                    [i % size for i in range(start, stop, step)], dtype=int)

            indices = indices % len(self)
            channels = zeros(len(indices), dtype=uint8)
            timetags = zeros(len(indices), dtype=uint64)

            for i, j in enumerate(indices):
                channels[i] = self._buffer.ptrs.channel[j]
                timetags[i] = self._buffer.ptrs.timestamp[j]
            return (channels, timetags)

        if key < 0:
            key += size
        if key < 0 or key >= size:
            raise IndexError("Index out of range")
        channel = zeros(1, dtype=uint8)
        timetag = zeros(1, dtype=uint64)
        tail = self._buffer.count[0]
        key = (tail + key) % size
        channel[0] = self._buffer.ptrs.channel[key]
        timetag[0] = self._buffer.ptrs.timestamp[key]
        return (channel, timetag)

    # def Slice(self, key):
    #     (channels, timetags) = self[key]
    #     return standard_records(self.resolution, len(channels),
    #                             channels, timetags)

    def records(self, index):
        (channels, timestamps) = self[index]
        (coarse, fine) = self.resolution
        n = len(channels)
        return standard_records(n, self.resolution, channels, timestamps)

    def Push(self, channels: uint8[:], timetags: uint64[:]):
        # writes tags to the buffer
        print(len(channels))

    @property
    def name(self):
        return self._buffer.name

    @property
    def file_descriptor(self):
        return self._buffer.file_descriptor

    @property
    def capacity(self):
        return self._buffer.capacity[0]

    @cython.cfunc
    def _resolution(self):
        return self._buffer.resolution[0]

    @property
    def resolution(self):
        return self._buffer.resolution[0]

    @resolution.setter
    def resolution(self, resolution):
        if resolution is None:
            return
        self._buffer.resolution[0] = resolution
        return

    @property
    def count(self):
        return self._buffer.count[0]

    @property
    def index_of_reference(self):
        return self._buffer.index_of_reference[0]

    @property
    def n_channels(self):
        return self._buffer.n_channels[0]

    @n_channels.setter
    def n_channels(self, n_channels):
        if n_channels is None:
            return
        self._buffer.n_channels[0] = n_channels
        return

    def lower_bound(self, time: cython.double) -> cython.int:
        index: cython.int = _tangy.std_lower_bound(
            cython.address(self._buffer),
            _tangy.std_bins_from_time(self._buffer.resolution[0], time))
        return index

    def upper_bound(self, time: cython.double) -> cython.int:
        index: cython.int = _tangy.std_upper_bound(
            cython.address(self._buffer),
            _tangy.std_bins_from_time(self._buffer.resolution[0], time))
        return index

    @cython.ccall
    def time_in_buffer(self) -> cython.double:
        return _tangy.std_time_in_buffer(cython.address(self._buffer))


@cython.cclass
class BufferClocked:
    """Interface to underlying ring buffer

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (Optional[Union[float, Tuple[float, float]]]): Resolution \
        of timetags in seconds. A single float for the "standard timetags". A \
        pair of floats for "clocked timetags" with a "coarse" and "fine" \
        timing structure. Unused if connecting.
        n_channels (int): Number of channels
        length (Optional[int] = 1000): Length of buffer to create. Unused if \
        connecting.

    Examples:
        Creating a new buffer can be done like so:
        >>> my_buffer = tangy.buffer("my_buffer", 1e-9, 4, int(1e6))

        Buffers can also be connected to since they are backed by shared \
        memory they can be created in one python instance that is for example \
        reading from a timetagger and then connected to in another instance to\
        analyse the timetags in that buffer without interfering with the \
        device connection.
        >>> my_connected_buffer = tangy.buffer("my_buffer")
    """

    _buffer = cython.declare(_tangy.clk_buffer)
    _name = cython.declare(bytes)

    def __init__(self, name: str, length: cython.int = 1000,
                 resolution_coarse: float64 = 1e-9,
                 resolution_fine: float64 = 1e-12,
                 n_channels: int = 8):

        self._name = name.encode('utf-8')
        c_name: cython.p_char = self._name

        result: _tangy.tbResult
        result = _tangy.clk_buffer_connect(c_name,
                                           cython.address(self._buffer))
        if True is result.Ok:
            print("found a buffer and connected")
            return

        _resolution: _tangy.clk_res
        _resolution.coarse = resolution_coarse
        _resolution.fine = resolution_fine
        result = _tangy.clk_buffer_init(length, _resolution, n_channels,
                                        c_name, cython.address(self._buffer))
        if False is result.Ok:
            # raise an error
            print("buffer creation failed")

        _tangy.clk_buffer_info_init(self._buffer.map_ptr,
                                    cython.address(self._buffer))
        return

    def __del__(self):
        result: _tangy.tbResult = _tangy.clk_buffer_deinit(
            cython.address(self._buffer))

    def __repr__(self):
        out_str = """Details:
    Name:            %s
    File Descriptor: %d
    Capacity:        %d
    Resolution:
        Coarse:      %.2g
        Fine:        %.2g
    Count:           %d
    Reference Index: %d
    #-channels:      %d""" % (
            self._buffer.name,
            self._buffer.file_descriptor,
            self._buffer.capacity[0],
            self._buffer.resolution[0].coarse,
            self._buffer.resolution[0].fine,
            self._buffer.count[0],
            self._buffer.index_of_reference[0],
            self._buffer.n_channels[0])

        return out_str

    def __len__(self):
        return self.capacity

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __getitem__(self, key):
        return self._get(key)

    @cython.cfunc
    def _get(self, key):
        size: int = self._buffer.capacity[0]
        count: int = self._buffer.count[0]
        tail: int = count

        if isinstance(key, slice):
            start: int = key.start or 0
            stop: int = key.stop or tail
            step: int = key.step or 1

            # indices: [:, :, ::1] int
            indices = zeros(abs(stop) - abs(start), dtype=int)
            if step == -1:
                indices = asarray([i % size for i in range(
                    stop - 1, start, step)], dtype=int)
            else:
                indices = asarray(
                    [i % size for i in range(start, stop, step)], dtype=int)

            indices = (indices) % len(self)
            channels = zeros(len(indices), dtype=uint8)
            clocks = zeros(len(indices), dtype=uint64)
            deltas = zeros(len(indices), dtype=uint64)

            timetag: _tangy.clk_timetag
            for i, j in enumerate(indices):
                channels[i] = self._buffer.ptrs.channel[j]
                # timetag = _tangy.clk_arrival_time_at(self._buffer, j)
                timetag = self._buffer.ptrs.timestamp[j]
                clocks[i] = timetag.clock
                deltas[i] = timetag.delta
            return (channels, clocks, deltas)

        if key < 0:
            # key += size
            key += count
        if key < 0 or key >= size:
            raise IndexError("Index out of range")
        channel = zeros(1, dtype=uint8)
        clock = zeros(1, dtype=uint64)
        delta = zeros(1, dtype=uint64)
        # tail = self._buffer.count[0]
        # key = (tail + key) % size
        key = key % size
        channel[0] = self._buffer.ptrs.channel[key]
        clock[0] = self._buffer.ptrs.timestamp[key].clock
        delta[0] = self._buffer.ptrs.timestamp[key].delta
        return (channel, clock, delta)

    # # TODO: add a fused type for int or slice
    # def Slice(self, key):
    #     (channels, clocks, deltas) = self[key]
    #     return clocked_records(self.resolution, len(channels),
    #                            channels, clocks, deltas)

    def records(self, index):
        (channels, clocks, deltas) = self[index]
        (coarse, fine) = self.resolution
        n = len(channels)
        return clocked_records(n, coarse, fine, channels, clocks, deltas)

    @property
    def name(self):
        return self._buffer.name

    @property
    def file_descriptor(self):
        return self._buffer.file_descriptor

    @property
    def capacity(self):
        return self._buffer.capacity[0]

    @cython.cfunc
    def _resolution(self):
        res: _tangy.clk_res
        res.coarse = self._buffer.resolution[0].coarse
        res.fine = self._buffer.resolution[0].fine
        return res

    @property
    def resolution(self):
        return (self._buffer.resolution[0].coarse,
                self._buffer.resolution[0].fine)

    @resolution.setter
    def resolution(self, resolution: tuple(float, float)):
        if resolution is None:
            return

        _resolution: _tangy.clk_res
        _resolution.coarse = resolution(0)
        _resolution.fine = resolution(1)
        self._buffer.resolution[0] = _resolution
        return

    @property
    def count(self):
        return self._buffer.count[0]

    @property
    def index_of_reference(self):
        return self._buffer.index_of_reference[0]

    @property
    def n_channels(self):
        return self._buffer.n_channels[0]

    @n_channels.setter
    def n_channels(self, n_channels):
        if n_channels is None:
            return
        self._buffer.n_channels[0] = n_channels
        return

    @cython.ccall
    def lower_bound(self, time: cython.double) -> cython.int:
        index: cython.int = _tangy.clk_lower_bound(
            cython.address(self._buffer),
            _tangy.clk_bins_from_time(self._buffer.resolution[0], time))
        return index

    @cython.ccall
    def upper_bound(self, time: cython.double) -> cython.int:
        index: cython.int = _tangy.clk_upper_bound(
            cython.address(self._buffer),
            _tangy.clk_bins_from_time(self._buffer.resolution[0], time))
        return index

    @cython.ccall
    def time_in_buffer(self) -> cython.double:
        return _tangy.clk_time_in_buffer(cython.address(self._buffer))


# @cython.cfunc
# def _time_in_buffer(buffer: TangyBuffers) -> float:
#     if TangyBuffers is _tangy.std_buffer:
#         return _tangy.std_time_in_buffer(cython.address(buffer))
#     elif TangyBuffers is _tangy.clk_buffer:
#         return _tangy.clk_time_in_buffer(cython.address(buffer))


_Buffer = cython.union(
    standard=_tangy.std_buffer,
    clocked=_tangy.clk_buffer)

TangyBuffer = cython.fused_type(_tangy.std_buffer, _tangy.clk_buffer)

RecordBuffer = cython.fused_type(BufferStandard, BufferClocked)


@cython.cfunc
def time_in_buffer_alt(buffer: RecordBuffer) -> float:
    if RecordBuffer is BufferStandard:
        buffer_time = _tangy.std_time_in_buffer(cython.address(buffer._buffer))
    elif RecordBuffer is BufferClocked:
        buffer_time = _tangy.clk_time_in_buffer(cython.address(buffer._buffer))
    return buffer_time


@cython.cfunc
def bins_from_time(buffer: TangyBuffer, time: float64) -> cython.ulonglong:
    bins: uint64 = 0
    if TangyBuffer is _tangy.std_buffer:
        bins = _tangy.std_bins_from_time(buffer.resolution[0], time)
    elif TangyBuffer is _tangy.clk_buffer:
        bins = _tangy.clk_bins_from_time(buffer.resolution[0], time)
    return bins


@cython.cfunc
def lower_bound_alt(buffer: TangyBuffer, time: float64) -> cython.ulonglong:
    index: uint64 = 0
    bins: uint64 = bins_from_time(buffer, time)
    if TangyBuffer is _tangy.std_buffer:
        index = _tangy.std_lower_bound(cython.address(buffer), bins)
    elif TangyBuffer is _tangy.clk_buffer:
        index = _tangy.clk_lower_bound(cython.address(buffer), bins)
    return index


@cython.cfunc
def time_in_buffer_alt_alt(buffer: TangyBuffer) -> float:
    if TangyBuffer is _tangy.std_buffer:
        buffer_time = _tangy.std_time_in_buffer(cython.address(buffer))
    elif TangyBuffer is _tangy.clk_buffer:
        buffer_time = _tangy.clk_time_in_buffer(cython.address(buffer))
    return buffer_time


# @cython.cfunc
# def _singles_alt(buffer: TangyBuffer, start: cython.ulonglong,
#                  stop: cython.ulonglong, counters: uint64[:]
#                  ) -> cython.ulonglong:
#
#     total: uint64 = 0
#     if TangyBuffer is _tangy.std_buffer:
#         total = _tangy.std_singles(cython.address(buffer), start, stop,
#                                    counters)
#     elif TangyBuffer is _tangy.clk_buffer:
#         total = _tangy.clk_singles(cython.address(buffer), start, stop,
#                                    counters)
#     return total


@cython.dataclasses.dataclass(frozen=True)
class zero_delay_result:
    times: ndarray(float64) = cython.dataclasses.field()
    intensities: ndarray(uint64) = cython.dataclasses.field()
    fit: ndarray(float64) = cython.dataclasses.field()
    tau1: cython.double = cython.dataclasses.field()
    tau2: cython.double = cython.dataclasses.field()
    t0: cython.double = cython.dataclasses.field()
    max_intensity: cython.double = cython.dataclasses.field()


def double_decay(time, tau1, tau2, t0, max_intensity):
    tau = where(time < t0, tau1, tau2)
    decay = max_intensity * exp(-nabs(time - t0) / tau)
    return decay


PyBuffers = cython.fused_type(BufferStandard, BufferClocked)


@cython.ccall
def lower_bound(buffer: RecordBuffer, read_time: float) -> int:
    time_in_buffer: float64 = buffer.time_in_buffer()
    if RecordBuffer is BufferStandard:
        index: uint64 = buffer.lower_bound(time_in_buffer - read_time)
    elif RecordBuffer is BufferClocked:
        index: uint64 = buffer.lower_bound(time_in_buffer - read_time)

    return index


@cython.ccall
def singles(buffer: RecordBuffer,
            read_time: Optional[float] = None, n_channels: int = 16,
            start: Optional[int] = None, stop: Optional[int] = None
            ) -> Tuple[int, List[int]]:
    """Count the occurances of each channel over a region of the buffer

    Args:
        buffer (RecordBuffer): Buffer containing timetags
        read_time (Optional[float] = None): Length of time to integrate over
        n_channels (int = 16): Number of channels present in the buffer
        start (Optional[int] = None): Buffer position to start counting from
        stop (Optional[int] = None): Buffer position to sotp counting to

    Returns:
        (int, List[int]): Total counts and list of total counts on each channel

    Examples:
        Get all of the singles in a buffer
        >>> tangy.singles(buffer, buffer.time_in_buffer())

        Count the singles in the last 1s
        >>> tangy.singles(buffer, 1)
    """

    counters: uint64[:] = zeros(n_channels, dtype=uint64)
    counters_view: c_uint64_t[::1] = counters

    if read_time:
        read_time: float64 = read_time
        start: uint64 = lower_bound(buffer, read_time)

    if stop is None:
        stop: uint64 = buffer.count - 1

    total: uint64 = 0

    if RecordBuffer is BufferStandard:
        total = _tangy.std_singles(cython.address(buffer._buffer), start, stop,
                                   cython.address(counters_view[0]))
        return (total, counters)

    elif RecordBuffer is BufferClocked:
        total = _tangy.clk_singles(cython.address(buffer._buffer), start, stop,
                                   cython.address(counters_view[0]))
        return (total, counters)


@cython.cclass
class StdCoincidenceMeasurement:
    _cc = cython.declare(cython.pointer(_tangy.std_cc_measurement))

    channels: cython.uchar[:]
    delays: cython.double[:]

    def __init__(self, buffer: BufferStandard, channels: List[int],
                 delays: Optional[List[float]] = None):

        n: uint64 = len(channels)
        self.channels: cython.uchar[:] = asarray(channels, dtype=uint8)
        self.delays: cython.double[:] = zeros(n, dtype=float64)

        if delays:
            for i in range(n):
                self.delays[i] = delays

        self._cc = _tangy.std_coincidence_measurement_new(
            buffer._buffer.resolution[0], n, cython.address(self.channels[0]))

    def __del__(self):
        _tangy.std_coincidence_measurement_delete(self._cc)

    @cython.ccall
    def count(self, buffer: BufferStandard, radius: float, read_time: float) -> int:
        count: uint64 = _tangy.std_coincidences_count(
            cython.address(buffer._buffer),
            self._cc.n_channels,
            cython.address(self.channels[0]),
            cython.address(self.delays[0]),
            radius, read_time)
        return count

    @cython.ccall
    def collect(self, buffer: BufferStandard, radius: float, read_time: float
                ) -> standard_records:
        count: uint64 = _tangy.std_coincidences_records(
            cython.address(buffer._buffer), cython.address(self.delays[0]),
            radius, read_time, self._cc)

        total: uint64 = self._cc.total_records
        records: ndarray(uint64) = zeros(total, dtype=uint64)
        for i in range(total):
            records[i] = self._cc.records.data[i]

        records = standard_records(total, self._cc.resolution,
                                   asarray(self.channels), records)

        return records


@cython.cclass
class ClkCoincidenceMeasurement:
    _cc = cython.declare(cython.pointer(_tangy.clk_cc_measurement))

    channels: ndarray(uint8)
    delays: ndarray(float64)

    _channels_view: cython.uchar[:]
    _delays_view: cython.double[:]

    def __init__(self, buffer: BufferClocked, channels: List[int],
                 delays: Optional[List[float]] = None):

        n: uint64 = len(channels)
        self.channels = asarray(channels, dtype=uint8)
        self.delays = zeros(n, dtype=float64)

        if delays:
            for i in range(n):
                self.delays[i] = delays[i]

        self._channels_view = self.channels
        self._delays_view = self.delays
        self._cc = _tangy.clk_coincidence_measurement_new(
            buffer._buffer.resolution[0], n,
            cython.address(self._channels_view[0]))

    def __del__(self):
        _tangy.clk_coincidence_measurement_delete(self._cc)

    @cython.ccall
    def count(self, buffer: BufferClocked, radius: float, read_time: float) -> int:
        count: uint64 = _tangy.clk_coincidences_count(
            cython.address(buffer._buffer), self._cc.n_channels,
            cython.address(self._channels_view[0]), cython.address(
                self._delays_view[0]),
            radius, read_time)
        return count

    @cython.ccall
    def collect(self, buffer: BufferClocked, radius: float, read_time: float
                ) -> clocked_records:
        count: uint64 = _tangy.clk_coincidences_records(
            cython.address(buffer._buffer), cython.address(
                self._delays_view[0]),
            radius, read_time, self._cc)
        total: uint64 = self._cc.total_records
        clocks: ndarray(uint64) = zeros(total, dtype=uint64)
        deltas: ndarray(uint64) = zeros(total, dtype=uint64)
        for i in range(total):
            clocks[i] = self._cc.records.data.clock[i]
            deltas[i] = self._cc.records.data.delta[i]

        records = clocked_records(total,
                                  self._cc.resolution.coarse,
                                  self._cc.resolution.fine,
                                  asarray(self.channels), clocks, deltas)

        return records


CCMeasurement = cython.fused_type(StdCoincidenceMeasurement,
                                  ClkCoincidenceMeasurement)


def coincidence_measurement(buffer: RecordBuffer, channels: List[int],
                            delays: Optional[List[float]] = None) -> Union[StdCoincidenceMeasurement, ClkCoincidenceMeasurement]:
    if BufferStandard is RecordBuffer:
        return StdCoincidenceMeasurement(buffer, channels, delays)
    elif BufferClocked is RecordBuffer:
        return ClkCoincidenceMeasurement(buffer, channels, delays)


@cython.cclass
class CoincidenceMeasurementStandard:
    _cc = cython.declare(cython.pointer(_tangy.std_cc_measurement))

    channels: ndarray(uint8)
    delays: ndarray(float64)

    _channels_view: cython.uchar[:]
    _delays_view: cython.double[:]

    def __init__(self, resolution: float, channels: List[int],
                 delays: Optional[List[float]] = None):

        n: uint64 = len(channels)
        self.channels = asarray(channels, dtype=uint8)
        self.delays = zeros(n, dtype=float64)

        if delays:
            for i in range(n):
                self.delays[i] = delays[i]

        self._channels_view = self.channels
        self._delays_view = self.delays
        self._cc = _tangy.std_coincidence_measurement_new(
            resolution, n, cython.address(self._channels_view[0]))

    def __del__(self):
        _tangy.std_coincidence_measurement_delete(self._cc)


@cython.cclass
class CoincidenceMeasurementClocked:
    _cc = cython.declare(cython.pointer(_tangy.clk_cc_measurement))

    channels: ndarray(uint8)
    delays: ndarray(float64)

    _channels_view: cython.uchar[:]
    _delays_view: cython.double[:]

    def __init__(self, resolution: Tuple[float, float], channels: List[int],
                 delays: Optional[List[float]] = None):

        n: uint64 = len(channels)
        self.channels = asarray(channels, dtype=uint8)
        self.delays = zeros(n, dtype=float64)

        if delays:
            for i in range(n):
                self.delays[i] = delays[i]

        self._channels_view = self.channels
        self._delays_view = self.delays
        res: _tangy.clk_res
        res.coarse = resolution[0]
        res.fine = resolution[1]
        self._cc = _tangy.clk_coincidence_measurement_new(
            res, n, cython.address(self._channels_view[0]))

    def __del__(self):
        _tangy.clk_coincidence_measurement_delete(self._cc)


@cython.cclass
class CoincidenceMeasurement:
    _measurement: Union[
        CoincidenceMeasurementStandard,
        CoincidenceMeasurementClocked]

    def __init__(self, buffer: Union[BufferStandard, BufferClocked],
                 channels: List[int], delays: Optional[List[float]] = None):

        resolution = buffer.resolution
        if type(buffer) is BufferStandard:
            self._measurement = CoincidenceMeasurementStandard(resolution,
                                                               channels,
                                                               delays)
        elif type(buffer) is BufferClocked:
            self._measurement = CoincidenceMeasurementClocked(resolution,
                                                              channels, delays)
        return

    def count(self, buffer: Union[BufferStandard, BufferClocked],
              radius: float, read_time: float) -> int:

        count: uint64 = 0
        if type(buffer) is BufferStandard:
            count = _tangy.std_coincidences_count(
                    cython.address(buffer._buffer),
                    len(self._measurement.channels),
                    cython.address(self._measurement._channels_view[0]),
                    cython.address(self._measurement._delays_view[0]),
                    radius, read_time)
        elif type(buffer) is BufferClocked:
            count = _tangy.clk_coincidences_count(
                    cython.address(buffer._buffer),
                    len(self._measurement.channels),
                    cython.address(self._measurement._channels_view[0]),
                    cython.address(self._measurement._delays_view[0]),
                    radius, read_time)
        return count



# def collect_coincidences(buffer: RecordBuffer, channels: List[int],
#                          delays: Optiona[List[float]], radius: float,
#                          read_time: float) -> Union[
#     Tuple[int, clocked_records, CCMeasurement],
#     Tuple[int, standard_records, CCMeasurement]
# ]:
#     if BufferStandard is RecordBuffer:
#         measurement = StdCoincidenceMeasurement(buffer, channels, delays)
#         (count, records) = measurement.count(buffer, radius, read_time)
#         return (count, records, measurement)
#     elif BufferClocked is RecordBuffer:
#         measurement = ClkCoincidenceMeasurement(buffer, channels, delays)
#         (count, records) = measurement.count(buffer, radius, read_time)
#         return (count, records, measurement)


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.ccall
def coincidences(buffer: RecordBuffer, channels: cython.uchar[:],
                 delays: cython.double[:], diameter: float,
                 read_time: float) -> int:

    n_channels: uint64 = channels.shape[0]
    count: uint64 = 0

    if RecordBuffer is BufferStandard:
        count = _tangy.std_coincidences_count(cython.address(buffer._buffer),
                                              n_channels,
                                              cython.address(channels[0]),
                                              cython.address(delays[0]),
                                              diameter, read_time)
    elif RecordBuffer is BufferClocked:
        count = _tangy.clk_coincidences_count(cython.address(buffer._buffer),
                                              n_channels,
                                              cython.address(channels[0]),
                                              cython.address(delays[0]),
                                              diameter, read_time)
    return count


@cython.ccall
def timetrace(buffer: RecordBuffer, channels: List[int], read_time: float,
              resolution: float = 10) -> List[int]:

    n_channels: uint64 = len(channels)
    channels: uint8[:] = asarray(channels, dtype=uint8)
    channels_view: cython.uchar[::1] = channels
    channels_ptr: cython.pointer(cython.uchar) = cython.address(
        channels_view[0])

    buffer_resolution: float64 = 0
    if RecordBuffer is BufferStandard:
        buffer_resolution = buffer._buffer.resolution[0]
    elif RecordBuffer is BufferClocked:
        buffer_resolution = buffer._buffer.resolution[0].fine

    bin_width: uint64 = round(resolution / buffer_resolution)

    n: cython.int = 1
    if resolution < read_time:
        n = int(read_time // resolution) + 1

    intensities: uint64[:] = zeros(n, dtype=uint64)
    intensities_view: c_uint64_t[::1] = intensities
    intensities_ptr: cython.pointer(c_uint64_t) = cython.address(
        intensities_view[0])

    if RecordBuffer is BufferStandard:
        total: uint64 = _tangy.std_timetrace(cython.address(buffer._buffer),
                                             read_time,
                                             bin_width,
                                             channels_ptr,
                                             n_channels,
                                             intensities_ptr)
    elif RecordBuffer is BufferClocked:
        total: uint64 = _tangy.clk_timetrace(cython.address(buffer._buffer),
                                             read_time,
                                             bin_width,
                                             channels_ptr,
                                             n_channels,
                                             intensities_ptr)
    return intensities


@cython.ccall
def find_zero_delay(buffer: RecordBuffer, channel_a: int, channel_b: int,
                    read_time: float, resolution: float = 1e-9
                    ) -> zero_delay_result:

    trace_res: float64 = 5e-2
    trace: uint64[:] = timetrace(
        buffer, [channel_a, channel_b], read_time, trace_res)

    avrg_intensity = mean(trace) / trace_res

    correlation_window = 2 / avrg_intensity * 2

    if resolution is None:
        resolution = (2 / avrg_intensity) / 8000

    res: float64 = 0
    if RecordBuffer is BufferStandard:
        res = buffer._buffer.resolution[0]
    elif RecordBuffer is BufferClocked:
        res = buffer._buffer.resolution[0].fine

    n_bins: uint64 = round(correlation_window / resolution) - 1
    correlation_window = correlation_window / res

    measurement_resolution: uint64 = uint64(
        correlation_window / float64(n_bins))

    correlation_window = n_bins * measurement_resolution
    n_bins = n_bins * 2
    intensities: uint64[:] = zeros(n_bins, dtype=uint64)
    intensities_view: c_uint64_t[::1] = intensities

    if RecordBuffer is BufferStandard:
        _tangy.std_find_zero_delay(cython.address(buffer._buffer),
                                   read_time,
                                   uint64(correlation_window),
                                   measurement_resolution,
                                   channel_a,
                                   channel_b,
                                   n_bins,
                                   cython.address(intensities_view[0]))

    elif RecordBuffer is BufferClocked:
        _tangy.clk_find_zero_delay(cython.address(buffer._buffer),
                                   read_time,
                                   uint64(correlation_window),
                                   measurement_resolution,
                                   channel_a,
                                   channel_b,
                                   n_bins,
                                   cython.address(intensities_view[0]))

    times = (arange(n_bins) - (n_bins // 2)) * resolution
    max_idx = intensities.argmax()
    intensities[max_idx] = 0
    t0 = times[intensities.argmax()]

    tau = 2 / avrg_intensity
    max_intensity = intensities.max()

    guess = [tau, tau, t0, max_intensity]

    [opt, cov] = curve_fit(double_decay, times, intensities, p0=guess)
    hist_fit = double_decay(times, *opt)
    result = zero_delay_result(
        times=times,
        intensities=intensities,
        fit=hist_fit,
        tau1=opt[0],
        tau2=opt[1],
        t0=opt[2],
        max_intensity=opt[3])

    return result


Resolution = cython.fused_type(_tangy.std_res, _tangy.clk_res)


@cython.ccall
def Buffer(name: str, length: int, n_channels: int,
           resolution: Optional[Union[float, [float, float]]]):
    """Function to create a new buffer or connect to an existing one

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (Optional[Union[float, Tuple[float, float]]]): Resolution \
        of timetags in seconds. A single float for the "standard timetags". A \
        pair of floats for "clocked timetags" with a "coarse" and "fine" \
        timing structure. Unused if connecting.
        n_channels (int): Number of channels
        length (Optional[int] = 1000): Length of buffer to create. Unused if \
        connecting.

    Returns:
        An instance of either the ``BufferStandard`` or ``BufferClocked``\
        classes

    Note:
        For buffers using the clocked timetag format the resolution must be \
        specified as a tuple in the form (coarse resolution, fine resolution).\
        As an example a clock signal from an 80Mhz TiSapphire laser and a fine\
        resolution on-board the time timetagger would give: \
        ``resolution = (12.5e-9, 1e-12)``

    Examples:
        Create a new buffer with the standard format
        >>> standard_buffer = tangy.buffer("standard", 1e-9, 4, int(1e6))

        Create a new buffer with the clocked format
        >>> resolution = (12.5e-9, 1e-12) # 80Mhz Clock and 1ps fine resolution
        >>> my_buffer = tangy.buffer("clocked", resolution, 4, int(1e6))

        Connect to existing buffer
        >>> standard_buffer_connection = tangy.buffer("standard")
        >>> clocked_buffer_connection = tangy.buffer("clocked")
    """
    if type(resolution) is float:
        return BufferStandard(name, length, resolution, n_channels)
    elif type(resolution) is tuple:
        return BufferClocked(name, length, resolution[0], resolution[1],
                             n_channels)


@ cython.cfunc
def new_buffer(name: str, length: int, n_channels: int,
               resolution: Resolution):

    if Resolution is _tangy.std_res:
        return BufferStandard(name, length, resolution, n_channels)

    elif Resolution is _tangy.clk_res:
        return BufferClocked(name, length, resolution.coarse, resolution.fine,
                             n_channels)


BufferT = cython.fused_type(_tangy.std_buffer, _tangy.clk_buffer)

Record = cython.fused_type(_tangy.standard, _tangy.clocked)


@ cython.cfunc
def time_from_record(record: Record, resolution: Resolution):
    time: float64 = 0
    if Record is _tangy.standard and Resolution is _tangy.std_res:
        time = _tangy.std_to_time(record, resolution)
    elif Record is _tangy.clocked and Resolution is _tangy.clk_res:
        time = _tangy.clk_to_time(record, resolution)
    return time


@ cython.cfunc
def bins_from_record(record: Record, resolution: Resolution):
    bins: uint64 = 0
    if Record is _tangy.standard and Resolution is _tangy.std_res:
        bins = _tangy.std_as_bins(record, resolution)
    elif Record is _tangy.clocked and Resolution is _tangy.clk_res:
        bins = _tangy.clk_as_bins(record, resolution)
    return bins


@ cython.cfunc
def _read_next(buffer: BufferT,
               file_handle: cython.pointer(FILE),
               status: cython.pointer(_tangy.READER_STATUS), n: uint64):
    res: uint64
    if BufferT is _tangy.std_buffer:
        res = _tangy.read_next_HH2_T2(
            cython.address(buffer), file_handle, status, n)
    elif BufferT is _tangy.clk_buffer:
        res = _tangy.read_next_HH2_T3(
            cython.address(buffer), file_handle, status, n)

    return res


_ptu_header_tag_types = {
    "tyEmpty8":      0xFFFF0008,
    "tyBool8":       0x00000008,
    "tyInt8":        0x10000008,
    "tyBitSet64":    0x11000008,
    "tyColor8":      0x12000008,
    "tyFloat8":      0x20000008,
    "tyTDateTime":   0x21000008,
    "tyFloat8Array": 0x2001FFFF,
    "tyAnsiString":  0x4001FFFF,
    "tyWideString":  0x4002FFFF,
    "tyBinaryBlob":  0xFFFFFFFF,
}
_ptu_header_tag_types_reversed = {v: k
                                  for k, v in _ptu_header_tag_types.items()}
_ptu_record_types = {
    'PicoHarpT3':     66307,
    'PicoHarpT2':     66051,
    'HydraHarpT3':    66308,
    'HydraHarpT2':    66052,
    'HydraHarp2T3':   16843524,
    'HydraHarp2T2':   16843268,
    'TimeHarp260NT3': 66309,
    'TimeHarp260NT2': 66053,
    'TimeHarp260PT3': 66310,
    'TimeHarp260PT2': 66054,
    'MultiHarpNT3':   66311,
    'MultiHarpNT2':   66055,
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
    "PicoHarpT3":     {
        "isT2": False,
        "version": 0,
        "wraparound": _wraparound["PT3_0"],
    },
    "PicoHarpT2":     {
        "isT2": True,
        "version": 0,
        "wraparound": _wraparound["PT2_0"],
    },
    "HydraHarpT3":    {
        "isT2": False,
        "version": 1,
        "wraparound": _wraparound["HT3_1"],
    },
    "HydraHarpT2":    {
        "isT2": True,
        "version": 1,
        "wraparound": _wraparound["HT2_1"],
    },
    "HydraHarp2T3":   {
        "isT2": False,
        "version": 2,
        "wraparound": _wraparound["HT3_2"],
    },
    "HydraHarp2T2":   {
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
    "MultiHarpNT3":   {
        "isT2": False,
        "version": 2,
        "wraparound": _wraparound["HT3_2"],
    },
    "MultiHarpNT2":   {
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
        length (int = 1000)

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
    _std_buffer: BufferStandard
    _clk_buffer: BufferClocked

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
            s_res: _tangy.std_res = sync_res
            self._std_buffer = new_buffer[_tangy.std_res](
                name, length, n_ch, s_res)
            return

        if "T3" in key:
            self._buffer_type = _tangy.BufferType.Clocked
            c_res: _tangy.clk_res
            c_res.coarse = glob_res
            c_res.fine = sync_res
            self._clk_buffer = new_buffer[_tangy.clk_res](
                name, length, n_ch, c_res)
            print(self._clk_buffer.resolution)
            return

        raise ValueError

    def __del__(self):
        fclose(self._c_file_handle)
        self._file_handle.close()

    def __repr__(self):
        if _tangy.BufferType.Standard == self._buffer_type:
            return self._std_buffer.__repr__()
        if _tangy.BufferType.Clocked == self._buffer_type:
            return self._clk_buffer.__repr__()

    @ property
    def buffer(self):
        if _tangy.BufferType.Standard == self._buffer_type:
            return self._std_buffer
        if _tangy.BufferType.Clocked == self._buffer_type:
            return self._clk_buffer

    @ property
    def record_count(self):
        return self._status.record_count

    @ property
    def header(self):
        return self._header

    def __getitem__(self, index):
        if _tangy.BufferType.Standard == self._buffer_type:
            return self._std_buffer[index]

        elif _tangy.BufferType.Clocked == self._buffer_type:
            return self._clk_buffer[index]

    def __len__(self):
        return len(self._buffer)

    @ property
    def count(self):
        x: uint64 = 0
        if _tangy.BufferType.Standard == self._buffer_type:
            x = self._std_buffer.count
        if _tangy.BufferType.Clocked == self._buffer_type:
            x = self._clk_buffer.count

        return x

    def records(self, index):
        if _tangy.BufferType.Standard == self._buffer_type:
            (channels, timetags) = self._std_buffer[index]
            n = len(channels)
            return standard_records(n, self._std_buffer.resolution, channels,
                                    timetags)
        elif _tangy.BufferType.Clocked == self._buffer_type:
            (channels, clocks, deltas) = self._clk_buffer[index]
            (coarse, fine) = self._clk_buffer.resolution
            n = len(channels)
            return clocked_records(n, coarse, fine, channels, clocks, deltas)

    def read(self, n: uint64):
        """
        Read an amount of tags from the target file

        :param n: [TODO:description]
        """
        if _tangy.BufferType.Standard == self._buffer_type:
            res: uint64 = _tangy.read_next_HH2_T2(
                cython.address(self._std_buffer._buffer), self._c_file_handle,
                self._status, n)

        if _tangy.BufferType.Clocked == self._buffer_type:
            res: uint64 = _tangy.read_next_HH2_T3(
                cython.address(self._clk_buffer._buffer), self._c_file_handle,
                self._status, n)

        return res

    def read_seconds(self, t: float64):
        if _tangy.BufferType.Standard == self._buffer_type:
            ch_last: uint8
            tt_last: uint64
            (ch_last, tt_last) = self._std_buffer[-1]
            bins: uint64 = _tangy.std_as_bins(
                new_standard_record(ch_last, tt_last),
                self._std_buffer._resolution())

            res: uint64 = _tangy.read_next_HH2_T2(
                cython.address(self._std_buffer._buffer), self._c_file_handle,
                self._status, bins)

        if _tangy.BufferType.Clocked == self._buffer_type:
            (ch_last, cl_last, d_last) = self._clk_buffer[-1]

            bins: uint64 = _tangy.clk_as_bins(
                new_clocked_record(ch_last, cl_last, d_last),
                self._clk_buffer._resolution())

            res: uint64 = _tangy.read_next_HH2_T3(
                cython.address(self._clk_buffer._buffer), self._c_file_handle,
                self._status, bins)

        return res


@cython.cfunc
def new_standard_record(channel: uint8, timetag: uint64):
    new: _tangy.standard
    new.channel = channel
    new.timetag = timetag
    return new


@cython.cfunc
def new_clocked_record(channel: uint8, clock: uint64, delta: uint64):
    new: _tangy.clocked
    new.channel = channel
    new.clock = clock
    new.delta = delta
    return new
