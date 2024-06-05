import cython
from _typeshed import Incomplete
from cython.cimports import _tangy as _tangy
from cython.cimports.libc.stdint import int64_t as i64
from cython.cimports.libc.stdlib import malloc as malloc
from enum import Enum
from numpy import ndarray as ndarray, uint64 as u64n

TimeTag: Incomplete
Resolution: Incomplete
std_buf_ptr: Incomplete
clk_buf_ptr: Incomplete
TangyBufferPtr: Incomplete

def to_time(tag: TimeTag, resolution: Resolution) -> cython.double: ...
def timetag_at(ptr: TangyBufferPtr, idx: u64n): ...
def buffer_type(ptr: TangyBufferPtr): ...
def tangy_config_location() -> str: ...

class RecordsStandard:
    """Container for Standard format Timetags

    Args:
        count (u64n):
        resolution (float):
        channels (ndarray(u8n)):
        timetags (ndarray(u64n)):
    """
    count: u64n
    resolution: float
    channels: None
    timetags: None
    def asTime(self): ...
    def __len__(self) -> cython.Py_ssize_t: ...

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
    count: u64n
    resolution_coarse: float
    resolution_fine: float
    channels: None
    clocks: None
    deltas: None
    def asTime(self): ...
    def __len__(self) -> cython.Py_ssize_t: ...

class RecordsNew:
    """Container for timetags

    Args:
        count (u64n):
        resolution (float):
        channels (ndarray(u8n)):
        timetags (Union[ndarray(u64n), Tuple[ndarray(u64n), ndarray(u64n)]]):
    """
    count: u64n
    resolution: float
    clock_period: float
    channels: None
    timetags: None | tuple[None, None]

Record: Incomplete

class JointHistogram:
    """JSI result
    """
    central_bin: int
    temporal_window: float
    bin_size: tuple[int, int]
    data: None
    marginal_idler: None
    marginal_signal: None
    axis_idler: None
    axis_signal: None

def centre_histogram(central_bin: int, temporal_window: int, marginal_idler: None, marginal_signal: None, histogram: None):
    """
    Centre a 2D histogram and marginals

    Todo:
        central_bin and temporal_window arguments should be removable, instead        everything should be calculated from the dimensions of the marginals

    Args:
        central_bin (int): central bin
        temporal_window (int): temporal window
        marginal_idler (ndarray(u64n)): Marginal distribution of idler
        marginal_signal (ndarray(u64n)): Marginal distribution of sigal
        histogram (ndarray(u64n)): 2D joint histogram of signal and idler

    Returns:
        (Tuple[ndarray(u64n),ndarray(u64n),ndarray(u64n)]): Tuple of idler        marginal, signal marginal and joint histogram
    """
def bin_histogram(histogram: None, x_width: i64, y_width: i64) -> tuple[tuple[u64n, u64n], None, None, None]: ...
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

class TangyBufferType(Enum):
    Standard: int
    Clocked: int

