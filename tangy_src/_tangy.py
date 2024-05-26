# import datetime
import cython
# from cython.cimports.cython import view
from cython.cimports import _tangy as _tangy

import mmap
from os import dup, listdir, remove, makedirs
from os.path import getsize, join, exists
import json
# import time
from scipy.optimize import curve_fit
from numpy import mean, where, exp, roll
# from numpy import sum as npsum
from numpy import round as npround
from numpy import abs as nabs
from numpy import histogram as nphist
from numpy import arange, array, ndarray, asarray, zeros, frombuffer
from numpy import uint8 as u8n
from numpy import uint64 as u64n
from numpy import int64 as i64n
from numpy import float64 as f64n
from cython.cimports.libc.stdlib import malloc
from cython.cimports.libc.stdio import FILE, fdopen, fclose

from cython.cimports.libc.stdint import uint8_t as u8
# from cython.cimports.libc.stdint import uint32_t as u32
from cython.cimports.libc.stdint import uint64_t as u64
from cython.cimports.libc.stdint import int64_t as i64
import struct
# from cython.cimports.numpy import npu64n_t

# import numpy.typing as npt
from typing import List, Tuple, Optional, Union
# from enum import Enum
from platformdirs import user_config_dir


# __all__ = ["RecordsStandard", "RecordsClocked", "TagBuffer", "singles",
#            "timetrace", "find_zero_delay", "zero_delay_result", "Coincidences",
#            "JointDelayHistogram", "JointHistogram", "PTUFile"]

TimeTag = cython.fused_type(_tangy.standard, _tangy.clocked)
Resolution = cython.fused_type(_tangy.std_res, _tangy.clk_res)
# TangyBuffer = cython.fused_type(_tangy.std_buffer, _tangy.clk_buffer)
std_buf_ptr = cython.typedef(cython.pointer(_tangy.std_buffer))
clk_buf_ptr = cython.typedef(cython.pointer(_tangy.clk_buffer))
TangyBufferPtr = cython.fused_type(std_buf_ptr, clk_buf_ptr)
_Resolution = cython.fused_type(float, Tuple[float, float])


# @cython.cfunc
# def into_std_buffer(void_ptr: cython.pointer(cython.void)) -> std_buf_ptr:
#     return cython.cast(std_buf_ptr, void_ptr)
#
#
# @cython.cfunc
# def into_clk_buffer(void_ptr: cython.pointer(cython.void)) -> clk_buf_ptr:
#     return cython.cast(clk_buf_ptr, void_ptr)


# @cython.cfunc
# def into_tangy_buffer(void_ptr: cython.pointer(cython.void),
#                       choice: _tangy.BufferType):
#
#     if choice is _tangy.BufferType.Standard:
#         return into_std_buffer(void_ptr)
#
#     if choice is _tangy.BufferType.Clocked:
#         return into_clk_buffer(void_ptr)


@cython.cfunc
def to_time(tag: TimeTag, resolution: Resolution) -> cython.double:

    if (TimeTag is _tangy.standard) and (Resolution is _tangy.std_res):
        return _tangy.std_to_time(tag, resolution)

    elif (TimeTag is _tangy.clocked) and (Resolution is _tangy.clk_res):
        return _tangy.clk_to_time(tag, resolution)


@cython.cfunc
def timetag_at(ptr: TangyBufferPtr, idx: u64n):
    if TangyBufferPtr is std_buf_ptr:
        return _tangy.std_record_at(ptr, idx)
    elif TangyBufferPtr is clk_buf_ptr:
        return _tangy.clk_record_at(ptr, idx)


# @cython.cfunc
# def time_at_index(buf_ptr: cython.pointer(cython.void),
#                   buf_type: _tangy.BufferType, index: u64n) -> float:
#
#     if buf_type is _tangy.BufferType.Standard:
#         ptr_std = into_std_buffer(buf_ptr)
#         rec_std: _tangy.standard = timetag_at(ptr_std, index)
#         return to_time[_tangy.standard, _tangy.std_res](rec_std, ptr_std[0].resolution[0])
#
#     elif buf_type is _tangy.BufferType.Clocked:
#         ptr_clk = into_clk_buffer(buf_ptr)
#         rec_clk: _tangy.clocked = timetag_at(ptr_clk, index)
#         print(ptr_clk.resolution[0].coarse, ptr_clk.resolution[0].fine)
#         return to_time[_tangy.clocked, _tangy.clk_res](rec_clk, ptr_clk[0].resolution[0])


@cython.cfunc
def buffer_type(ptr: TangyBufferPtr):
    if TangyBufferPtr is cython.pointer(_tangy.std_buffer):
        print("found standard")
    if TangyBufferPtr is cython.pointer(_tangy.clk_buffer):
        print("found clocked")


@cython.ccall
def tangy_config_location() -> str:
    appname = "Tangy"
    appauthor = "PeterBarrow"

    config_path = user_config_dir(appname, appauthor)
    if not exists(config_path):
        makedirs(config_path)
    return config_path


