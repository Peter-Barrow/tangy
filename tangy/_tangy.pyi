import cython
from _typeshed import Incomplete
from cython.cimports import _tangy as _tangy
from cython.cimports.cython import view as view
from cython.cimports.libc.stdint import int64_t as i64
from cython.cimports.libc.stdio import fseek as fseek
from cython.cimports.libc.stdlib import free as free
from enum import Enum as Enum
from numpy import array as array, empty as empty, log2 as log2, ndarray as ndarray, ravel as ravel, reshape as reshape, uint64 as u64n

TimeTag: Incomplete
Resolution: Incomplete
std_buf_ptr: Incomplete
clk_buf_ptr: Incomplete
TangyBufferPtr: Incomplete

def into_std_buffer(void_ptr: None) -> std_buf_ptr: ...
def into_clk_buffer(void_ptr: None) -> clk_buf_ptr: ...
def to_time(tag: TimeTag, resolution: Resolution) -> cython.double: ...
def timetag_at(ptr: TangyBufferPtr, idx: u64n): ...
def time_at_index(buf_ptr: None, buf_type: _tangy.BufferType, index: u64n) -> float: ...
def buffer_type(ptr: TangyBufferPtr): ...
def buffer_list_update() -> None: ...
def buffer_list_append() -> None: ...
def buffer_list_contains() -> None: ...

class RecordsStandard:
    count: u64n
    resolution: float
    channels: None
    timetags: None
    def asTime(self): ...
    def __len__(self) -> cython.Py_ssize_t: ...

class RecordsClocked:
    count: u64n
    resolution_coarse: float
    resolution_fine: float
    channels: None
    clocks: None
    deltas: None
    def asTime(self): ...
    def __len__(self) -> cython.Py_ssize_t: ...

Record: Incomplete

def double_decay(time, tau1, tau2, t0, max_intensity): ...

class delay_result:
    times: None
    intensities: None
    fit: None
    tau1: cython.double
    tau2: cython.double
    t0: cython.double
    central_delay: cython.double
    max_intensity: cython.double

class TangyBuffer:
    @classmethod
    def make_new_standard(cls, name: str, resolution: float, length: int, n_channels: int) -> TangyBufferStandard: ...
    @classmethod
    def make_new_clocked(cls, name: str, resolution: tuple[float, float], length: int, n_channels: int) -> TangyBufferClocked: ...
    def __del__(self) -> None: ...
    def configuration(self) -> dict: ...
    def __len__(self) -> int: ...
    def __call__(self, time: float) -> int: ...
    @property
    def end(self) -> int: ...
    @property
    def begin(self) -> int: ...
    def __getitem__(self, key): ...
    def oldest_index(self) -> int: ...
    def push(self, channels: None, timetags): ...
    @property
    def name(self) -> None: ...
    @property
    def file_descriptor(self) -> None: ...
    @property
    def capacity(self) -> int: ...
    @property
    def resolution(self) -> None: ...
    @resolution.setter
    def resolution(self, resolution) -> None: ...
    @property
    def count(self) -> int: ...
    @property
    def index_of_reference(self) -> int: ...
    @property
    def n_channels(self) -> int: ...
    def time_in_buffer(self) -> float: ...
    def time_range(self) -> tuple[float, float]: ...
    def bins_from_time(self, time: float) -> int: ...
    def lower_bound(self, time: float) -> int: ...

class TangyBufferStandard(TangyBuffer):
    def __init__(self, name: str, resolution: float, length: int, n_channels: int) -> None: ...
    def __del__(self) -> None: ...
    def oldest_index(self) -> int: ...
    def push(self, channels: None, timetags: None): ...
    @property
    def name(self): ...
    @property
    def file_descriptor(self): ...
    @property
    def capacity(self) -> int: ...
    @property
    def resolution(self) -> float: ...
    @resolution.setter
    def resolution(self, resolution: float): ...
    @property
    def count(self) -> int: ...
    @property
    def index_of_reference(self) -> int: ...
    @property
    def n_channels(self) -> int: ...
    def time_in_buffer(self) -> float: ...
    def time_range(self) -> tuple[float, float]: ...
    def bins_from_time(self, time: float) -> int: ...
    def lower_bound(self, time: float) -> int: ...

