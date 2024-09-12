import cython
from cython.cimports import _tangy as _tangy
import warnings

import mmap
from os import dup, listdir, remove, makedirs
from os.path import getsize, join, exists
import json
from scipy.optimize import curve_fit
from numpy import mean, where, exp, roll
from numpy import round as npround
from numpy import abs as nabs
from numpy import arange, array, ndarray, asarray, zeros, frombuffer, reshape
from numpy import uint8 as u8n
from numpy import uint64 as u64n
from numpy import int64 as i64n
from numpy import float64 as f64n

from cython.cimports.libc.stdio import FILE, fdopen, fclose
from cython.cimports.libc.stdint import uint8_t as u8
# from cython.cimports.libc.stdint import uint32_t as u32
from cython.cimports.libc.stdint import uint64_t as u64
from cython.cimports.libc.stdint import int64_t as i64
import struct
from typing import List, Tuple, Optional, Union
from numpy.typing import NDArray
from enum import Enum
from platformdirs import user_config_dir
from warnings import warn

__all__ = [
    "tangy_config_location",
    "Records",
    "JointHistogram",
    "centre_histogram",
    "bin_histogram",
    "delay_result",
    "TangyBufferType",
    "TangyBuffer",
    "PTUFile",
    "buffer_list_update",
    "buffer_list_append",
    "buffer_list_delete_all",
    "buffer_list_show",
]


@cython.ccall
def tangy_config_location() -> str:
    appname = "Tangy"
    appauthor = "PeterBarrow"

    config_path = user_config_dir(appname, appauthor)
    if not exists(config_path):
        makedirs(config_path)
    return config_path


@cython.dataclasses.dataclass(frozen=True)
class Records:
    """Container for timetags

    Contains array of timetags, required channel information will be either an
        array of the same dimensions as timetags or simply the only channels.
        allowed corresponding to a specific coincidence pattern.

    Args:
        count (u64n): Number of events
        resolution (float): Resolution of timetags
        clock_period (float): Clock period (if required)
        channels (ndarray(u8n)): Channels
        timetags (Union[ndarray(u64n), Tuple[ndarray(u64n), ndarray(u64n)]]): Timetags

    Examples:
        >>> records = Records(count=10, resolution=1e-9, clock_period=1.0,
        >>>                   channels=[0, 1], timetags=[0, ..., 10])

        >>> records = Records(count=4, resolution=1e-9, clock_period=1.0,
        >>>                   channels=[0, 1, 1, 0], timetags=[0, 1, 4, 5])

    """
    count: u64n = cython.dataclasses.field()
    resolution: float = cython.dataclasses.field()
    clock_period: float = cython.dataclasses.field()
    channels: ndarray(u8n) = cython.dataclasses.field()
    timetags: Union[ndarray(u64n), Tuple[ndarray(
        u64n), ndarray(u64n)]] = cython.dataclasses.field()


@cython.dataclasses.dataclass(frozen=True)
class JointHistogram:
    """JSI result
    """

    central_bin: int = cython.dataclasses.field()
    temporal_window: float = cython.dataclasses.field()
    bin_size: Tuple[int, int] = cython.dataclasses.field()
    data: ndarray(u64n) = cython.dataclasses.field()
    marginal_idler: ndarray(u64n) = cython.dataclasses.field()
    marginal_signal: ndarray(u64n) = cython.dataclasses.field()
    axis_idler: ndarray(f64n) = cython.dataclasses.field()
    axis_signal: ndarray(f64n) = cython.dataclasses.field()

    # TODO: add rebin function "def rebin(self, x, y) -> JointHistogram"


@cython.wraparound(False)
@cython.boundscheck(False)
@cython.ccall
def centre_histogram(central_bin: int, temporal_window: int,
                     marginal_idler: ndarray(u64n), marginal_signal: ndarray(u64n),
                     histogram: ndarray(u64n)):
    """
    Centre a 2D histogram and marginals

    Todo:
        central_bin and temporal_window arguments should be removable, instead\
        everything should be calculated from the dimensions of the marginals

    Args:
        central_bin (int): central bin
        temporal_window (int): temporal window
        marginal_idler (ndarray(u64n)): Marginal distribution of idler
        marginal_signal (ndarray(u64n)): Marginal distribution of sigal
        histogram (ndarray(u64n)): 2D joint histogram of signal and idler

    Returns:
        (Tuple[ndarray(u64n),ndarray(u64n),ndarray(u64n)]): Tuple of idler\
        marginal, signal marginal and joint histogram
    """

    bins = arange(temporal_window) - central_bin
    offset_idler: int = int(npround(
        mean(bins[marginal_idler > (0.1 * marginal_idler.max())])))
    offset_signal: int = int(npround(
        mean(bins[marginal_signal > (0.1 * marginal_signal.max())])))

    offset_idler *= (-1)
    offset_signal *= (-1)

    return (
        roll(marginal_idler, offset_idler),
        roll(marginal_signal, offset_signal),
        roll(roll(histogram, offset_idler, axis=0), offset_signal, axis=1)
    )


@cython.wraparound(False)
@cython.boundscheck(False)
@cython.cfunc
def bin_histogram(histogram: ndarray(u64n), x_width: i64, y_width: i64
                  ) -> Tuple[Tuple[u64n, u64n], ndarray(u64n), ndarray(u64n), ndarray(u64n)]:

    (n_rows, n_cols) = histogram.shape

    histogram_view: u64[:, ::1] = histogram

    n_cols_new: i64 = n_cols // y_width
    n_rows_new: i64 = n_rows // x_width

    result = zeros([n_rows_new, n_cols_new], dtype=u64n)
    result_view: u64[:, ::1] = result

    marginal_signal = zeros(n_rows_new, dtype=u64n)
    marginal_idler = zeros(n_cols_new, dtype=u64n)

    marginal_signal_view: u64[::1] = marginal_signal
    marginal_idler_view: u64[::1] = marginal_idler

    i: i64
    i_start: i64
    i_stop: i64
    j: i64
    j_start: i64
    j_stop: i64

    x: i64
    y: i64

    value: u64 = 0

    for i in range(n_rows_new):
        i_start = i * y_width
        i_stop = i_start + y_width
        for j in range(n_cols_new):
            j_start = j * x_width
            j_stop = j_start + x_width
            value = 0
            for y in range(i_start, i_stop):
                for x in range(j_start, j_stop):
                    value += histogram_view[y][x]
            result_view[i][j] = value
            marginal_idler_view[i] += value
            marginal_signal_view[j] += value

    return ((n_rows_new, n_cols_new), marginal_signal, marginal_idler, result)

# TODO: def extract_marginals