@cython.ccall
def buffer_list_update() -> dict:
    """
    Up-to-date list of available buffers

    Gets the list of available buffers from the Tangy configuration directory
        [```~/.config/Tangy/buffers``` on linux and
        ```C:\\Users\\user_name\\AppData\\Local\\PeterBarrow\\Tangy\\buffers```
        on Windows]. For each buffer configuration file the existence of the
        associated buffer is checked, buffers that no longer exists have their
        corresponding configuration file removed. Upon completion this returns
        a dictionary containing the buffer name, buffer format and path to the
        configuration file.

    Returns:
        (dict): Dictionary of {"name": {"format": fmt, "path": "/path/to/config"}

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
    result: _tangy.tbResult
    flag: u8 = 0
    for name, details in buffer_list.items():
        name_encoded = name.encode('utf-8')
        c_name: cython.p_char = name_encoded
        result = _tangy.shmem_exists(c_name, cython.address(flag))
        if result.Ok is False:
            continue
        if flag == 0:
            # buffer doesn't exist anymore so delete its json file
            remove(details["path"])
            continue

        # if we got here then the buffer exists, but we don't know about its
        # reference count, the reference count can also be higher than it should
        # if the last connection to that buffer crashed (no decrement)

        name_stub_free = ""
        # if details["format"].lower() == "standard":
        if details["format"] == 0:
            name_stub_free = name.replace("std_", "")

        # if details["format"].lower() == "clocked":
        if details["format"] == 1:
            name_stub_free = name.replace("clk_", "")

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
def buffer_list_contains():
    ...


@cython.ccall
def buffer_list_delete_all():
    buffer_list = buffer_list_update()

    for name in buffer_list.keys():
        format = buffer_list[name]["format"]
        if format == 0:
            buffer = TangyBufferStandard(name)
            buffer._buffer.reference_count = 0
            buffer.__del__()

        if format == 1:
            buffer = TangyBufferClocked(name)
            buffer.reference_count = 0
            buffer.__del__()

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
        out += f"{name} : \n\tFormat : {f}\n\tPath: {p}"

    print(out)


@cython.dataclasses.dataclass(frozen=True)
class RecordsStandard:
    """Container for Standard format Timetags

    Args:
        count (u64n):
        resolution (float):
        channels (ndarray(u8n)):
        timetags (ndarray(u64n)):
    """
    count: u64n = cython.dataclasses.field()
    resolution: float = cython.dataclasses.field()
    channels: ndarray(u8n) = cython.dataclasses.field()
    timetags: ndarray(u64n) = cython.dataclasses.field()

    @cython.ccall
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def asTime(self):
        resolution: cython.typeof(self.resolution) = self.resolution

        timetag_view: cython.ulonglong[:] = self.timetags

        # count: cython.Py_ssize_t = len(self)
        if 1 == self.count:
            return _tangy.std_time_from_bins(resolution, timetag_view[0])

        result: f64n[:] = zeros(self.count, dtype=f64n)
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
        count (u64n):
        resolution_coarse (float):
        resolution_fine (float):
        channels (ndarray(u8n)):
        clocks (ndarray(u64n)):
        deltas (ndarray(u64n)):
    """
    count: u64n = cython.dataclasses.field()
    resolution_coarse: float = cython.dataclasses.field()
    resolution_fine: float = cython.dataclasses.field()
    channels: ndarray(u8n) = cython.dataclasses.field()
    clocks: ndarray(u64n) = cython.dataclasses.field()
    deltas: ndarray(u64n) = cython.dataclasses.field()

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

        result: f64n[:] = zeros(self.count, dtype=f64n)
        result_view: cython.double[:] = result
        i: cython.Py_ssize_t
        for i in range(self.count):
            record.timestamp.clock = clocks_view[i]
            record.timestamp.delta = deltas_view[i]
            result_view[i] = _tangy.clk_to_time(record, resolution)
        return result

    def __len__(self) -> cython.Py_ssize_t:
        return len(self.channels)


Record = cython.fused_type(_tangy.standard, _tangy.clocked)

_Buffer = cython.union(
    standard=_tangy.std_buffer,
    clocked=_tangy.clk_buffer)

_Buffer_Ptr = cython.union(
    standard=cython.pointer(_tangy.std_buffer),
    clocked=cython.pointer(_tangy.clk_buffer))

# StandardData = Tuple[ndarray(u8n), ndarray(u64n)]
# ClockedData = Tuple[ndarray(u8n), Tuple[ndarray(u64n), ndarray(u64n)]]
# TagData = Union[StandardData, ClockedData]


def double_decay(time, tau1, tau2, t0, max_intensity):
    tau = where(time < t0, tau1, tau2)
    decay = max_intensity * exp(-nabs(time - t0) / tau)
    return decay


@cython.dataclasses.dataclass(frozen=True)
class delay_result:
    # TODO: add a "central_delay" field
    times: ndarray(f64n) = cython.dataclasses.field()
    intensities: ndarray(u64n) = cython.dataclasses.field()
    fit: ndarray(f64n) = cython.dataclasses.field()
    tau1: cython.double = cython.dataclasses.field()
    tau2: cython.double = cython.dataclasses.field()
    t0: cython.double = cython.dataclasses.field()
    central_delay: cython.double = cython.dataclasses.field()
    max_intensity: cython.double = cython.dataclasses.field()


_Coinc_Measurement = cython.union(
    standard=cython.pointer(_tangy.std_cc_measurement),
    clocked=cython.pointer(_tangy.clk_cc_measurement))


@cython.cclass
class TangyBuffer:
    """Interface to underlying ring buffer

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (float): Resolution of timetags in seconds. A single float
            for the "standard timetags". A pair of floats for "clocked timetags"
            with a "coarse" and "fine" timing structure. Unused if connecting.
            In seconds.
        n_channels (int): Number of channels
        length (int): Length of buffer to create.
        Unused if connecting.

    Attributes:
        name (str): Name of buffer
        file_descriptor (int): File descriptor of underlying ring buffer
            capacity (int): Size of buffer
        resolution (Union[float, Tuple[float, float]]): Single float for
            a buffer of ``standard timetags`` or a pair of floats for buffers of
            ``clocked timetags`` (coarse resolution, fine resolution).
            Resolutions are in seconds.
        count (int): Number of elements that have been written to the buffer
        index_of_reference (int): On/off marker
        n_channels (int): Number of channels the buffer can contain

    Note:
        If connecting to an existing buffer the resolution, n_channels and
        length arguments will be ignored even if supplied.

    Note:
        For buffers using the clocked timetag format the resolution must be
            specified as a tuple in the form (coarse resolution, fine
            resolution). As an example a clock signal from an 80Mhz TiSapphire
            laser and a fine resolution on-board the time timetagger would
            give: ``resolution = (12.5e-9, 1e-12)``

    Examples:
        Creation of a TangyBuffer object for both the ``Standard`` and
        ``Clocked`` timetag formats that can hold 1,000,000 timetags for a
        device with 4 channels. The method to connect to these buffers is also
        shown. This method of creating new buffers and connecting to existing
        ones allows the user to hold on to and continously read timetags from
        a device in one process and then connect to that buffer in another to
        perform analysis on the current data.
        === "Buffer in ``Standard`` format"
            ```python
            # Here we will create a buffer called 'standard' (imaginitive)
            # that will only except timetags in the ``Standard`` format, this is
            # selected by only supplying a single value for the resolution
            standard_buffer = tangy.TangyBuffer("standard", 1e-9, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            standard_buffer_connection = tangy.TangyBuffer("standard")
            ```

        === "Buffer in ``Clocked`` format"
            ```python
            # Here we will create a buffer called 'clocked' (imaginitive)
            # that will only except timetags in the ``Clocked`` format, this is
            # selected by supplying a pair of values for the resolution
            resolution = (12.5e-9, 1e-12) # 80Mhz Clock and 1ps fine resolution
            clocked_buffer = tangy.TangyBuffer("clocked", resolution, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            clocked_buffer_connection = tangy.TangyBuffer("clocked")
            ```
    """
    _name = cython.declare(bytes)
    _vptr: cython.pointer(cython.void)
    _type: _tangy.BufferType