class TangyBufferClocked(TangyBuffer):
    def __init__(self, name: str, resolution: tuple[float, float], length: int, n_channels: int) -> None: ...
    def __del__(self) -> None: ...
    def oldest_index(self) -> int: ...
    def push(self, channels: None, timetags: None | None): ...
    @property
    def name(self): ...
    @property
    def file_descriptor(self): ...
    @property
    def capacity(self) -> int: ...
    @property
    def resolution(self) -> tuple[float, float]: ...
    @resolution.setter
    def resolution(self, resolution: tuple[float, float]): ...
    @property
    def count(self) -> int: ...
    @property
    def index_of_reference(self) -> int: ...
    @property
    def n_channels(self) -> int: ...
    def time_in_buffer(self) -> float: ...
    def time_range(self) -> tuple[float, float]: ...
    def bins_from_time(self, time: float) -> int: ...
    def lower_bound(self, time: float) -> int: ...

TangyBufferT: Incomplete

def singles(buffer: TangyBufferT, read_time: float | None = None, start: int | None = None, stop: int | None = None) -> tuple[int, list[int]]: ...

class CoincidenceMeasurement:
    def __init__(self, channels: list[int], resolution: None, delays: list[float] | None = None) -> None: ...

def coincidences_count(buffer: TangyBufferT, read_time: float, window: float, config: CoincidenceMeasurement | None = None, channels: list[float] | None = None, delays: list[float] | None = None) -> int: ...
def coincidences_collect(buffer: TangyBufferT, read_time: float, window: float = None, config: CoincidenceMeasurement | None = None, channels: list[float] | None = None, delays: list[float] | None = None): ...

class JointHistogram:
    central_bin: int
    temporal_window: float
    bin_size: tuple[int, int]
    data: None
    marginal_idler: None
    marginal_signal: None
    axis_idler: None
    axis_signal: None

def centre_histogram(central_bin: int, temporal_window: int, marginal_idler: None, marginal_signal: None, histogram: None): ...
def bin_histogram(histogram: None, x_width: i64, y_width: i64) -> tuple[tuple[u64n, u64n], None, None, None]: ...

class JointHistogramMeasurement:
    def __init__(self, buffer: TangyBuffer, radius: cython.double, channels: list[int], signal: int, idler: int, clock: int | None = 0, delays: list[float] | None = None) -> None: ...
    def collect(self, buffer: TangyBufferT, read_time: float): ...
    def histogram(self, bin_width: int = 1, centre: bool = False) -> JointHistogram: ...

def timetrace(buffer: TangyBufferT, channels: list[int], read_time: float, resolution: float = 10): ...
def find_delay(buffer: TangyBufferT, channel_a: int, channel_b: int, read_time: float, resolution: float = 1e-09, window: float | None = None) -> delay_result: ...
def ptu_read_into(buffer: TangyBufferT, file_handle: None, status: None, n: u64n): ...

class PTUFile:
    def __init__(self, file_path: str, name: str, length: int = 1000) -> None: ...
    def __del__(self) -> None: ...
    def buffer(self): ...
    @property
    def record_count(self): ...
    @property
    def header(self): ...
    def __len__(self) -> int: ...
    @property
    def count(self): ...
    def read(self, n: u64n): ...

class IFace:
    name: str
    def __init__(self, name) -> None: ...
    @property
    def foo(self): ...
    @foo.setter
    def foo(self, value) -> None: ...
    @property
    def name(self) -> str: ...
    def greet(self) -> cython.void: ...
    def adds(self, a, b) -> None: ...

class ImplA(IFace):
    name: Incomplete
    def __init__(self, name, a) -> None: ...
    def adds(self, a: cython.int, b: cython.int) -> cython.int: ...

class ImplB(IFace):
    name: Incomplete
    def __init__(self, name) -> None: ...
    def adds(self, a: cython.double, b: cython.double) -> cython.double: ...