def double_decay(time, tau1, tau2, t0, max_intensity):
    tau = where(time < t0, tau1, tau2)
    decay = max_intensity * exp(-nabs(time - t0) / tau)
    return decay


@cython.dataclasses.dataclass(frozen=True)
class delay_result:
    times: ndarray(f64n) = cython.dataclasses.field()
    intensities: ndarray(u64n) = cython.dataclasses.field()
    fit: ndarray(f64n) = cython.dataclasses.field()
    tau1: cython.double = cython.dataclasses.field()
    tau2: cython.double = cython.dataclasses.field()
    t0: cython.double = cython.dataclasses.field()
    central_delay: cython.double = cython.dataclasses.field()
    max_intensity: cython.double = cython.dataclasses.field()


@cython.cfunc
def raise_shmem_error(result: _tangy.shmem_result):
    if result.Error == _tangy.shmem_error.SM_MAP_CREATE:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)
        raise RuntimeError("Failed to create map")

    if result.Error == _tangy.shmem_error.SM_HANDLE_TO_FD:
        raise RuntimeError("Could not convert handle to file descriptor")

    if result.Error == _tangy.shmem_error.SM_FD_TO_HANDLE:
        raise RuntimeError("Could not convert file descriptor to handle")

    if result.Error == _tangy.shmem_error.SM_MEMORY_MAPPING:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)
        raise RuntimeError("Memory failed failed")

    if result.Error == _tangy.shmem_error.SM_FTRUNCATE:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)

    if result.Error == _tangy.shmem_error.SM_MAP:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)

    if result.Error == _tangy.shmem_error.SM_STAT:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)

    if result.Error == _tangy.shmem_error.SM_FSTAT:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)

    if result.Error == _tangy.shmem_error.SM_UNMAP:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)

    if result.Error == _tangy.shmem_error.SM_FD_CLOSE:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)

    if result.Error == _tangy.shmem_error.SM_UNLINK:
        if result.Std_Error != 0:
            raise OSError(result.Std_Error)


class TangyBufferType(Enum):
    """ Format of timetags to use in instance of TangyBuffer
    """
    Standard = 0
    Clocked = 1