#     def __init__(self, name: str,
#                  resolution: Optional(Union[float, Tuple[float, float]]) = 1e-12,
#                  length: int = 10_000_000,
#                  n_channels: int = 8):
#
#         if type(resolution) is float:
#             super(self, TangyBufferStandard).__init__(name, resolution, length, n_channels)
#
#         elif type(resolution) is Tuple[float, float]:
#             super(self, TangyBufferClocked).__init__(name, resolution, length, n_channels)

    @classmethod
    def make_new_standard(cls, name: str, resolution: float,
                          length: int, n_channels: int):
        return TangyBufferStandard(name, resolution, length, n_channels)

    @classmethod
    def make_new_clocked(cls, name: str, resolution: Tuple[float, float],
                         length: int, n_channels: int):
        return TangyBufferClocked(name, resolution, length, n_channels)

    def __del__(self):
        raise NotImplementedError

    def configuration(self) -> dict:
        buffer_type = 0
        if self._type == _tangy.BufferType.Clocked:
            buffer_type = 1

        config = {
            "name": self.name.decode("ascii"),
            "format": buffer_type,  # TODO: Enum module should be used so we can give this a name
            "capacity": self.capacity,
            "count": self.count,
            "resolution": self.resolution,
            "reference_count": self.reference_count,
            "n_channels": self.n_channels,
        }
        return config

    def __repr__(self) -> str:
        out: str = "Tangy Buffer:\n"
        config = self.configuration()
        longest_key = max([len(k) for k in config.keys()])
        for k, v in config.items():
            out += f"{k.rjust(longest_key)} : {v}\n"
        return out

    def __len__(self):
        return self.capacity

    def __call__(self, time: float) -> int:
        return self._call(time)

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

    @property
    def end(self) -> int:
        """doc"""
        return self.count - 1

    @property
    def begin(self) -> int:
        """doc"""
        return self.oldest_index()

    @cython.boundscheck(False)
    @cython.wraparound(False)
    def __getitem__(self, key):
        return self._get(key)

    @cython.ccall
    def _get(self, key):
        raise NotImplementedError

    @cython.ccall
    def oldest_index(self) -> int:
        raise NotImplementedError

    @cython.ccall
    def _make_slice(self, key):
        start: int
        stop: int
        step: int = 1

        if type(key) is slice:
            # oldest = self.begin

            dist: int = abs(abs(key.stop) - abs(key.start))
            if (key.start > self.capacity) or (key.stop > self.capacity):
                if dist > self.capacity:
                    raise IndexError("out of range")
                start = key.start
                stop = key.stop
                return (start, stop, step)

            # if key.start < self.begin:
            #     start = oldest + self.begin
            if key.start < 0:
                start = (self.count + key.start - 1) % self.capacity
                stop = start + dist + 1
            else:
                start = key.start
                if start < self.begin:
                    start += self.begin
                start = (start % self.capacity)
                # stop = start + dist + 1
                stop = key.stop
                if stop < self.begin:
                    stop += self.begin
                stop = (stop % self.capacity) + 1

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

        return (start, stop, step)

    @cython.ccall
    def push(self, channels: ndarray(u8n), timetags):
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError

    @property
    def file_descriptor(self):
        raise NotImplementedError

    @property
    def capacity(self) -> int:
        raise NotImplementedError

    @property
    def resolution(self):
        raise NotImplementedError

    @resolution.setter
    def resolution(self, resolution):
        raise NotImplementedError

    @property
    def count(self) -> int:
        raise NotImplementedError

    @property
    def index_of_reference(self) -> int:
        raise NotImplementedError

    @property
    def reference_count(self) -> int:
        raise NotImplementedError

    @property
    def n_channels(self) -> int:
        raise NotImplementedError

    @cython.ccall
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
        raise NotImplementedError

    @cython.ccall
    def time_range(self) -> Tuple[float, float]:
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError


