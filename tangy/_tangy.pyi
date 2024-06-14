import cython
from cython.cimports import _tangy as _tangy
from cython.cimports.libc.stdint import int64_t as i64
from enum import Enum
from numpy import uint64 as u64n

__all__ = ['tangy_config_location', 'Records', 'JointHistogram', 'centre_histogram', 'bin_histogram', 'delay_result', 'TangyBufferType', 'TangyBuffer', 'PTUFile', 'buffer_list_update', 'buffer_list_append', 'buffer_list_delete_all', 'buffer_list_show']

def tangy_config_location() -> str: ...

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
    count: u64n
    resolution: float
    clock_period: float
    channels: None
    timetags: None | tuple[None, None]

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
    """ Format of timetags to use in instance of TangyBuffer
    """
    Standard: int
    Clocked: int

class TangyBuffer:
    '''Interface to underlying ring buffer

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
        Creation of a TangyBuffer object for both the ``Standard`` and         ``Clocked`` timetag formats that can hold 1,000,000 timetags for a         device with 4 channels. The method to connect to these buffers is also         shown. This method of creating new buffers and connecting to existing         ones allows the user to hold on to and continously read timetags from         a device in one process and then connect to that buffer in another to         perform analysis on the current data.
        === "Buffer in ``Standard`` format"
            ```python
            # Here we will create a buffer called \'standard\' (imaginitive)
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
            # Here we will create a buffer called \'clocked\' (imaginitive)
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
    '''
    def __init__(self, name: str, resolution: float = 0.1, clock_period: float = 1.0, channel_count: int = 4, capacity: int = 10000000, format: TangyBufferType = ...) -> None: ...
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
    def oldest_time(self) -> float: ...
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
    def time_range(self) -> tuple[float, float]: ...
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
    def clear(self) -> None: ...
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
    def coincidence_count(self, read_time: float, window: float, channels: list[int], delays: list[float] | None = None) -> int:
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
    def coincidence_collect(self, read_time: float, window: float, channels: list[int], delays: list[float] | None = None) -> Records:
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
    def timetrace(self, channels: int | list[int], read_time: float, resolution: float = 10.0):
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
    def relative_delay(self, channel_a: int, channel_b: int, read_time: float, resolution: float = 1e-09, window: float | None = None) -> delay_result:
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
    def joint_delay_histogram(self, signal: int, idler: int, channels: list[int], read_time: float, radius: float, delays: list[float] | None = None, clock: int | None = None, bin_width: int = 1, centre: bool = True) -> JointHistogram:
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

    '''
def buffer_list_append(buffer: TangyBuffer):
    """
    Adds the configuration of a buffer to the Tangy configuration directory

    Args:
        buffer (TangyBuffer): buffer with configuration to save
    """
def buffer_list_delete_all() -> None: ...
def buffer_list_show() -> None: ...