class TangyBuffer:
    def __init__(self, name: str, resolution: float, clock_period: float = 1.0, channel_count: int = 4, capacity: int = 10000000, format: TangyBufferType = ...) -> None: ...
    def __del__(self) -> None: ...
    def __len__(self) -> int:
        """ Length of buffer

        Returns:
            (int): Length of buffer
        """
    def __getitem__(self, key):
        """ Access subscript of buffer

        """
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
    @property
    def name(self) -> str:
        """ Name of buffer

        Returns:
            (str): buffer name
        """
    @property
    def resolution(self) -> float:
        """ Resolution of timetags in buffer

        Returns:
            (float): resolution of timetags
        """
    @resolution.setter
    def resolution(self, res: float): ...
    @property
    def clock_period(self) -> float:
        """ Clock period of timetags in buffer

        For timetags with 'coarse + fine' timing this returns the 'coarse'
            timing component, typically this will be the resolution / period
            of an external clock signal

        Returns:
            (float): clock period of timetags
        """
    @clock_period.setter
    def clock_period(self, period: float): ...
    @property
    def resolution_bins(self) -> int:
        """ Resolution in terms of bins of timetags in buffer

        Returns:
            (int): resolution of timetags
        """
    @property
    def clock_period_bins(self) -> int:
        """ Clock period in terms of bins of timetags in buffer

        Returns:
            (int): clock period of timetags
        """
    @property
    def conversion_factor(self) -> int:
        """doc"""
    @property
    def capacity(self) -> int:
        """ Maximum number of timetags the buffer can hold

        Returns:
            (int): maximum number of timetags
        """
    @property
    def count(self) -> int:
        """ Number of timetags written to the buffer
        """
    @property
    def reference_count(self) -> int:
        """ Number of current connections to the buffer

        Tracks number of connections to buffer, used to determine if it is safe
            to delete the backing memory and close the memory mapping.

        Returns:
            (int): number of connections
        """
    @reference_count.setter
    def reference_count(self, rc: int): ...
    @property
    def channel_count(self) -> int:
        """ Maximum number of channels in the buffer

        Typically set by a device or a file to limit the range of valid channels
            available.

        Returns:
            (int): number of channels
        """
    @channel_count.setter
    def channel_count(self, n_ch: int): ...
    def configuration(self) -> dict: ...
    def bins_from_time(self, time: float) -> int:
        """ Convert amount of time to a number of time bins

        Args:
            time (float): Amount of time in seconds

        Returns:
            (int): number of bins

        """
    def current_time(self) -> float:
        """ Returns the time of the most recent timetag
        Returns:
            (float): Most recent timetag as time
        """
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
    @property
    def begin(self) -> int:
        """ Index of first record in buffer
        Returns:
            (int): Index of first record in buffer
        """
    @property
    def end(self) -> int:
        """ Index of last record in buffer
        Returns:
            (int): Index of last record in buffer
        """
    def slice_from_pointers(self, length: u64n, channels: None, timestamps: None = None, clocks: None = None, deltas: None = None) -> _tangy.tangy_field_ptrs: ...
    def pull(self, start: u64n, stop: u64n): ...
    def push(self, channels: None, timetags: None | tuple[None, None]): ...
    def lower_bound(self, time: float) -> int:
        ''' Find the position in the buffer that gives the last "time" seconds        in the buffer

        Performs a binary search on the buffer where the location being         searched for is ``buffer.time_in_buffer() - time``.

        Args:
            time (float): Amount of time, in seconds, to split the buffer by

        Returns:
            (int): Index in buffer corresponding to the timetag that is greater            than or equal to ``buffer.time_in_buffer() - time``

        '''
    def singles(self, read_time: float | None = None, start: int | None = None, stop: int | None = None) -> tuple[int, list[int]]:
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
    def coincidence_count(self, read_time: float, window: float, channels: list[int], delays: list[int] | None = None):
        """ Count coincidences

        Args:
            read_time (float): time to integrate over
            window (float): maximum distance between timetags allows
            channels: (List[int]): channels to find coincidences between
            delays: (Optional[List[float]]): delays for each channel

        Returns:
            (int): Number of coincidences found

        """
    def coincidence_collect(self, read_time: float, window: float, channels: list[int], delays: list[int] | None = None) -> RecordsNew:
        """ Collect coincident timetags

        Args:
            read_time (float): time to integrate over
            window (float): maximum distance between timetags allows
            channels: (List[int]): channels to find coincidences between
            delays: (Optional[List[float]]): delays for each channel

        Returns:
            (Union[RecordsStandard, RecordsClocked]): Records found in coincidence

        """
    def timetrace(self, channels: list[int], read_time: float, resolution: float = 10.0): ...
    def relative_delay(self, channel_a: int, channel_b: int, read_time: float, resolution: float = 1e-09, window: float | None = None): ...
    def joint_delay_histogram(self, signal: int, idler: int, channels: list[int], read_time: float, radius: float, delays: list[float] | None = None, clock: int | None = None, bin_width: int = 1, centre: bool = True): ...

class PTUFile:
    '''Class to read data from Picoquant PTU file and write into buffer.

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

    '''
    def __init__(self, file_path: str, name: str, length: int = 1000) -> None: ...
    def __del__(self) -> None: ...
    def buffer(self) -> TangyBuffer:
        """
        Acquire the buffer being written to

        Returns:
            TangyBuffer: Instance of buffer for the openend file. Where the                 buffer is an instance of TangyBuffer (either TangyBufferStandard                or TangyBufferClocked).
        """
    @property
    def record_count(self): ...
    @property
    def header(self): ...
    def __len__(self) -> int: ...
    @property
    def count(self): ...
    def read(self, n: u64n):
        """
        Read an amount of tags from the target file

        :param n: [TODO:description]
        """

def buffer_list_update() -> dict:
    '''
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

    '''
def buffer_list_append(buffer: TangyBuffer):
    """
    Adds the configuration of a buffer to the Tangy configuration directory

    Args:
        buffer (TangyBuffer): buffer with configuration to save
    """
def buffer_list_delete_all() -> None: ...
def buffer_list_show() -> None: ...