@cython.cclass
class TangyBufferStandard(TangyBuffer):
    """Interface to underlying ring buffer

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (float): Resolution of timetags in seconds. A single float
            for the "standard timetags". A pair of floats for "clocked timetags"
            with a "coarse" and "fine" timing structure. Unused if connecting.
            In seconds.
        n_channels (int): Number of channels
        length (int): Length of buffer to create.
        Unused if connecting.

    Attributes:
        name (str): Name of buffer
        file_descriptor (int): File descriptor of underlying ring buffer
            capacity (int): Size of buffer
        resolution (Union[float, Tuple[float, float]]): Single float for
            a buffer of ``standard timetags`` or a pair of floats for buffers of
            ``clocked timetags`` (coarse resolution, fine resolution).
            Resolutions are in seconds.
        count (int): Number of elements that have been written to the buffer
        index_of_reference (int): On/off marker
        n_channels (int): Number of channels the buffer can contain

    Note:
        If connecting to an existing buffer the resolution, n_channels and
        length arguments will be ignored even if supplied.

    Note:
        For buffers using the clocked timetag format the resolution must be
            specified as a tuple in the form (coarse resolution, fine
            resolution). As an example a clock signal from an 80Mhz TiSapphire
            laser and a fine resolution on-board the time timetagger would
            give: ``resolution = (12.5e-9, 1e-12)``

    Examples:
        Creation of a TangyBuffer object for both the ``Standard`` and
        ``Clocked`` timetag formats that can hold 1,000,000 timetags for a
        device with 4 channels. The method to connect to these buffers is also
        shown. This method of creating new buffers and connecting to existing
        ones allows the user to hold on to and continously read timetags from
        a device in one process and then connect to that buffer in another to
        perform analysis on the current data.
        === "Buffer in ``Standard`` format"
            ```python
            # Here we will create a buffer called 'standard' (imaginitive)
            # that will only except timetags in the ``Standard`` format, this is
            # selected by only supplying a single value for the resolution
            standard_buffer = tangy.TangyBuffer("standard", 1e-9, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            standard_buffer_connection = tangy.TangyBuffer("standard")
            ```

        === "Buffer in ``Clocked`` format"
            ```python
            # Here we will create a buffer called 'clocked' (imaginitive)
            # that will only except timetags in the ``Clocked`` format, this is
            # selected by supplying a pair of values for the resolution
            resolution = (12.5e-9, 1e-12) # 80Mhz Clock and 1ps fine resolution
            clocked_buffer = tangy.TangyBuffer("clocked", resolution, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            clocked_buffer_connection = tangy.TangyBuffer("clocked")
            ```
    """

    _buffer: _tangy.std_buffer
    _ptr: cython.pointer(_tangy.std_buffer)
    _type: _tangy.BufferType
    _have_measurement: bool = False
    _measurement_cc: cython.pointer(_tangy.std_cc_measurement)

    def __init__(self, name: str,
                 resolution: Optional[float] = None,
                 length: Optional[int] = None,
                 n_channels: Optional[int] = None):
        buffer_list_update()
        self._name = name.encode('utf-8')
        c_name: cython.p_char = self._name

        result: _tangy.tbResult = _tangy.std_buffer_connect(c_name, cython.address(self._buffer))
        if result.Ok is True:
            self._ptr = cython.address(self._buffer)
            return

        if resolution is None:
            raise ValueError("Must supply a resolution when creating a new buffer")

        if length is None:
            raise ValueError("Must supply a length when creating a new buffer")

        if n_channels is None:
            raise ValueError("Must specifiy the number of channels when creating a new buffer")

        result = _tangy.std_buffer_init(length, resolution, n_channels, c_name,
                                        cython.address(self._buffer))
        if False is result.Ok:
            # raise an error
            raise MemoryError
        _tangy.std_buffer_info_init(self._buffer.map_ptr,
                                    cython.address(self._buffer))
        self._ptr = cython.address(self._buffer)
        self._type = _tangy.BufferType.Clocked

        buffer_list_append(self)
        return

    def __del__(self):
        result: _tangy.tbResult = _tangy.std_buffer_deinit(self._ptr)
        if result.Ok is False:
            print("something went wrong...")
        # TODO: check result...
        # TODO: update buffer list

    @cython.ccall
    def oldest_index(self) -> int:
        return _tangy.std_oldest_index(self._ptr)

    @cython.ccall
    def _get(self, key):
        start: int
        stop: int
        step: int

        (start, stop, step) = self._make_slice(key)
        n: u64n = abs(stop - start)

        count: u64n
        channels: u8n[:] = zeros(n, dtype=u8n)
        channels_view: cython.uchar[:] = channels

        ptrs: _tangy.std_slice
        ptrs.length = n
        ptrs.channel = cython.address(channels_view[0])

        timestamps: u64n[:] = zeros(n, dtype=u64n)
        timestamps_view: u64[:] = timestamps
        ptrs.timestamp = cython.address(timestamps_view[0])

        count = _tangy.std_buffer_slice(self._ptr,
                                        cython.address(ptrs),
                                        start, stop)

        return (channels[::step], timestamps[::step])

    @cython.ccall
    def push(self, channels: ndarray(u8n), timetags: ndarray(u64n)):

        count: u64n = 0
        n_channels: int = len(channels)

        start: u64n = self.count
        stop: u64n = start + n_channels

        n_timetags: int = len(timetags)
        if n_channels != n_timetags:
            ValueError
        channels_view: cython.uchar[:] = channels
        timetags_view: u64[:] = timetags
        ptrs: _tangy.std_slice
        ptrs.length = n_channels
        ptrs.channel = cython.address(channels_view[0])
        ptrs.timestamp = cython.address(timetags_view[0])
        count = _tangy.std_buffer_push(self._ptr, ptrs, start, stop)
        return

    @property
    def name(self):
        return self._buffer.name

    @property
    def file_descriptor(self):
        return self._buffer.file_descriptor

    @property
    def capacity(self) -> int:
        return self._buffer.capacity[0]

    @property
    def resolution(self) -> float:
        return self._buffer.resolution[0]

    @resolution.setter
    def resolution(self, resolution: float):
        self._buffer.resolution[0] = resolution

    @property
    def count(self) -> int:
        return self._buffer.count[0]

    @property
    def index_of_reference(self) -> int:
        return self._buffer.index_of_reference[0]

    @property
    def reference_count(self) -> int:
        return self._buffer.reference_count[0]

    @reference_count.setter
    def reference_count(self, int):
        self._buffer.reference_count[0] = 0

    @property
    def n_channels(self) -> int:
        return self._buffer.n_channels[0]

    @cython.ccall
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
        return _tangy.std_time_in_buffer(self._ptr)

    @cython.ccall
    def time_range(self) -> Tuple[float, float]:
        # begin: float = time_at_index(self._v_ptr, self._type, self.begin % self.capacity)
        # end: float = time_at_index(self._v_ptr, self._type, self.end % self.capacity)
        begin: float
        end: float
        idx: int
        idx = (self.begin + 1) % self.capacity
        rec: _tangy.standard = _tangy.std_record_at(self._ptr, idx)
        begin = _tangy.std_to_time(rec, self._buffer.resolution[0])

        idx = self.end % self.capacity
        rec = _tangy.std_record_at(self._ptr, idx)
        end = _tangy.std_to_time(rec, self._buffer.resolution[0])

        return (begin, end)

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
        bins: u64n = _tangy.std_bins_from_time(self._buffer.resolution[0], time)

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

        bins: u64n = self.bins_from_time(time)
        index: u64n = _tangy.std_lower_bound(self._ptr, bins)

        return index

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

        counters: u64n[:] = zeros(self.n_channels, dtype=u64n)
        counters_view: u64[::1] = counters

        if read_time:
            read_time: f64n = read_time
            start: u64n = self.lower_bound(read_time)

        if stop is None:
            stop: u64n = self.count - 1

        total: u64n = 0

        total = _tangy.std_singles(self._ptr, start, stop, cython.address(counters_view[0]))

        return (total, counters)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.ccall
    def coincidence_count(self, read_time: float, window: float,
                          channels: List[int], delays: Optional[List[int]] = None):

        _n_channels = len(channels)

        assert _n_channels <= self.n_channels, "More channels than available in buffer"

        assert max(channels) <= self.n_channels, \
            f"Requested channel {max(channels)} when maximum channel available in {self.n_channels}"

        _channels: ndarray(u8n) = array(channels, dtype=u8n)

        if delays is None:
            delays: ndarray(f64n) = zeros(_n_channels, dtype=f64n)

        _channels_view: cython.uchar[::1] = _channels
        _delays_view: cython.double[::1] = array(delays, dtype=f64n)

        count = _tangy.std_coincidences_count(self._ptr,
                                              _n_channels,
                                              cython.address(_channels_view[0]),
                                              cython.address(_delays_view[0]),
                                              window,
                                              read_time)
        return count

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.ccall
    def coincidence_collect(self, read_time: float, window: float,
                            channels: List[int], delays: Optional[List[int]] = None):

        n_channels = len(channels)

        assert n_channels <= self.n_channels, "More channels than available in buffer"

        assert max(channels) <= self.n_channels, \
            f"Requested channel {max(channels)} when maximum channel available in {self.n_channels}"

        _channels: ndarray(u8n) = array(channels, dtype=u8n)

        if delays is None:
            delays: ndarray(f64n) = zeros(n_channels, dtype=f64n)

        channels_view: cython.uchar[::1] = _channels
        delays_view: cython.double[::1] = array(delays, dtype=f64n)

        if self._have_measurement is False:
            self._measurement_cc = _tangy.std_coincidence_measurement_new(
                self._buffer.resolution[0], n_channels, cython.address(channels_view[0]))

        self._measurement_cc.n_channels = n_channels
        self._measurement_cc.channels = cython.address(channels_view[0])

        count: u64n = _tangy.std_coincidences_records(self._ptr,
                                                      cython.address(delays_view[0]),
                                                      window,
                                                      read_time,
                                                      self._measurement_cc)

        total: u64n = self._measurement.total_records

        assert count == total, f"Count {count} and total {total} aren't equal"

        records: ndarray(u64n) = zeros(total, dtype=u64n)
        for i in range(total):
            records[i] = self._measurement_cc.records.data[i]

        return RecordsStandard(total, self.resolution, _channels, records)


