import cython
from _typeshed import Incomplete
from cython.cimports.libc.stdint import int64_t as i64
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
def buffer_list_contains() -> None: ...
def buffer_list_delete_all() -> None: ...
def buffer_list_show() -> None: ...

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
    """Mixin for concrete buffer implementations

    Buffer mixin class defining basic functionality that all implementors will
        employ. Provides buffer subscripting utilities in the form of
        ```TangyBuffer().begin``` and ```TangyBuffer().end``` to get correct
        positions in underlying buffer for where data begins and ends along with
        ```__getitem__``` for subscripting and ```__call__``` providing the
        user with the means to request a position in the buffer according to a
        point in time.

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

    """
    @classmethod
    def make_new_standard(cls, name: str, resolution: float, length: int, n_channels: int): ...
    @classmethod
    def make_new_clocked(cls, name: str, resolution: tuple[float, float], length: int, n_channels: int): ...
    def __del__(self) -> None: ...
    def configuration(self) -> dict:
        """ Serialise buffer configuration

        Returns:
            (dict): information about underlying buffer
        """
    def __len__(self) -> int:
        """ Length of buffer

        Returns:
            (int): Length of buffer
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
    def end(self) -> int:
        """ Index of last record in buffer
        Returns:
            (int): Index of last record in buffer
        """
    @property
    def begin(self) -> int:
        """ Index of first record in buffer
        Returns:
            (int): Index of first record in buffer
        """
    def __getitem__(self, key):
        """ Access subscript of buffer

        """
    def oldest_index(self) -> int: ...
    def push(self, channels: None, timetags): ...
    @property
    def name(self) -> None:
        """ Name of buffer

        Returns:
            (str): buffer name
        """
    @property
    def file_descriptor(self) -> None:
        """ File descriptor of buffer

        Returns:
            (str): buffers file descriptor
        """
    @property
    def capacity(self) -> int:
        """ Maximum number of timetags the buffer can hold

        Returns:
            (int): maximum number of timetags
        """
    @property
    def resolution(self) -> None:
        """ Resolution of timetags in buffer

        """
    @resolution.setter
    def resolution(self, resolution) -> None: ...
    @property
    def count(self) -> int:
        """ Number of timetags written to the buffer
        """
    @property
    def index_of_reference(self) -> int: ...
    @property
    def reference_count(self) -> int:
        """ Number of current connections to the buffer

        Tracks number of connections to buffer, used to determine if it is safe
            to delete the backing memory and close the memory mapping.

        Returns:
            (int): number of connections
        """
    @property
    def n_channels(self) -> int:
        """ Maximum number of channels in the buffer

        Typically set by a device or a file to limit the range of valid channels
            available.

        Returns:
            (int): number of channels
        """
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
    def time_range(self) -> tuple[float, float]: ...
    def bins_from_time(self, time: float) -> int:
        """ Convert amount of time to a number of time bins

        Args:
            time (float): Amount of time in seconds

        Returns:
            (int): number of bins

        Note:
            For buffers with the clocked timetag format this will be in units            of the fine resolution.

        """
    def lower_bound(self, time: float) -> int:
        ''' Find the position in the buffer that gives the last "time" seconds        in the buffer

        Performs a binary search on the buffer where the location being         searched for is ``buffer.time_in_buffer() - time``.

        Args:
            time (float): Amount of time, in seconds, to split the buffer by

        Returns:
            (int): Index in buffer corresponding to the timetag that is greater            than or equal to ``buffer.time_in_buffer() - time``

        '''
    def timetrace(self, channels: list[int], read_time: float, resolution: float = 10): ...

class TangyBufferStandard(TangyBuffer):
    '''Interface to ```standard``` style buffers

    Buffer implementation for ```standard``` style buffers with ```channel```
        field and a single field for timing information, ```timestamp```. Such
        buffers have timetags with the following structure in the c-api:
        ```c
        // Timetag format
        typedef struct std {
            u8 channel;
            u64 timestamp;
        } timetag_standard;

        typedef f64 resolution_standard;
        ```

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (float): Resolution of timetags in seconds. A single float
            for the "standard timetags". Unused if connecting. In seconds.
        n_channels (int): Number of channels. Unused if connecting.
        length (int): Length of buffer to create. Unused if connecting.

    Attributes:
        name (str): Name of buffer
        file_descriptor (int): File descriptor of underlying ring buffer
            capacity (int): Size of buffer
        resolution (float): Resolution are in seconds.
        count (int): Number of elements that have been written to the buffer
        index_of_reference (int): On/off marker
        n_channels (int): Number of channels the buffer can contain

    Note:
        If connecting to an existing buffer the resolution, n_channels and
        length arguments will be ignored even if supplied.

    Examples:
        ```python
        # Here we will create a buffer called \'standard\' (imaginitive)
        # that will only except timetags in the ``Standard`` format, this is
        # selected by only supplying a single value for the resolution
        standard_buffer = tangy.TangyBufferStandard("standard", 1e-9, 4, int(1e6))

        # A new buffer object can be made by connecting to a buffer with
        # the correct name
        standard_buffer_connection = tangy.TangyBufferStandard("standard")
        ```
    '''
    def __init__(self, name: str, resolution: float | None = None, length: int | None = None, n_channels: int | None = None) -> None: ...
    def __del__(self) -> None: ...
    def oldest_index(self) -> int: ...
    def push(self, channels: None, timetags: None): ...
    @property
    def name(self):
        """ Name of buffer

        Returns:
            (str): buffer name
        """
    @property
    def file_descriptor(self):
        """ File descriptor of buffer

        Returns:
            (str): buffers file descriptor
        """
    @property
    def capacity(self) -> int:
        """ Maximum number of timetags the buffer can hold

        Returns:
            (int): maximum number of timetags
        """
    @property
    def resolution(self) -> float:
        """ Resolution of timetags in buffer

        Returns:
            (float): resolution
        """
    @resolution.setter
    def resolution(self, resolution: float): ...
    @property
    def count(self) -> int:
        """ Number of timetags written to the buffer

        Returns:
            (int): total number of timetags written
        """
    @property
    def index_of_reference(self) -> int: ...
    @property
    def reference_count(self) -> int:
        """ Number of current connections to the buffer

        Tracks number of connections to buffer, used to determine if it is safe
            to delete the backing memory and close the memory mapping.

        Returns:
            (int): number of connections
        """
    @reference_count.setter
    def reference_count(self, int) -> None: ...
    @property
    def n_channels(self) -> int:
        """ Maximum number of channels in the buffer

        Typically set by a device or a file to limit the range of valid channels
            available.

        Returns:
            (int): number of channels
        """
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
    def time_range(self) -> tuple[float, float]: ...
    def bins_from_time(self, time: float) -> int:
        """ Convert amount of time to a number of time bins

        Args:
            time (float): Amount of time in seconds

        Returns:
            (int): number of bins

        Note:
            For buffers with the clocked timetag format this will be in units            of the fine resolution.

        """
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
    def coincidence_collect(self, read_time: float, window: float, channels: list[int], delays: list[int] | None = None) -> RecordsStandard:
        """ Collect coincident timetags

        Args:
            read_time (float): time to integrate over
            window (float): maximum distance between timetags allows
            channels: (List[int]): channels to find coincidences between
            delays: (Optional[List[float]]): delays for each channel

        Returns:
            (RecordsClocked): Records found in coincidence

        """

class TangyBufferClocked(TangyBuffer):
    '''Interface to ```clocked``` style buffers

    Buffer implementation for ```clocked``` style buffers with ```channel```
        field and a pair of fields for timing information, ```timestamp```. Such
        buffers have timetags with the following structure in the c-api:
        ```c
        typedef struct timestamp_clocked {
            u64 clock;
            u64 delta;
        } timestamp_clocked;

        // Timetag format
        typedef struct timetag_clocked {
            u8 channel;
            timestamp_clocked timestamp;
        } timetag_clocked;

        typedef struct resolution_clocked {
            f64 coarse;
            f64 fine;
        } resolution_clocked;
        ```

    Args:
        name (str): Name of buffer to be created or attached to.
        resolution (float): Resolution of timetags in seconds. A pair of floats
            for "coarse" and "fine" timing structure. Unused if connecting.
            In seconds.
        n_channels (int): Number of channels. Unused if connecting.
        length (int): Length of buffer to create. Unused if connecting.

    Attributes:
        name (str): Name of buffer
        file_descriptor (int): File descriptor of underlying ring buffer
            capacity (int): Size of buffer
        resolution (Tuple[float, float]): Pair of floats in the form
            (coarse resolution, fine resolution). Resolutions are in seconds.
        count (int): Number of elements that have been written to the buffer
        index_of_reference (int): On/off marker
        n_channels (int): Number of channels the buffer can contain

    Note:
        If connecting to an existing buffer the resolution, n_channels and
        length arguments will be ignored even if supplied.

    Note:
         The resolution must be specified as a tuple in the form (coarse
         resolution, fine resolution). As an example a clock signal from an
         80Mhz TiSapphire laser and a fine resolution on-board the time
         timetagger would give: ``resolution = (12.5e-9, 1e-12)``

    Examples:
        Here we will create a buffer called \'clocked\' (imaginitive)
            that will only except timetags in the ``Clocked`` format, this is
            selected by supplying a pair of values for the resolution
        >>> resolution = (12.5e-9, 1e-12) # 80Mhz Clock and 1ps fine resolution
        >>> clocked_buffer = tangy.TangyBufferClocked("clocked", resolution, 4, int(1e6))

            A new buffer object can be made by connecting to a buffer with
            the correct name
        >>> clocked_buffer_connection = tangy.TangyBufferClocked("clocked")
        ```
    '''
    def __init__(self, name: str, resolution: tuple[float, float] | None = None, length: int | None = None, n_channels: int | None = None) -> None: ...
    def __del__(self) -> None: ...
    def oldest_index(self) -> int: ...
    def push(self, channels: None, timetags: None | None): ...
    @property
    def name(self):
        """ Name of buffer

        Returns:
            (str): buffer name
        """
    @property
    def file_descriptor(self):
        """ File descriptor of buffer

        Returns:
            (str): buffers file descriptor
        """
    @property
    def capacity(self) -> int:
        """ Maximum number of timetags the buffer can hold

        Returns:
            (int): maximum number of timetags
        """
    @property
    def resolution(self) -> tuple[float, float]:
        """ Resolution of timetags in buffer

        Returns:
            (Tuple[float, float]): Tuple of (coarse, fine) resolutions

        """
    @resolution.setter
    def resolution(self, resolution: tuple[float, float]): ...
    @property
    def count(self) -> int:
        """ Number of timetags written to the buffer
        """
    @property
    def index_of_reference(self) -> int: ...
    @property
    def reference_count(self) -> int:
        """ Number of current connections to the buffer

        Tracks number of connections to buffer, used to determine if it is safe
            to delete the backing memory and close the memory mapping.

        Returns:
            (int): number of connections
        """
    @reference_count.setter
    def reference_count(self, int) -> None: ...
    @property
    def n_channels(self) -> int:
        """ Maximum number of channels in the buffer

        Typically set by a device or a file to limit the range of valid channels
            available.

        Returns:
            (int): number of channels
        """
    def time_in_buffer(self) -> float:
        """ Amount of time held in the buffer
        Returns:
            (float): Time between oldest and newest timetags
        """
    def time_range(self) -> tuple[float, float]: ...
    def bins_from_time(self, time: float) -> int:
        """ Convert amount of time to a number of time bins

        Args:
            time (float): Amount of time in seconds

        Returns:
            (int): number of bins

        Note:
            For buffers with the clocked timetag format this will be in units            of the fine resolution.

        """
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
    def coincidence_count(self, read_time: float, window: float, channels: list[int], delays: list[float] | None = None):
        """ Count coincidences

        Args:
            read_time (float): time to integrate over
            window (float): maximum distance between timetags allows
            channels: (List[int]): channels to find coincidences between
            delays: (Optional[List[float]]): delays for each channel

        Returns:
            (int): Number of coincidences found

        """
    def coincidence_collect(self, read_time: float, window: float, channels: list[int], delays: list[int] | None = None) -> RecordsClocked:
        """ Collect coincident timetags

        Args:
            read_time (float): time to integrate over
            window (float): maximum distance between timetags allows
            channels: (List[int]): channels to find coincidences between
            delays: (Optional[List[float]]): delays for each channel

        Returns:
            (RecordsClocked): Records found in coincidence

        """

TangyBufferT: Incomplete

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

class JointHistogramMeasurement:
    def __init__(self, buffer: TangyBuffer, radius: cython.double, channels: list[int], signal: int, idler: int, clock: int | None = 0, delays: list[float] | None = None) -> None: ...
    def collect(self, buffer: TangyBufferT, read_time: float):
        """ Collect timetags for coincidences

        Returns:
            (Union[RecordsStandard, RecordsClocked]):
        """
    def histogram(self, bin_width: int = 1, centre: bool = False) -> JointHistogram: ...

def timetrace(buffer: TangyBufferT, channels: list[int], read_time: float, resolution: float = 10): ...
def find_delay(buffer: TangyBufferT, channel_a: int, channel_b: int, read_time: float, resolution: float = 1e-09, window: float | None = None) -> delay_result: ...
def ptu_read_into(buffer: TangyBufferT, file_handle: None, status: None, n: u64n): ...

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
    def buffer(self):
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

class IFace:
    name: str
    def __init__(self, name) -> None: ...
    @property
    def foo(self):
        """doc"""
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