@cython.cclass
class TangyBuffer:
    """Interface to underlying ring buffer

    Provides ability to create, connect and modify a buffer of timetags and
        includes method to analyse the timetags currently held within it.

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (float = 0.1, optional): Resolution of timetags in seconds.
            Unused if connecting.
        clock_period (float = 1.0, optional): Length of clock period in seconds for
            measurements that include clock information in each timetag. Unused
            if connecting
        channel_count (Optional[int] = 4, optional): Number of channels. Unused
            if connecting.
        length (Optional[int] = 10_000_000, optional): Length of buffer to create.
            Unused if connecting.
        format (TangyBufferType = TangyBufferType.Standard, optional): Format of
            timetags in the buffer, default is the ```standard``` format with a
            single value for the channel and single value for timeing information.
            Unused if connecting.

    Attributes:
        name (str): Name of buffer
        resolution (float): Resolution of timetags in seconds
        clock_period (float): Clock period of clock signal used if timetags with
            clock information are used. Defaults to 1.0 otherwise
        resolution_bins (int): Resolution in bins
        clock_period_bins (int): Clock period in units of resolution
        conversion_factor (int): Factor to convert between time and bins
        capacity (int): Maximum number of timetags that can be stored
        count (int): total number of timetags written to the buffer
        reference_count (int): Number of reference to current open buffer. Other
            processes can connect to the same buffer
        channel_count (int): Number of available channels in the buffer
        begin (int): Index of first timetag. Can be greater than capacity
        end (int): Index of last timetag. Can be greater than capacity and will
            always be greater than ```begin```

    Note:
        If connecting to an existing buffer the resolution, clock_period,
        n_channels, capacity and format arguments will be ignored even if
        supplied. The correct values will be made available from the buffer
        connected to.

    Examples:
        Creation of a TangyBuffer object for both the ``Standard`` and \
        ``Clocked`` timetag formats that can hold 1,000,000 timetags for a \
        device with 4 channels. The method to connect to these buffers is also \
        shown. This method of creating new buffers and connecting to existing \
        ones allows the user to hold on to and continously read timetags from \
        a device in one process and then connect to that buffer in another to \
        perform analysis on the current data.
        === "Buffer in ``Standard`` format"
            ```python
            # Here we will create a buffer called 'standard' (imaginitive)
            # that will only except timetags in the ``Standard`` format
            standard_buffer = tangy.TangyBuffer("standard", 1e-9,
                                                channel_count=4,
                                                capacity=int(1e6)
                                                format=TangyBufferType.Standard)

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            standard_buffer_connection = tangy.TangyBuffer("standard")
            ```

        === "Buffer in ``Clocked`` format"
            ```python
            # Here we will create a buffer called 'clocked' (imaginitive)
            # that will only except timetags in the ``Clocked`` format
            clocked_buffer = tangy.TangyBuffer("clocked", 1e-12,
                                                clock_period=12.5e-9,  # 80MHz Ti-Sapph
                                                channel_count=4,
                                                capacity=int(1e6)
                                                format=TangyBufferType.Clocked)

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            clocked_buffer_connection = tangy.TangyBuffer("clocked")
            ```
    """

    _name = cython.declare(bytes)
    _buf: _tangy.tangy_buffer
    _ptr_buf: cython.pointer(_tangy.tangy_buffer)
    _ptr_rb: cython.pointer(_tangy.shared_ring_buffer)
    _format: TangyBufferType
    _ptr_rec_vec: cython.pointer(_tangy.tangy_record_vec)

    def __init__(self, name: str, resolution: float = 0.1,
                 clock_period: float = 1.0,
                 channel_count: int = 4,
                 capacity: int = 10_000_000,
                 format: TangyBufferType = TangyBufferType.Standard):

        buffer_list_update()

        # TODO: connect to buffers without need to specify format
        # See buffer_list_delete_all for for details

        self._format = format

        self._name = name.encode('utf-8')
        c_name: cython.p_char = self._name

        self._ptr_buf = cython.address(self._buf)

        result: _tangy.shmem_result = _tangy.tangy_buffer_connect(
            c_name, self._ptr_buf)
        if result.Ok is True:
            self._ptr_rb = cython.address(self._buf.buffer)
            return

        buffer_format: _tangy.buffer_format = _tangy.buffer_format.STANDARD
        if format == TangyBufferType.Clocked:
            buffer_format = _tangy.buffer_format.CLOCKED

        result: _tangy.shmem_result = _tangy.tangy_buffer_init(buffer_format,
                                                               c_name,
                                                               capacity,
                                                               resolution,
                                                               clock_period,
                                                               channel_count,
                                                               self._ptr_buf)

        if result.Ok is False:
            raise_shmem_error(result)

        self._ptr_rb = cython.address(self._buf.buffer)
        buffer_list_append(self)

        return

    def __del__(self):
        c_name: cython.p_char = self._name
        flag: u8 = 0
        result: _tangy.shmem_result = _tangy.shmem_exists(c_name,
                                                          cython.address(flag))
        if exists == 0:
            buffer_list_update()
            return

        result = _tangy.tangy_buffer_deinit(self._ptr_buf)
        if result.Ok is False:
            raise_shmem_error(result)
        buffer_list_update()

    def close(self):
        self.__del__()

    def __len__(self):
        """ Length of buffer

        Returns:
            (int): Length of buffer
        """
        return self.capacity

    @cython.cfunc
    def _make_slice(self, key: Union[int, slice]):
        start: int
        stop: int
        step: int = 1

        if type(key) is slice:
            step: int = 1 if key.step is None else key.step

            # oldest = self.begin

            dist: int = abs(abs(key.stop) - abs(key.start))
            if (key.start > self.capacity) or (key.stop > self.capacity):
                if dist > self.capacity:
                    raise IndexError("out of range")
                start = key.start
                stop = key.stop
                # print("here", start, stop, stop)
                return (start, stop, step)

            # if key.start < self.begin:
            #     start = oldest + self.begin
            if key.start < 0:
                # print("a")
                start = (self.count + key.start - 1) % self.capacity
                # stop = start + dist + 1
                stop = start + dist
            else:
                # print("b")
                start = key.start
                if start < self.begin:
                    start += self.begin
                start = (start % self.capacity)
                # stop = start + dist + 1
                stop = key.stop
                if stop < self.begin:
                    stop += self.begin
                # stop = (stop % self.capacity) + 1
                stop = (stop % self.capacity)

            # start = (key.start % self.capacity)
            # # stop = start + key.stop
            # stop = start + dist + 1

        if type(key) is int:
            if abs(key) > self.count:
                raise IndexError("out of range")

            if (key > self.capacity):
                start = key
                stop = key + 1
                return (start, stop, step)

            if key < 0:
                start = (self.count + key - 1) % self.capacity
                stop = start + 1
            else:
                if key < self.begin:
                    key += self.begin
                start = (key % self.capacity)
                stop = start + 1

        if abs(abs(stop) - abs(start)) > self.count:
            raise IndexError("out of range")

        # print("down here", start, stop, stop)
        return (start, stop, step)

    @cython.ccall
    def _get(self, key):
        (start, stop, step) = self._make_slice(key)

        if self._buf.format == _tangy.buffer_format.STANDARD:
            (channels, timestamps) = self.pull(start, stop)
            if len(channels) == 1:
                return (channels[0], timestamps[0])
            return (channels[::step], timestamps[::step])

        if self._buf.format == _tangy.buffer_format.CLOCKED:
            (channels, (clocks, deltas)) = self.pull(start, stop)
            if len(channels) == 1:
                return (channels[0], (clocks[0], deltas[0]))
            return (channels[::step], (clocks[::step], deltas[::step]))

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __getitem__(self, key):
        """ Access subscript of buffer

        """
        return self._get(key)

    @cython.cfunc
    def _call(self, time: float) -> int:

        time_at_start: f64n = 0
        time_at_stop: f64n = 0
        (time_at_start, time_at_stop) = self.time_range()

        # idx: int = self.begin

        if time < 0:
            return self.lower_bound(time_at_stop + time)

        if time <= time_at_stop:
            return self.lower_bound(time_at_start + time)

        # NOTE: should look into upper_bound here for searching from startraise NotImplementedError

        return 0

    def __call__(self, time: float) -> int:
        """ Converts a time to an buffer position

        Takes a time and converts it to a position in the buffer relative to the
            total time currently held within the buffer. Positive numbers find
            positions from the start of the buffer whilst negative numbers find
            positions from the end of the buffer.

        Examples:
            Find the position bounding the first second in the buffer
            >>> idx = buffer(1)
            Find the position bounding the last second in the buffer
            >>> idx = buffer(-1)

        Returns:
            (int): Index corresponding to requested time
        """
        return self._call(time)

    @property
    def name(self) -> str:
        """ Name of buffer

        Returns:
            (str): buffer name
        """
        return self._name.decode("utf-8")

    @property
    def resolution(self) -> float:
        """ Resolution of timetags in buffer

        Returns:
            (float): resolution of timetags
        """
        return _tangy.srb_get_resolution(cython.address(self._buf.buffer))

    @resolution.setter
    def resolution(self, res: float):
        _tangy.srb_set_resolution(self._ptr_rb, res)
        cf: u64n = _tangy.srb_conversion_factor(res, self.clock_period)
        _tangy.srb_set_conversion_factor(self._ptr_rb, cf)

    @property
    def clock_period(self) -> float:
        """ Clock period of timetags in buffer

        For timetags with 'coarse + fine' timing this returns the 'coarse'
            timing component, typically this will be the resolution / period
            of an external clock signal

        Returns:
            (float): clock period of timetags
        """
        return _tangy.srb_get_clock_period(self._ptr_rb)

    @clock_period.setter
    def clock_period(self, period: float):
        _tangy.srb_set_clock_period(self._ptr_rb, period)
        cf: u64n = _tangy.srb_conversion_factor(self.resolution, period)
        _tangy.srb_set_conversion_factor(self._ptr_rb, cf)

    @property
    def resolution_bins(self) -> int:
        """ Resolution in terms of bins of timetags in buffer

        Returns:
            (int): resolution of timetags
        """
        return _tangy.srb_get_resolution_bins(self._ptr_rb)

    @property
    def clock_period_bins(self) -> int:
        """ Clock period in terms of bins of timetags in buffer

        Returns:
            (int): clock period of timetags
        """
        return _tangy.srb_get_clock_period_bins(self._ptr_rb)

    @property
    def conversion_factor(self) -> int:
        """doc"""
        return _tangy.srb_get_conversion_factor(self._ptr_rb)

    @property
    def capacity(self) -> int:
        """ Maximum number of timetags the buffer can hold

        Returns:
            (int): maximum number of timetags
        """
        return _tangy.srb_get_capacity(self._ptr_rb)

    @property
    def count(self) -> int:
        """ Number of timetags written to the buffer
        """
        return _tangy.srb_get_count(self._ptr_rb)

    @property
    def reference_count(self) -> int:
        """ Number of current connections to the buffer

        Tracks number of connections to buffer, used to determine if it is safe
            to delete the backing memory and close the memory mapping.

        Returns:
            (int): number of connections
        """
        return _tangy.srb_get_reference_count(self._ptr_rb)

    @reference_count.setter
    def reference_count(self, rc: int):
        _tangy.srb_set_reference_count(self._ptr_rb, rc)

    @property
    def channel_count(self) -> int:
        """ Maximum number of channels in the buffer

        Typically set by a device or a file to limit the range of valid channels
            available.

        Returns:
            (int): number of channels
        """
        return _tangy.srb_get_channel_count(self._ptr_rb)

    @channel_count.setter
    def channel_count(self, n_ch: int):
        _tangy.srb_set_channel_count(self._ptr_rb, n_ch)

    def configuration(self) -> dict:
        config = {
            "name": self._buf.buffer.name.decode("utf-8"),
            "format": self._format.name,
            "capacity": self.capacity,
            "count": self.count,
            "resolution": self.resolution,
            "clock period": self.clock_period,
            "#-channels": self.channel_count,
            "reference_count": self.reference_count,
        }

        return config

    def __str__(self) -> str:
        out: str = "Tangy Buffer:\n"
        config = self.configuration()
        longest_key = max([len(k) for k in config.keys()])
        for k, v in config.items():
            out += f"{k.rjust(longest_key)} : {v}\n"
        return out

    @cython.ccall
    def bins_from_time(self, time: float) -> int:
        """ Convert amount of time to a number of time bins

        Args:
            time (float): Amount of time in seconds

        Returns:
            (int): number of bins

        """
        bins: u64n = _tangy.tangy_bins_from_time(self._ptr_buf, time)
        return bins

    @cython.ccall
    def oldest_time(self) -> float:
        return _tangy.tangy_oldest_time(self._ptr_buf)

    @cython.ccall
    def current_time(self) -> float:
        """ Returns the time of the most recent timetag
        Returns:
            (float): Most recent timetag as time
        """
        return _tangy.tangy_current_time(self._ptr_buf)

    @cython.ccall
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
        return _tangy.tangy_time_in_buffer(self._ptr_buf)

    @cython.ccall
    def time_range(self) -> Tuple[float, float]:

        begin: float = self.oldest_time()
        end: float = self.current_time()

        return (begin, end)

    @property
    def begin(self) -> int:
        """ Index of first record in buffer
        Returns:
            (int): Index of first record in buffer
        """
        count: u64n = self.count
        capacity: u64n = self.capacity

        start: u64n = 0

        if count > capacity:
            start = count - capacity

        return start

    @property
    def end(self) -> int:
        """ Index of last record in buffer
        Returns:
            (int): Index of last record in buffer
        """
        return self.count - 1

    @cython.cfunc
    def slice_from_pointers(self, length: u64n, channels: ndarray(u8n),
                            timestamps: ndarray(u64n) = None, clocks: ndarray(u64n) = None,
                            deltas: ndarray(u64n) = None) -> _tangy.tangy_field_ptrs:

        assert length > 0, "slice length must be non zero"
        slice: _tangy.tangy_field_ptrs
        ch: u8[:] = channels

        if self._buf.format == _tangy.buffer_format.STANDARD:
            assert timestamps is not None, "Must supply timestamps"
            slice.standard.length = length
            slice.standard.channel = cython.address(ch[0])
            ts: u64[:] = timestamps
            slice.standard.timestamp = cython.address(ts[0])
            return slice

        if self._buf.format == _tangy.buffer_format.CLOCKED:
            assert clocks is not None, "Must supply clocks"
            assert deltas is not None, "Must supply deltas"
            slice.clocked.length = length
            slice.clocked.channels = cython.address(ch[0])
            cl: u64[:] = clocks
            dt: u64[:] = deltas
            slice.clocked.clocks = cython.address(cl[0])
            slice.clocked.deltas = cython.address(dt[0])
            return slice

    @cython.ccall
    def pull(self, start: u64n, stop: u64n):
        total: u64n = stop - start

        slice: _tangy.tangy_field_ptrs
        channels: u8n[:] = zeros(total, dtype=u8n)

        if self._buf.format == _tangy.buffer_format.STANDARD:
            timetags: u64n[:] = zeros(total, dtype=u64n)
            slice = self.slice_from_pointers(
                total, channels, timestamps=timetags, clocks=None, deltas=None)
            count_pull: u64n = _tangy.tangy_buffer_slice(
                self._ptr_buf, cython.address(slice), start, stop)

            assert total == count_pull, "Did not find correct number of records"

            return (channels, timetags)

        if self._buf.format == _tangy.buffer_format.CLOCKED:
            clocks: u64n[:] = zeros(total, dtype=u64n)
            deltas: u64n[:] = zeros(total, dtype=u64n)
            slice = self.slice_from_pointers(
                total, channels, timestamps=None, clocks=clocks, deltas=deltas)
            count_pull: u64n = _tangy.tangy_buffer_slice(
                self._ptr_buf, cython.address(slice), start, stop)

            assert total == count_pull, "Did not find correct number of records"

            return (channels, (clocks, deltas))

    @cython.ccall
    def push(self, channels: ndarray(u8n),
             timetags: Union[ndarray(u64n),
                             Tuple[ndarray(u64n), ndarray(u64n)]]):

        total: u64n = len(channels)

        start: u64n = self.count
        stop: u64n = start + total

        count_pushed: u64n = 0
        slice: _tangy.tangy_field_ptrs
        if self._buf.format == _tangy.buffer_format.STANDARD:
            slice = self.slice_from_pointers(
                total, channels, timestamps=timetags, clocks=None, deltas=None)
            assert slice.standard.length > 0, "No timetags to push"
            count_pushed = _tangy.tangy_buffer_push(
                self._ptr_buf, cython.address(slice), start, stop)

        if self._buf.format == _tangy.buffer_format.CLOCKED:
            slice = self.slice_from_pointers(
                total, channels, timestamps=None, clocks=timetags[0], deltas=timetags[1])
            assert slice.clocked.length > 0, "No timetags to push"
            count_pushed = _tangy.tangy_buffer_push(
                self._ptr_buf, cython.address(slice), start, stop)

        return count_pushed

    @cython.ccall
    def clear(self):
        _tangy.tangy_clear_buffer(self._ptr_buf)

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
        bins: u64n = self.bins_from_time(time)
        index: u64n = _tangy.tangy_lower_bound(self._ptr_buf, bins)
        return index

    @cython.ccall
    def timetags(self,
                 channels: Optional[Union[int, List[int]]] = None,
                 start: Optional[int] = None,
                 stop: Optional[int] = None) -> List[Tuple[int, NDArray]]:
        """ Get the timetags for selected channels
        Args:
            channels (Optional[Union[int, List[int]]]): Channels to get
                timetags for, can be either a single channel (int) or many
                (list of ints). If no channels are set and value left as None,
                all channels will gathered.
            start (Optional[int]): Position in buffer to start collecting from,
                if None the first valid position in the buffer will be used.
            stop (Optional[int]): Position in the buffer to collect timetags
                up to, if left as None the end of the buffer will be used.

        Returns:
            (List[Tuple[int, NDArray]]): a list of tuples, each list element
                contains the channel index and ndarray of timetags for that
                channel

        Examples:
            Get all timetags for channels 0 and 1
            >>> timetags = buffer.timetags(channels=[0, 1])

            Get the first 10 timetags on channel 2
            >>> start = buffer.begin
            >>> stop = start + 10
            >>> channel_target = 2
            >>> timetags_channel_2 = timetags(channels=channel_target,
                                              start=start,
                                              stop=stop)

            Get the last 100 timetags on channel 4
            >>> stop = buffer.end
            >>> stop = stop - 100
            >>> timetags_channel_2 = timetags(channels=4,
                                              start=start,
                                              stop=stop)
        """

        if start is None:
            start = self.begin

        if stop is None:
            stop = self.end

        if channels is None:
            channels = [c for c in range(self.channel_count)]

        if type(channels) is int:
            channels = [channels]

        tag_arrays = []
        if self._buf.format == _tangy.buffer_format.STANDARD:
            (ch, tt) = self[start:stop]
            for c in channels:
                channel_mask = ch == c
                if channel_mask.sum() != 0:
                    tag_arrays.append((c, tt[channel_mask]))

        if self._buf.format == _tangy.buffer_format.CLOCKED:
            (ch, (cl, dt)) = self[start:stop]
            for c in channels:
                channel_mask = ch == c
                if channel_mask != 0:
                    tag_arrays.append(
                        (c, (cl[channel_mask], dt[channel_mask])))

        return tag_arrays

    @cython.ccall
    def singles(self, read_time: Optional[float] = None,
                start: Optional[int] = None,
                stop: Optional[int] = None) -> Tuple[int, List[int]]:
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

        counters: u64n[:] = zeros(self.channel_count, dtype=u64n)
        counters_view: u64[::1] = counters

        if read_time:
            time_in_buffer = self.time_in_buffer()
            current_time: f64n = self.current_time()
            if read_time >= time_in_buffer:
                # TODO: really should have a warning here
                start: u64n = self.begin
            else:
                read_time: f64n = current_time - read_time
                start: u64n = self.lower_bound(read_time)

        if stop is None:
            # stop: u64n = self.count - 1
            stop: u64n = self.end

        total: u64n = 0
        total = _tangy.tangy_singles(self._ptr_buf, start, stop,
                                     cython.address(counters_view[0]))
        return (total, counters)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.ccall
    def coincidence_count(self, read_time: float, window: float,
                          channels: List[int],
                          delays: Optional[List[float]] = None) -> int:
        """ Count coincidences

        Counts the coincidences for the chosen channels over the specified read
            time provided the timetags have a distance between them less than
            the window. Optionally delays can be applied to each channel.The
            read time is taken as time from the most recent timetag in the
            buffer, e.g. a read time of 1s in a buffer containing 100s will
            give a result from the 99th second to the 100th.

        Args:
            read_time (float): time to integrate over
            window (float): maximum distance between timetags allowed
            channels (List[int]): channels to find coincidences between
            delays (Optional[List[float]] = None,): delays for each channel

        Returns:
            (int): Number of coincidences found

        """

        _n_channels = len(channels)

        assert _n_channels <= self.channel_count, "More channels than available in buffer"

        assert max(channels) <= self.channel_count, \
            f"Requested channel {max(channels)} when maximum channel available in {self.n_channels}"

        _channels: ndarray(u8n) = array(channels, dtype=u8n)
        _channels_view: cython.uchar[::1] = _channels

        if delays is None:
            delays: List[float] = [0 for i in range(_n_channels)]

        _delays_view: cython.double[::1] = array(delays, dtype=f64n)

        count = 0
        count = _tangy.tangy_coincidence_count(self._ptr_buf,
                                               _n_channels,
                                               cython.address(
                                                   _channels_view[0]),
                                               cython.address(_delays_view[0]),
                                               window,
                                               read_time)

        return count

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.ccall
    def coincidence_collect(self, read_time: float, window: float,
                            channels: List[int],
                            delays: Optional[List[float]] = None) -> Optional[Records]:
        """ Collect coincident timetags

        Collects the timetags in coincdience for the chosen channels over the
            specified read time provided the timetags have a distance between
            them less than the window. Optionally delays can be applied to each
            channel.The read time is taken as time from the most recent timetag
            in the buffer, e.g. a read time of 1s in a buffer containing 100s
            will give a result from the 99th second to the 100th.

        Args:
            read_time (float): time to integrate over
            window (float): maximum distance between timetags allowed
            channels (List[int]): channels to find coincidences between
            delays (Optional[List[float]] = None,): delays for each channel

        Returns:
            (Records): Records found in coincidence

        """

        _n_channels = len(channels)

        assert _n_channels <= self.channel_count, "More channels than available in buffer"

        assert max(channels) <= self.channel_count, \
            f"Requested channel {max(channels)} when maximum channel available in {self.n_channels}"

        _channels: ndarray(u8n) = array(channels, dtype=u8n)
        _channels_view: cython.uchar[::1] = _channels

        if delays is None:
            delays: List[float] = [0 for i in range(_n_channels)]

        _delays_view: cython.double[::1] = array(delays, dtype=f64n)

        count = 0
        count = _tangy.tangy_coincidence_collect(self._ptr_buf,
                                                 _n_channels,
                                                 cython.address(
                                                     _channels_view[0]),
                                                 cython.address(
                                                     _delays_view[0]),
                                                 window,
                                                 read_time,
                                                 cython.address(self._buf.records))

        if count == 0:
            warnings.warn("No coincidences found")
            return None

        slice: _tangy.tangy_field_ptrs
        n_records: u64n = count * _n_channels

        if self._buf.format == _tangy.buffer_format.STANDARD:
            timetags: u64n[:] = zeros(n_records, dtype=u64n)
            slice = self.slice_from_pointers(
                n_records, _channels, timestamps=timetags, clocks=None, deltas=None)

        if self._buf.format == _tangy.buffer_format.CLOCKED:
            clocks: u64n[:] = zeros(n_records, dtype=u64n)
            deltas: u64n[:] = zeros(n_records, dtype=u64n)
            slice = self.slice_from_pointers(
                n_records, _channels, timestamps=None, clocks=clocks, deltas=deltas)

        _tangy.tangy_records_copy(self._buf.format,
                                  cython.address(self._buf.records),
                                  cython.address(slice))

        if self._buf.format == _tangy.buffer_format.STANDARD:
            # return count, (channels, timetags)
            # return RecordsStandard(count, self.resolution, _channels, timetags)
            return Records(count, self.resolution, self.clock_period,
                           _channels, timetags)

        if self._buf.format == _tangy.buffer_format.CLOCKED:
            # return count, (channels, (clocks, deltas))
            # return RecordsClocked(count, self.clock_period, self.resolution,
            #                       _channels, clocks, deltas)
            return Records(count, self.resolution, self.clock_period,
                           _channels, (clocks, deltas))

    @cython.ccall
    def timetrace(self, channels: Union[int, List[int]], read_time: float,
                  resolution: float = 10.0):
        """ Time trace of buffer for chosen channels and read time

        Produces an array of count rates accumulated for the chosen channels
            over the read time specified. The read time is taken as time from
            the most recent timetag in the buffer, e.g. a read time of 1s in a
            buffer containing 100s will give a result from the 99th second to the
            100th.

        Args:
            channels (List[int]): Channels to count timetags of
            read_time (float): Amount of time to measure over, In seconds
            resolution (float = 10.0): Size of bins in seconds

        Returns:
            (ndarray): intensities

        """
        n_channels: u64n = 1

        channels_arr: u8n[:]

        if isinstance(channels, (list)):
            n_channels = len(channels)
            channels_arr = zeros(n_channels, dtype=u8n)
            channels_arr = asarray(channels, dtype=u8n)
        elif isinstance(channels, (int)):
            channels_arr = zeros(n_channels, dtype=u8n)
            channels_arr[0] = channels

        # print(n_channels, channels_arr)

        # channels_view: cython.uchar[::1] = asarray(channels, dtype=u8n)
        channels_view: cython.uchar[::1] = channels_arr

        bin_width: u64n = round(resolution / self.resolution)
        start: u64 = self.lower_bound(self.current_time() - read_time)
        stop: u64 = self.count
        length: u64 = round(read_time / resolution)

        intensities: u64n[:] = zeros(length - 1, dtype=u64n)
        intensities_view: u64[:] = intensities

        count: u64 = _tangy.tangy_timetrace(self._ptr_buf, start, stop,
                                            bin_width,
                                            cython.address(channels_view[0]),
                                            n_channels,
                                            length,
                                            cython.address(intensities_view[0]))

        assert count > 0, "No data found"
        return intensities

    @cython.ccall
    def relative_delay(self, channel_a: int, channel_b: int, read_time: float,
                       resolution: float = 1e-9,
                       window: Optional[float] = None) -> delay_result:
        """ Relative delay between two channels

        Args:
            channel_a (int): First channel
            channel_b (int): Second channel
            read_time (float,): Time to integrate over
            resolution (float = 1e-9,): Resolution of bins
            window (Optional[float] = None): Correlation window

        Returns:
            (delay_result): Dataclass containing histogram data and fitting results
        """

        # PERF: replace time trace with singles()
        # NOTE: decay (tau) is ≈ 1 / singles(channelX), so we have:
        #   tau_a = 1 / singles(channel_a) and tau_b = 1 / singles(channel_b)
        # resolution_trace: f64n = 1.0
        # trace: u64n[:] = self.timetrace(
        #     [channel_a, channel_b], read_time, resolution_trace)

        (_, counts_singles) = self.singles(read_time)
        intensity_average = (
            counts_singles[channel_a] + counts_singles[channel_b]) / read_time

        # intensity_average = mean(trace) / resolution_trace

        correlation_window: f64n = window
        if window is None:
            # NOTE: This should then be...
            # correlation_window =
            #   (1 / singles(channel_a)) + (1 / singles(channel_b))
            correlation_window = 2 / intensity_average ** 2

        length: u64n = round(correlation_window / resolution) - 1
        correlation_window = correlation_window / self.resolution

        resolution_measurment: u64n = u64n(correlation_window / f64n(length))

        correlation_window = length * resolution_measurment
        length *= 2

        intensity_array: u64n[:] = zeros(length, dtype=u64n)
        intensity_view: u64[:] = intensity_array

        start: u64 = self.lower_bound(self.current_time() - read_time)
        stop: u64 = self.count

        _tangy.tangy_relative_delay(self._ptr_buf, start, stop,
                                    u64n(correlation_window),
                                    resolution_measurment,
                                    channel_a, channel_b, length,
                                    cython.address(intensity_view[0]))

        times = (arange(length) - (length // 2)) * resolution
        max_idx = intensity_array.argmax()
        t0 = times[max_idx]

        tau = 2 / intensity_average
        max_intensity = intensity_array.max()

        guess = [tau, tau, t0, max_intensity]

        [opt, cov] = curve_fit(double_decay, times, intensity_array, p0=guess)
        hist_fit = double_decay(times, *opt)

        # central_delay = t0

        result = delay_result(
            times=times,
            intensities=intensity_array,
            fit=hist_fit,
            tau1=opt[0],
            tau2=opt[1],
            t0=opt[2],
            central_delay=opt[2],
            max_intensity=opt[3])

        return result

    @cython.ccall
    def joint_delay_histogram(self, signal: int, idler: int, channels: List[int],
                              read_time: float, radius: float,
                              delays: Optional[List[float]] = None,
                              clock: Optional[int] = None,
                              bin_width: int = 1,
                              centre: bool = True) -> JointHistogram:
        """ 2-D histogram of delays between channels

        Histograms relative delays of channsl found to be in coincdience for
            over the specified read time provided the timetags have a distance
            between them less than the window. Optionally delays can be applied
            to each channel.The read time is taken as time from the most recent
            timetag in the buffer, e.g. a read time of 1s in a buffer containing
            100s will give a result from the 99th second to the 100th. Can be
            used to produce a joint spectral intensity if the conversion from
            time to wavelength (frequency) is known.

        Args:
            signal (int): channel of signal photon
            idler (int): channel of idler photon
            channels (List[int],): channels to test for coincidence, must contain
                signal, idler and optionally a clock channel
            read_time (float): time to integrate over
            radius (float,): maximum distance between timetags allowed
            delays (Optional[List[float]] = None,): delays for each channel
            clock (Optional[int] = None,): Optional clock channel
            bin_width (int = 1,): Width of bins in histogram
            centre (bool = True): Whether or not to centre the histogram

        Returns:
            (JointHistogram): Joint delay histogram and marginal distributions

        """

        _n_channels = len(channels)

        assert _n_channels <= self.channel_count, "More channels than available in buffer"

        assert max(channels) <= self.channel_count, \
            f"Requested channel {max(channels)} when maximum channel available in {self.n_channels}"

        _channels: ndarray(u8n) = array(channels, dtype=u8n)
        _channels_view: cython.uchar[::1] = _channels

        if delays is None:
            delays: List[float] = [0 for i in range(_n_channels)]

        _delays_view: cython.double[::1] = array(delays, dtype=f64n)

        if self._format == TangyBufferType.Standard:
            assert clock is not None, "Clock must be set for standard formats"
        else:
            clock = 0

        radius_bins: u64n = round(radius / self.resolution)
        temporal_window: u64n = radius_bins + radius_bins
        n_bins: u64n = temporal_window * temporal_window
        histogram: u64n[:] = zeros(u64n(n_bins), dtype=u64n)
        histogram_view: u64[:] = histogram

        count: u64n = 0
        count = _tangy.tangy_joint_delay_histogram(self._ptr_buf,
                                                   clock, signal, idler,
                                                   _n_channels,
                                                   cython.address(
                                                       _channels_view[0]),
                                                   cython.address(
                                                       _delays_view[0]),
                                                   radius,
                                                   read_time,
                                                   cython.address(histogram_view[0]))

        if count == 0:
            warn("No counts found, results will be empty")

        histogram = reshape(histogram, [temporal_window, temporal_window])

        temporal_window = temporal_window // bin_width
        central_bin = temporal_window // 2

        # TODO: this needs to go behind an if-guard
        # TODO: will need other marginal calculation, see "def extract_marginals"
        ((nr, nc), ms, mi, histogram) = bin_histogram(
            histogram, bin_width, bin_width)
        if centre:
            (ms, mi, histogram) = centre_histogram(central_bin, temporal_window,
                                                   mi, ms, histogram)

        axis = (arange(temporal_window) - radius_bins) * self.resolution
        return JointHistogram(radius_bins, temporal_window,
                              (bin_width, bin_width), histogram,
                              mi, ms, axis, axis)

    @cython.ccall
    def second_order_coherence(self, signal: int, idler: int, read_time: float,
                               radius: float, resolution: float,
                               delays: Optional[List[float]] = None):

        length: u64n = u64n(radius / resolution)
        correlation_window: f64n = radius / self.resolution

        resolution_hist: u64n = u64n(correlation_window / f64n(length))
        correlation_window = length * resolution_hist
        length *= 2

        intensities: u64n[:] = zeros(length, dtype=u64n)
        intensities_view: u64[:] = intensities

        times = (arange(length) - (length // 2)) * resolution

        if delays is None:
            start: u64 = self.lower_bound(self.current_time() - read_time)
            stop: u64 = self.count

            _tangy.tangy_second_order_coherence(
                self._ptr_buf, start, stop, correlation_window,
                resolution_hist, signal, idler,
                length, cython.address(intensities_view[0]))
            return (times, intensities)

        _delays_view: cython.double[::1] = array(delays, dtype=f64n)
        _tangy.tangy_second_order_coherence_delays(
            self._ptr_buf, read_time, correlation_window, resolution_hist,
            signal, idler, cython.address(_delays_view[0]),
            length, cython.address(intensities_view[0]))
        return (times, intensities)


ChannelConfig = Tuple[TangyBuffer, List[int], Optional[List[float]]]


@cython.cclass
class Measurement:

    def __init__(self,
                 channel_info: Union[ChannelConfig, List[ChannelConfig]]
                 ):

        if type(channel_info) is ChannelConfig:
            channel_info = [channel_info]

        buffers_count: int = len(channel_info)

        buffers = []
        channels = []
        delays = []

        pattern_count = 0

        for (buf, ch, d) in channel_info:
            buffers.append(buf)
            channels.append(ch)
            delays.append(d)
            pattern_count += len(channels)
    # TODO: what do I really want here?


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


@cython.cfunc
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
            value = i64n(val)
        elif tag_type == "tyFloat8":
            value = i64n(val).view("float64")
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

        # tag = {"idx": idx, "type": tag_type, "value": value}
        tag = {"type": tag_type, "value": value}
        tag_name = name.strip(b"\0").decode()
        if idx != -1:
            tag_name = f"{tag_name} {idx}"
        tags[tag_name] = tag

    return tags, offset + 48, tag_end_offset


# @cython.cfunc
# def ptu_read_into(buffer: TangyBufferT,
#                   file_handle: cython.pointer(FILE),
#                   status: cython.pointer(_tangy.READER_STATUS),
#                   n: u64n):
#     res: u64n = 0
#
#     if TangyBufferT is TangyBufferStandard:
#         res = _tangy.read_next_HH2_T2(buffer._ptr, file_handle, status, n)
#     elif TangyBufferT is TangyBufferClocked:
#         res = _tangy.read_next_HH2_T3(buffer._ptr, file_handle, status, n)
#
#     return res


@cython.cclass
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

    _tag_end: u64n
    _offset: u64n

    # _buffer_type: _tangy.BufferType
    _buffer: TangyBuffer

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
        glob_res: f64n = self._header["MeasDesc_GlobalResolution"]['value']
        sync_res: f64n = self._header["MeasDesc_Resolution"]['value']

        record_type = self._header["TTResultFormat_TTTRRecType"]["value"]
        key = _ptu_record_types_reversed[record_type].upper()

        if "T2" in key:
            resolution = sync_res
            clock_period = 1
            fmt = TangyBufferType.Standard
        elif "T3" in key:
            resolution = sync_res
            clock_period = glob_res
            fmt = TangyBufferType.Clocked

        self._buffer = TangyBuffer(
            name, resolution, clock_period, n_ch, length, fmt)

        return

    def __del__(self):
        fclose(self._c_file_handle)
        self._file_handle.close()

    # def __repr__(self):
    #     if _tangy.BufferType.Standard == self._buffer_type:
    #         return self._std_buffer.__repr__()
    #     if _tangy.BufferType.Clocked == self._buffer_type:
    #         return self._clk_buffer.__repr__()

    def buffer(self) -> TangyBuffer:
        """
        Acquire the buffer being written to

        Returns:
            TangyBuffer: Instance of buffer for the openend file. Where the \
                buffer is an instance of TangyBuffer (either TangyBufferStandard\
                or TangyBufferClocked).
        """

        return self._buffer

    @property
    def record_count(self):
        return self._status.record_count

    @property
    def header(self):
        return self._header

    def __len__(self):
        return len(self._buffer)

    @property
    def count(self):
        x: u64n = self._buffer.count
        return x

    @cython.ccall
    def read(self, n: u64n) -> int:
        """
        Read an amount of tags from the target file

        Args:
            n (int): Number of tags to read from the file

        Returns:
            (u64n): NUmber of records read

        """

        res: u64n = 0
        record_type = self._header["TTResultFormat_TTTRRecType"]["value"]

        if self._buffer._format == TangyBufferType.Standard:

            slice_standard: cython.pointer(_tangy.std_slice) = \
                cython.address(self._buffer._buf.slice.standard)

            if record_type == _ptu_record_types["PicoHarpT2"]:
                res = _tangy.srb_read_next_PH_T2(self._buffer._ptr_rb,
                                                 slice_standard,
                                                 self._c_file_handle,
                                                 self._status,
                                                 n)
                return res

            if record_type == _ptu_record_types["HydraHarp2T2"]:
                res = _tangy.srb_read_next_HH2_T2(self._buffer._ptr_rb,
                                                  slice_standard,
                                                  self._c_file_handle,
                                                  self._status,
                                                  n)
                return res

        if self._buffer._format == TangyBufferType.Clocked:
            slice_clocked: cython.pointer(_tangy.clk_slice) = \
                cython.address(self._buffer._buf.slice.clocked)

            if record_type == _ptu_record_types["PicoHarpT3"]:
                res = _tangy.srb_read_next_PH_T3(self._buffer._ptr_rb,
                                                 slice_clocked,
                                                 self._c_file_handle,
                                                 self._status,
                                                 n)
                return res

            if record_type == _ptu_record_types["HydraHarp2T3"]:
                res = _tangy.srb_read_next_HH2_T3(self._buffer._ptr_rb,
                                                  slice_clocked,
                                                  self._c_file_handle,
                                                  self._status,
                                                  n)
                return res
        return res


@cython.cclass
class QuToolsFile():
    """
    """

    _file_path: str
    _file_handle: object
    _c_file_handle = cython.declare(cython.pointer(FILE))

    _buffer: TangyBuffer
    _timetag_offset: u64

    def __init__(self, file_path: str, name: str, length: int = 1000):

        elems = file_path.split(".")
        if elems[-1] != "bin":
            raise NameError("File must have .bin extension")

        self._file_path = file_path
        self._file_handle = open(self._file_path, "rb")
        _file_no = self._file_handle.fileno()
        self._c_file_handle = fdopen(dup(_file_no), "rb".encode("ascii"))

        self._buffer = TangyBuffer(
            name, 1e-12, 1, 8, length, TangyBufferType.Standard)

        self._timetag_offset = _tangy.srb_read_header_qutools(
            self._buffer._ptr_rb, self._c_file_handle)
        return

    def __del__(self):
        fclose(self._c_file_handle)
        self._file_handle.close()

    def buffer(self) -> TangyBuffer:
        """
        Acquire the buffer being written to

        Returns:
            TangyBuffer: Instance of buffer for the openend file. Where the \
                buffer is an instance of TangyBuffer.
        """

        return self._buffer

    def __len__(self):
        return len(self._buffer)

    @property
    def count(self):
        x: u64n = self._buffer.count
        return x

    @cython.ccall
    def read(self, n: u64n) -> int:

        res: int = _tangy.srb_read_next_qutools(
            self._buffer._ptr_rb,
            cython.address(
                self._buffer._buf.slice.standard),
            self._c_file_handle,
            self._timetag_offset,
            n)

        return res


@cython.ccall
def buffer_list_update() -> dict:
    """
    Up-to-date list of available buffers

    Gets the list of available buffers from the Tangy configuration directory,
        for example, ```~/.config/Tangy/buffers``` on linux and
        ```C:\\Users\\user_name\\AppData\\Local\\PeterBarrow\\Tangy\\buffers```
        on Windows. For each buffer configuration file the existence of the
        associated buffer is checked, buffers that no longer exists have their
        corresponding configuration file removed. Upon completion this returns
        a dictionary containing the buffer name, buffer format and path to the
        configuration file.

    Returns:
        (dict): Dictionary of
            ```{"name": {"format": fmt, "path": "/path/to/config"}```

    """
    buffer_list_path = join(tangy_config_location(), "buffers")
    if not exists(buffer_list_path):
        makedirs(buffer_list_path)
    buffer_list = {}

    for file in listdir(buffer_list_path):
        if file.endswith(".json") or file.endswith(".JSON"):
            file_name = join(buffer_list_path, file)
            with open(file_name, "r") as f:
                config = {k.lower(): v for k, v in json.load(f).items()}
                keys = config.keys()
                if "name" not in keys:
                    continue
                if "format" not in keys:
                    continue
                buffer_list[config["name"]] = {
                    "format": config["format"],
                    "path": file_name
                }

    buffer_list_available = {}
    result: _tangy.shmem_result
    flag: u8 = 0
    for name, details in buffer_list.items():
        name_encoded = name.encode('utf-8')
        c_name: cython.p_char = name_encoded
        result = _tangy.shmem_exists(c_name, cython.address(flag))
        if result.Ok is False:
            remove(details["path"])
            continue
        if flag == 0:
            # buffer doesn't exist anymore so delete its json file
            remove(details["path"])

        # if we got here then the buffer exists, but we don't know about its
        # reference count, the reference count can also be higher than it should
        # if the last connection to that buffer crashed (no decrement)

        # name_stub_free = ""
        # if details["format"].lower() == "standard":
        #     name_stub_free = name.replace("std_", "")

        # if details["format"].lower() == "clocked":
        #     name_stub_free = name.replace("clk_", "")

        name_stub_free = "_".join(name.split("_")[1::])

        buffer_list_available[name_stub_free] = details

    return buffer_list_available


@cython.ccall
def buffer_list_append(buffer: TangyBuffer):
    """
    Adds the configuration of a buffer to the Tangy configuration directory

    Args:
        buffer (TangyBuffer): buffer with configuration to save
    """

    config = buffer.configuration()
    buffer_list_path = join(tangy_config_location(), "buffers")
    file_name = join(buffer_list_path, config["name"] + ".json")
    with open(file_name, "w") as file:
        json.dump(config, file, indent=4)


@cython.ccall
def buffer_list_delete_all():
    buffer_list = buffer_list_update()

    for name in buffer_list.keys():

        format = TangyBufferType.Standard
        if buffer_list[name]["format"] == "Clocked":
            format = TangyBufferType.Clocked

        buffer = TangyBuffer(name, format=format)
        buffer.reference_count = 0

    buffer_list_update()


@cython.ccall
def buffer_list_show():
    tangy_config_path = tangy_config_location()
    buffer_list_path = join(tangy_config_path, "buffers")
    buffer_list = buffer_list_update()
    out = f"Tangy configuration: {tangy_config_path}\n"
    out += f"Buffer configurations: {buffer_list_path}\n"
    out += "Available Tangy buffers\n"
    for name, details in buffer_list.items():
        f = details["format"]
        p = details["path"]
        out += f"{name} : \n\tFormat : {f}\n\tPath: {p}\n"

    print(out)