@cython.cclass
class TangyBufferClocked(TangyBuffer):
    """Interface to underlying ring buffer

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (float): Resolution of timetags in seconds. A single float
            for the "standard timetags". A pair of floats for "clocked timetags"
            with a "coarse" and "fine" timing structure. Unused if connecting.
            In seconds.
        n_channels (int): Number of channels
        length (int): Length of buffer to create.
        Unused if connecting.

    Attributes:
        name (str): Name of buffer
        file_descriptor (int): File descriptor of underlying ring buffer
            capacity (int): Size of buffer
        resolution (Union[float, Tuple[float, float]]): Single float for
            a buffer of ``standard timetags`` or a pair of floats for buffers of
            ``clocked timetags`` (coarse resolution, fine resolution).
            Resolutions are in seconds.
        count (int): Number of elements that have been written to the buffer
        index_of_reference (int): On/off marker
        n_channels (int): Number of channels the buffer can contain

    Note:
        If connecting to an existing buffer the resolution, n_channels and
        length arguments will be ignored even if supplied.

    Note:
        For buffers using the clocked timetag format the resolution must be
            specified as a tuple in the form (coarse resolution, fine
            resolution). As an example a clock signal from an 80Mhz TiSapphire
            laser and a fine resolution on-board the time timetagger would
            give: ``resolution = (12.5e-9, 1e-12)``

    Examples:
        Creation of a TangyBuffer object for both the ``Standard`` and
        ``Clocked`` timetag formats that can hold 1,000,000 timetags for a
        device with 4 channels. The method to connect to these buffers is also
        shown. This method of creating new buffers and connecting to existing
        ones allows the user to hold on to and continously read timetags from
        a device in one process and then connect to that buffer in another to
        perform analysis on the current data.
        === "Buffer in ``Standard`` format"
            ```python
            # Here we will create a buffer called 'standard' (imaginitive)
            # that will only except timetags in the ``Standard`` format, this is
            # selected by only supplying a single value for the resolution
            standard_buffer = tangy.TangyBuffer("standard", 1e-9, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            standard_buffer_connection = tangy.TangyBuffer("standard")
            ```

        === "Buffer in ``Clocked`` format"
            ```python
            # Here we will create a buffer called 'clocked' (imaginitive)
            # that will only except timetags in the ``Clocked`` format, this is
            # selected by supplying a pair of values for the resolution
            resolution = (12.5e-9, 1e-12) # 80Mhz Clock and 1ps fine resolution
            clocked_buffer = tangy.TangyBuffer("clocked", resolution, 4, int(1e6))

            # A new buffer object can be made by connecting to a buffer with
            # the correct name
            clocked_buffer_connection = tangy.TangyBuffer("clocked")
            ```
    """

    _buffer: _tangy.clk_buffer
    _ptr: cython.pointer(_tangy.clk_buffer)
    _type: _tangy.BufferType
    _have_measurement: bool = False
    _measurement_cc: cython.pointer(_tangy.clk_cc_measurement)
    # _name = cython.declare(bytes)

    def __init__(self, name: str,
                 resolution: Optional[Tuple[float, float]] = None,
                 length: Optional[int] = None,
                 n_channels: Optional[int] = None):
        buffer_list_update()
        self._name = name.encode('utf-8')
        c_name: cython.p_char = self._name

        result: _tangy.tbResult = _tangy.clk_buffer_connect(c_name, cython.address(self._buffer))
        if result.Ok is True:
            self._ptr = cython.address(self._buffer)
            return

        if resolution is None:
            raise ValueError("Must supply a resolution when creating a new buffer")

        if length is None:
            raise ValueError("Must supply a length when creating a new buffer")

        if n_channels is None:
            raise ValueError("Must specifiy the number of channels when creating a new buffer")

        _resolution: _tangy.clk_res
        _resolution.coarse = resolution[0]
        _resolution.fine = resolution[1]

        result = _tangy.clk_buffer_init(length, _resolution, n_channels, c_name,
                                        cython.address(self._buffer))
        if False is result.Ok:
            # raise an error
            raise MemoryError

        _tangy.clk_buffer_info_init(self._buffer.map_ptr,
                                    cython.address(self._buffer))
        self._ptr = cython.address(self._buffer)
        self._type = _tangy.BufferType.Clocked
        buffer_list_append(self)
        return

    def __del__(self):
        result: _tangy.tbResult = _tangy.clk_buffer_deinit(self._ptr)
        if result.Ok is False:
            print("something went wrong")
        # TODO: check result...
        # TODO: update buffer list

    @cython.ccall
    def oldest_index(self) -> int:
        return _tangy.clk_oldest_index(self._ptr)

    @cython.ccall
    def _get(self, key):
        start: int
        stop: int
        step: int

        (start, stop, step) = self._make_slice(key)
        n: u64n = abs(stop - start)

        count: u64n
        channels: u8n[:] = zeros(n, dtype=u8n)
        channels_view: cython.uchar[:] = channels

        ptrs: _tangy.clk_field_ptrs
        ptrs.length = n
        ptrs.channels = cython.address(channels_view[0])

        clocks: u64n[:] = zeros(n, dtype=u64n)
        clocks_view: u64[:] = clocks
        ptrs.clocks = cython.address(clocks_view[0])

        deltas: u64n[:] = zeros(n, dtype=u64n)
        deltas_view: u64[:] = deltas
        ptrs.deltas = cython.address(deltas_view[0])

        count = _tangy.clk_buffer_slice(self._ptr,
                                        cython.address(ptrs),
                                        start, stop)

        return (channels[::step], clocks[::step], deltas[::step])

    @cython.ccall
    def push(self, channels: ndarray(u8n),
             timetags: Union[ndarray(u64n),
                             Tuple(ndarray(u64n), ndarray(u64n))]):

        count: u64n = 0
        n_channels: int = len(channels)

        start: u64n = self.count
        stop: u64n = start + n_channels

        (clocks, deltas) = timetags
        n_clocks: int = len(clocks)
        n_deltas: int = len(deltas)
        if (n_channels != n_clocks) or (n_channels != n_deltas):
            ValueError

        channels_view: cython.uchar[:] = channels
        clocks_view: u64[:] = clocks
        deltas_view: u64[:] = deltas
        ptrs: _tangy.clk_field_ptrs
        ptrs.length = n_channels
        ptrs.channels = cython.address(channels_view[0])
        ptrs.clocks = cython.address(clocks_view[0])
        ptrs.deltas = cython.address(deltas_view[0])
        count = _tangy.clk_buffer_push(self._ptr, ptrs, start, stop)
        return

    @property
    def name(self):
        return self._buffer.name

    @property
    def file_descriptor(self):
        return self._buffer.file_descriptor

    @property
    def capacity(self) -> int:
        return self._buffer.capacity[0]

    @property
    def resolution(self) -> Tuple[float, float]:
        return (self._buffer.resolution[0].coarse,
                self._buffer.resolution[0].fine)

    @resolution.setter
    def resolution(self, resolution: Tuple[float, float]):
        _res: _tangy.clk_res
        _res.coarse = resolution[0]
        _res.fine = resolution[1]
        self._buffer.resolution[0] = _res

    @property
    def count(self) -> int:
        return self._buffer.count[0]

    @property
    def index_of_reference(self) -> int:
        return self._buffer.index_of_reference[0]

    @property
    def reference_count(self) -> int:
        return self._buffer.reference_count[0]

    @reference_count.setter
    def reference_count(self, int):
        self._buffer.reference_count[0] = 0

    @property
    def n_channels(self) -> int:
        return self._buffer.n_channels[0]

    @cython.ccall
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
        return _tangy.clk_time_in_buffer(self._ptr)

    @cython.ccall
    def time_range(self) -> Tuple[float, float]:
        # begin: float = time_at_index(self._v_ptr, self._type, self.begin % self.capacity)
        # end: float = time_at_index(self._v_ptr, self._type, self.end % self.capacity)
        begin: float
        end: float
        idx: int

        idx = (self.begin + 1) % self.capacity
        rec: _tangy.clocked = _tangy.clk_record_at(self._ptr, idx)
        begin = _tangy.clk_to_time(rec, self._buffer.resolution[0])

        idx = self.end % self.capacity
        rec = _tangy.clk_record_at(self._ptr, idx)
        end = _tangy.clk_to_time(rec, self._buffer.resolution[0])

        return (begin, end)

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
        bins: u64n = _tangy.clk_bins_from_time(self._buffer.resolution[0], time)
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

        bins: u64n = self.bins_from_time(time)
        index: u64n = _tangy.clk_lower_bound(self._ptr, bins)

        return index

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

        counters: u64n[:] = zeros(self.n_channels, dtype=u64n)
        counters_view: u64[::1] = counters

        if read_time:
            read_time: f64n = read_time
            start: u64n = self.lower_bound(read_time)

        if stop is None:
            stop: u64n = self.count - 1

        total: u64n = 0

        total = _tangy.clk_singles(self._ptr, start, stop, cython.address(counters_view[0]))

        return (total, counters)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.ccall
    def coincidence_count(self, read_time: float, window: float,
                          channels: List[int], delays: Optional[List[int]] = None):

        _n_channels = len(channels)

        assert _n_channels <= self.n_channels, "More channels than available in buffer"

        assert max(channels) <= self.n_channels, \
            f"Requested channel {max(channels)} when maximum channel available in {self.n_channels}"

        _channels: ndarray(u8n) = array(channels, dtype=u8n)

        if delays is None:
            delays: ndarray(f64n) = zeros(_n_channels, dtype=f64n)

        _channels_view: cython.uchar[::1] = _channels
        _delays_view: cython.double[::1] = array(delays, dtype=f64n)

        count = _tangy.clk_coincidences_count(self._ptr,
                                              _n_channels,
                                              cython.address(_channels_view[0]),
                                              cython.address(_delays_view[0]),
                                              window,
                                              read_time)
        return count

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.ccall
    def coincidence_collect(self, read_time: float, window: float,
                            channels: List[int], delays: Optional[List[int]] = None):

        n_channels = len(channels)

        assert n_channels <= self.n_channels, "More channels than available in buffer"

        assert max(channels) <= self.n_channels, \
            f"Requested channel {max(channels)} when maximum channel available in {self.n_channels}"

        _channels: ndarray(u8n) = array(channels, dtype=u8n)

        if delays is None:
            delays: ndarray(f64n) = zeros(n_channels, dtype=f64n)

        channels_view: cython.uchar[::1] = _channels
        delays_view: cython.double[::1] = array(delays, dtype=f64n)

        if self._have_measurement is False:
            self._measurement_cc = _tangy.clk_coincidence_measurement_new(
                self._buffer.resolution[0], n_channels, cython.address(channels_view[0]))

        self._measurement_cc.n_channels = n_channels
        self._measurement_cc.channels = cython.address(channels_view[0])

        count: u64n = _tangy.clk_coincidences_records(self._ptr,
                                                      cython.address(delays_view[0]),
                                                      window,
                                                      read_time,
                                                      self._measurement_cc)

        total: u64n = self._measurement_cc.total_records

        assert count == total, f"Count {count} and total {total} aren't equal"

        clocks: ndarray(u64n) = zeros(total, dtype=u64n)
        deltas: ndarray(u64n) = zeros(total, dtype=u64n)
        for i in range(total):
            clocks[i] = self._measurement_cc.records.data.clock[i]
            deltas[i] = self._measurement_cc.records.data.delta[i]

        (coarse, fine) = self.resolution

        return RecordsClocked(total, coarse, fine, _channels, clocks, deltas)


TangyBufferT = cython.fused_type(TangyBufferStandard, TangyBufferClocked)

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


@cython.cclass
class JointHistogramMeasurement:
    _n_channels: u8n
    _window: float
    _central_bin: int
    _radius: float
    _channels: ndarray(u8n)
    _delays: ndarray(f64n)
    _channels_view: cython.uchar[:]
    _delays_view: cython.double[:]
    _measurement: _tangy.delay_histogram_measurement
    _measurement_ptr: cython.pointer(_tangy.delay_histogram_measurement)
    _temporal_window: int
    _histogram: ndarray(u64n)
    _histogram_view: u64[:, ::1]
    _histogram_ptrs: cython.pointer(cython.pointer(u64))

    def __init__(self, buffer: TangyBuffer, radius: cython.double,
                 channels: List[int], signal: int,
                 idler: int, clock: Optional[int] = 0,
                 delays: Optional[List[float]] = None):

        n: u64n = len(channels)
        self._n_channels = n

        self._channels = asarray(channels, dtype=u8n)
        self._delays = zeros(n, dtype=f64n)

        if delays:
            for i in range(n):
                self._delays[i] = delays[i]

        self._channels_view = self._channels
        self._delays_view = self._delays

        radius_bins = buffer.bins_from_time(radius)
        self._radius = radius
        self._temporal_window = radius_bins * 2
        self._central_bin = radius_bins
        self._histogram = zeros([self._temporal_window, self._temporal_window],
                                dtype=u64n, order='C')
        self._histogram_view = self._histogram

        channels_ptr = cython.address(self._channels_view[0])

        resolution = buffer.resolution
        if type(resolution) is float:
            print("standard")
            self._measurement = _tangy.std_dh_measurement_new(n, clock, signal, idler, channels_ptr)
            self._measurement_ptr = cython.address(self._measurement)

        elif type(resolution) is tuple:
            print("clocked")
            self._measurement = _tangy.clk_dh_measurement_new(n, clock, signal, idler, channels_ptr)
            self._measurement_ptr = cython.address(self._measurement)

        return

    @cython.ccall
    def collect(self, buffer: TangyBufferT, read_time: float):
        """ Collect timetags for coincidences

        Returns:
            (Union[RecordsStandard, RecordsClocked]):
        """

        count: u64n = 0
        total: u64n = 0

        self._histogram_ptrs = cython.cast(
            cython.pointer(cython.pointer(u64)),
            malloc(self._temporal_window * cython.sizeof(u64)))

        i: cython.Py_ssize_t = 0
        for i in range(self._temporal_window):
            self._histogram_ptrs[i] = cython.address(self._histogram_view[i, 0])

        if TangyBufferT is TangyBufferStandard:
            count = _tangy.std_joint_delay_histogram(
                buffer._ptr,
                cython.address(self._delays_view[0]),
                self._radius,
                read_time,
                self._measurement_ptr,
                cython.address(self._histogram_ptrs[0]))

        elif TangyBufferT is TangyBufferClocked:
            count = _tangy.clk_joint_delay_histogram(
                buffer._ptr,
                cython.address(self._delays_view[0]),
                self._radius,
                read_time,
                self._measurement_ptr,
                cython.address(self._histogram_ptrs[0]))

        # free(self._measurement_ptr)
        return count

    @cython.ccall
    def histogram(self, bin_width: int = 1, centre: bool = False) -> JointHistogram:
        if bin_width < 1:
            raise ValueError("bin_width must be >= 1")

        ((nr, nc), ms, mi, histogram) = bin_histogram(self._histogram, bin_width, bin_width)

        temporal_window = self._temporal_window // bin_width
        central_bin = temporal_window // 2
        if centre:
            (ms, mi, histogram) = centre_histogram(central_bin, temporal_window,
                                                   mi, ms, histogram)

        axis = arange(temporal_window) - central_bin  # TODO: convert to time
        return JointHistogram(central_bin, temporal_window,
                              (bin_width, bin_width), histogram,
                              mi, ms, axis, axis)


@cython.ccall
def timetrace(buffer: TangyBufferT, channels: List[int], read_time: float,
              resolution: float = 10):

    n_channels: u64n = len(channels)
    # channels: u8n[:] = asarray(channels, dtype=u8n)
    channels_view: cython.uchar[::1] = asarray(channels, dtype=u8n)
    channels_ptr: cython.pointer(cython.uchar) = cython.address(
        channels_view[0])

    buffer_resolution: f64n = 0
    if TangyBufferT is TangyBufferStandard:
        buffer_resolution = buffer.resolution
    elif TangyBufferT is TangyBufferClocked:
        buffer_resolution = buffer.resolution[1]    # fine resolution

    bin_width: u64n = round(resolution / buffer_resolution)

    n: cython.int = 1
    if resolution < read_time:
        n = int(read_time // resolution) + 1

    intensity_vec: cython.pointer(_tangy.vec_u64) = _tangy.vector_u64_init(n)

    total: u64n = 0
    if TangyBufferT is TangyBufferStandard:
        total = _tangy.std_timetrace(buffer._ptr,
                                     read_time,
                                     bin_width,
                                     channels_ptr,
                                     n_channels,
                                     n,
                                     intensity_vec)
    if TangyBufferT is TangyBufferClocked:
        total = _tangy.clk_timetrace(buffer._ptr,
                                     read_time,
                                     bin_width,
                                     channels_ptr,
                                     n_channels,
                                     n,
                                     intensity_vec)

    intensities: u64n[:] = zeros(intensity_vec.length, dtype=u64n)
    intensities_view: u64[::1] = intensities
    for i in range(intensity_vec.length):
        intensities_view[i] = intensity_vec.data[i]

    intensity_vec = _tangy.vector_u64_deinit(intensity_vec)

    return intensities


@cython.ccall
def find_delay(buffer: TangyBufferT, channel_a: int, channel_b: int,
               read_time: float, resolution: float = 1e-9,
               window: Optional[float] = None
               ) -> delay_result:

    trace_res: f64n = 5e-2
    trace: u64n[:] = timetrace(
        buffer, [channel_a, channel_b], read_time, trace_res)

    avrg_intensity = mean(trace) / trace_res

    if window is None:
        correlation_window = 2 / avrg_intensity * 2

    correlation_window = f64n(window)

    if resolution is None:
        resolution = (2 / avrg_intensity) / 8000

    res: f64n = 0
    if TangyBufferT is TangyBufferStandard:
        res = buffer.resolution
    elif TangyBufferT is TangyBufferClocked:
        res = buffer.resolution[1]    # fine resolution

    n_bins: u64n = round(correlation_window / resolution) - 1
    correlation_window = correlation_window / res

    measurement_resolution: u64n = u64n(
        correlation_window / f64n(n_bins))

    correlation_window = n_bins * measurement_resolution
    n_bins = n_bins * 2
    intensities: u64n[:] = zeros(int(n_bins), dtype=u64n)
    intensities_view: u64[::1] = intensities

    if TangyBufferT is TangyBufferStandard:
        _tangy.std_find_zero_delay(buffer._ptr,
                                   read_time,
                                   u64n(correlation_window),
                                   measurement_resolution,
                                   channel_a,
                                   channel_b,
                                   n_bins,
                                   cython.address(intensities_view[0]))

    elif TangyBufferT is TangyBufferClocked:
        _tangy.clk_find_zero_delay(buffer._ptr,
                                   read_time,
                                   u64n(correlation_window),
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

    # if buffer._type is _tangy.BufferType.Clocked:
    if TangyBufferT is TangyBufferClocked:
        index = buffer.lower_bound(buffer.time_in_buffer() - 1)
        channels, clocks, deltas = buffer[index:buffer.count - 1]
        temporal_window = int(buffer.resolution[0] / buffer.resolution[1])
        bins = arange(temporal_window)
        hist_a, edges = nphist(deltas[channels == channel_a], bins)
        central_delay += mean(bins[:-1][hist_a > (0.5 * max(hist_a))]) * (1e-12)

    result = delay_result(
        times=times,
        intensities=intensities,
        fit=hist_fit,
        tau1=opt[0],
        tau2=opt[1],
        t0=opt[2],
        central_delay=central_delay,
        max_intensity=opt[3])

    return result


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

        tag = {"idx": idx, "type": tag_type, "value": value}
        tag_name = name.strip(b"\0").decode()
        tags[tag_name] = tag

    return tags, offset + 48, tag_end_offset


@cython.cfunc
def ptu_read_into(buffer: TangyBufferT,
                  file_handle: cython.pointer(FILE),
                  status: cython.pointer(_tangy.READER_STATUS),
                  n: u64n):
    res: u64n = 0

    if TangyBufferT is TangyBufferStandard:
        res = _tangy.read_next_HH2_T2(buffer._ptr, file_handle, status, n)
    elif TangyBufferT is TangyBufferClocked:
        res = _tangy.read_next_HH2_T3(buffer._ptr, file_handle, status, n)

    return res


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

        print("attempting to make buffer")
        resolution: Union[float, Tuple[float, float]]
        if "T2" in key:
            # self._buffer_type = _tangy.BufferType.Standard
            resolution = sync_res
            self._buffer = TangyBuffer.make_new_standard(name, resolution, length, n_ch)

        elif "T3" in key:
            # self._buffer_type = _tangy.BufferType.Clocked
            # self._buffer = TangyBuffer(name, (glob_res, sync_res), length, n_ch)
            resolution = (glob_res, sync_res)
            self._buffer = TangyBuffer.make_new_clocked(name, resolution, length, n_ch)

        print("buffer made")
        return

    def __del__(self):
        fclose(self._c_file_handle)
        self._file_handle.close()

    # def __repr__(self):
    #     if _tangy.BufferType.Standard == self._buffer_type:
    #         return self._std_buffer.__repr__()
    #     if _tangy.BufferType.Clocked == self._buffer_type:
    #         return self._clk_buffer.__repr__()

    def buffer(self):
        """
        Acquire the buffer being written to

        Returns:
            TangyBuffer: Instance of buffer for the openend file. Where the \
                buffer is an instance of TangyBuffer (either TangyBufferStandard\
                or TangyBufferClocked).
        """
        return self._buffer

    @ property
    def record_count(self):
        return self._status.record_count

    @ property
    def header(self):
        return self._header

    def __len__(self):
        return len(self._buffer)

    @ property
    def count(self):
        x: u64n = self._buffer.count
        return x

    @cython.ccall
    def read(self, n: u64n):
        """
        Read an amount of tags from the target file

        :param n: [TODO:description]
        """
        res: u64n = 0
        if type(self._buffer) is TangyBufferStandard:
            res = ptu_read_into[TangyBufferStandard](
                self._buffer, self._c_file_handle, self._status, n)
        elif type(self._buffer) is TangyBufferClocked:
            res = ptu_read_into[TangyBufferClocked](
                self._buffer, self._c_file_handle, self._status, n)
        return res

    # def read_seconds(self, t: f64n):
    #     if _tangy.BufferType.Standard == self._buffer_type:
    #         ch_last: u8n
    #         tt_last: u64n
    #         (ch_last, tt_last) = self._std_buffer[-1]

    #         bins: u64n = _tangy.std_as_bins(
    #             new_standard_record(ch_last, tt_last),
    #             self._std_buffer._resolution())

    #         res: u64n = _tangy.read_next_HH2_T2(
    #             cython.address(self._std_buffer._buffer), self._c_file_handle,
    #             self._status, bins)

    #     if _tangy.BufferType.Clocked == self._buffer_type:
    #         (ch_last, cl_last, d_last) = self._clk_buffer[-1]

    #         bins: u64n = _tangy.clk_as_bins(
    #             new_clocked_record(ch_last, cl_last, d_last),
    #             self._clk_buffer._resolution())

    #         res: u64n = _tangy.read_next_HH2_T3(
    #             cython.address(self._clk_buffer._buffer), self._c_file_handle,
    #             self._status, bins)

    #     return res


@cython.cclass
class IFace:

    name: str

    def __init__(self, name):
        ...

    @property
    def foo(self):
        """doc"""
        return self._foo[0]

    @foo.setter
    def foo(self, value):
        self._foo[0] = value

    @property
    def name(self) -> str:
        return self.name

    @cython.ccall
    def greet(self) -> cython.void:
        g: str = f"object, {self.name}, says hello"
        print(g)

    def adds(self, a, b):
        pass


@cython.cclass
class ImplA(IFace):

    _foo = cython.declare(cython.pointer(cython.int))

    def __init__(self, name, a):
        self.name = name

    @cython.ccall
    def adds(self, a: cython.int, b: cython.int) -> cython.int:
        return a + b

    # @property
    # def foo(self):
    #     """doc"""
    #     return self._foo[0]


@cython.cclass
class ImplB(IFace):

    def __init__(self, name):
        self.name = name

    @cython.ccall
    def adds(self, a: cython.double, b: cython.double) -> cython.double:
        return a + b


# @cython.cclass
# class TestBuffer:
#     #_ptr: Union[cython.pointer(_tangy.std_buffer), cython.pointer(_tangy.clk_buffer)]
#     #_buffer: Union[_tangy.std_buffer, _tangy.clk_buffer]
#
#     def __init__(self, buf: TangyBufferT):
#         if TangyBufferT is TangyBufferStandard:
#             self._buffer: buf._ptr
#         if TangyBufferT is TangyBufferClocked:
#             self._buffer: buf._ptr
#
#     @property
#     def file_descriptor(self):
#         return self._buffer.file_descriptor
#
#     @property
#     def capacity(self) -> int:
#         return self._buffer.capacity[0]
#
#     @property
#     def resolution(self) -> float:
#         return self._buffer.resolution[0]
#
#     @resolution.setter
#     def resolution(self, resolution: float):
#         self._buffer.resolution[0] = resolution
#
#     @property
#     def count(self) -> int:
#         return self._buffer.count[0]
#
#     @property
#     def index_of_reference(self) -> int:
#         return self._buffer.index_of_reference[0]
#
#     @property
#     def n_channels(self) -> int:
#         return self._buffer.n_channels[0]
