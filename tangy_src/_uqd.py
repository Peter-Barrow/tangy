import cython
import time
from cython.cimports import _uqd as _uqd
from cython.cimports.libc.stdlib import malloc, free
from cython.cimports.libcpp import bool as cbool
from typing import List, Tuple, Optional, Union
from cython.cimports.libc.stdint import uint8_t as u8
from cython.cimports.libc.stdint import uint64_t as u64
from cython.cimports.libc.stdint import int64_t as i64
from numpy import ndarray, zeros, uint8, uint64, float64

from ._tangy import TangyBufferStandard


UQD_ERROR_FLAG = {
    1: {
        "DataOverflow",
        "An overflow in the 512 k values SRAM FIFO has been detected. \
        The time-tag generation rate is higher than the USB transmission rate.",
    },
    2: {
        "NegFifoOverflow",
        "Internal reason, should never occur"
    },
    4: {
        "PosFifoOverflow",
        "Internal reason, should never occur"
    },
    8: {
        "DoubleError",
        "One input had two pulses within the coincidence window."
    },
    16: {
        "InputFifoOverflow",
        "More than 1024 successive tags were detected with a rate greater 100 MHz"
    },
    32: {
        "10MHzHardError",
        "The 10 MHz input is not connected or connected to a wrong type of signal."
    },
    64: {
        "10MHzSoftError",
        "The 10 MHz input is connected, but the frequency is not 10 MHz."
    },
    128: {
        "OutFifoOverflow",
        "Internal error, should never occur"
    },
    256: {
        "OutDoublePulse",
        "An output pulse was generated, while another pulse was still present \
        on the same output. The pulse length is too long for the given rate."
    },
    512: {
        "OutTooLate",
        "The internal processing was too slow. This is because the output \
        event queue is too small for the given rate. Increase the value with \
        SetOutputEventQueue()"
    },
}


@cython.cclass
class UQD:
    """

    NOTE:
        Linux users will need to add the following file to their system, \
        ``/etc/udev/rules.d/UQDLogic16.rules`` that contains the following line \
        ``ATTR{idVendor}=="0bd0", ATTR{idProduct}=="f100", MODE="666"``. This \
        will ensure that the device does not need additional root privaledges to \
        operate. After this file has been created the user will have to log out \
        and the log in again or run the following command \
        ``sudo udevadm control --reload-rules && udevadm trigger`` to update the \
        current device rules.

    """

    _c_timetag: _uqd.CTimeTag
    _c_logic: cython.pointer(_uqd.CLogic)

    _channel_ptr: cython.pointer(u8)
    _timetag_ptr: cython.pointer(cython.longlong)

    _device_id: cython.int
    _number_of_channels: cython.int
    _led_brightness: cython.int
    _filter_min_count: cython.int
    _filter_max_time: cython.double
    _logic_enabled: cython.int
    _gating_enabled: cython.int
    _input_thresholds: ndarray(float64)
    _inversion: ndarray(uint8)
    _input_delay: ndarray(float64)
    _function_generator_period: int
    _function_generator_high: int
    _exclusion: ndarray(uint8)
    _10MHz: bool = False
    _time_gate: bool = False
    _gate_width: int
    _buffer: TangyBufferStandard

    def __init__(self, device_id: int = 1, calibrate: bool = True,
                 add_buffer: bool = False,
                 buffer_size: Optional[int] = 10_000_000):

        if device_id < 1:
            raise ValueError("device_id must be >= 1")

        _uqd.ctimetag_new(cython.address(self._c_timetag))
        _uqd.clogic_new(cython.address(self._c_timetag), self._c_logic)

        if self.is_open() is True:
            raise ResourceWarning(f"Device with id={device_id} in use")

        self._device_id = device_id
        self._c_timetag.Open(device_id)
        self._input_thresholds = zeros(self.number_of_channels, dtype=float64)
        self._inversion = zeros(self.number_of_channels, dtype=uint8)
        self._input_delay = zeros(self.number_of_channels, dtype=float64)
        self._exclusion = zeros(self.number_of_channels, dtype=uint8)

        if calibrate:
            self.calibrate()

        if add_buffer:
            self._buffer = TangyBufferStandard(f"uqdbuffer{self._device_id}",
                                               self.resolution,
                                               buffer_size,
                                               self.number_of_channels)
        return

    def is_open(self) -> bool:
        res: int = self._c_timetag.IsOpen()
        if res == 1:
            return True

        return False

    def __close__(self):
        print('Gracefully closing connection to device...')
        self._c_timetag.Close()

    def __exit__(self):
        print('Gracefully closing connection to device...')
        self._c_timetag.Close()

    def calibrate(self):
        self._c_timetag.Calibrate()

    @property
    def led_brightness(self) -> int:
        """
        Brightness of front panel LED.

        Args:
            percent (int): brightness in percent
        """
        return self._led_brightness

    @led_brightness.setter
    def led_brightness(self, percent: int):
        """
        Brightness of front panel LED.

        Returns:
            percent (int): brightness in percent
        """
        if (percent < 0) or (percent > 100):
            raise ValueError("led_brightness must be in an integer between 0 and 100")
        self._c_timetag.SetLedBrightness(percent)
        self._led_brightness = percent

    @property
    def fpga_version(self) -> cython.int:
        """
        Version of FPGA design on device.

        Returns:
            (int): fpga design version
        """
        return self._c_timetag.GetFpgaVersion()

    @property
    def resolution(self) -> float:
        """
        Get the resolution of the device.

        Depending on the device firmware this will return either 78.125ps or
        156.25ps.

        Returns:
            (float): resolution
        """
        res: cython.double = self._c_timetag.GetResolution()
        return res

    @property
    def number_of_channels(self) -> int:
        """
        Number of channels enabled on the device.

        Depending on loaded firmware this will return either 8 or 16

        Returns:
            (int): number of useable input channels
        """
        return self._c_timetag.GetNoInputs()

    @property
    def input_threshold(self) -> List[float64]:
        """
        Input thresholds

        Returns:
            List[float64]: Currently set input thresholds
        """
        return self._input_thresholds

    @input_threshold.setter
    def input_threshold(self, value: Tuple[int, float64]):
        """
        Set input threshold for a channel.

        Takes a tuple in the form Tuple[channel, voltage], channel is the range
        0 <= channel < UQD.number_of_channels and voltage must be the range of
        -2V to + 2V in steps of 15mV

        Args:
            value (Tuple[int, float64]): Tuple of (channel, voltage)

        """

        n: int = self.number_of_channels
        channel: int = value[0]
        if (channel < 0) or (channel >= n):
            raise ValueError(f"channel must be in range 0 <= channel < {n}")

        voltage: float64 = value[1]
        if abs(voltage) > 2:
            raise ValueError("abs(voltage) must be <= 2V")

        self._input_thresholds[channel] = voltage
        self._c_timetag.SetInputThreshold(channel, voltage)

    @property
    def inversion(self) -> List[uint8]:
        """
        Channels set to use negative edge triggering

        Returns:
            (List[uint8]): List of channels set to trigger on negative edges
        """
        return self._inversion

    @inversion.setter
    def inversion(self, channel: uint8):
        """
        Channels set to use negative edge triggering

        Args:
            channel (uint8): channel to enable negative edge triggering on
        """

        n: int = self.number_of_channels
        if (channel < 0) or (channel >= n):
            raise ValueError(f"channel must be in range 0 <= channel < {n}")
        self._inversion[channel] = 1

    @property
    def input_delay(self) -> float64:
        """
        Delays in seconds set on each channel

        Returns:
            (float64): delays on each channel in seconds
        """
        return self._input_delay

    @input_delay.setter
    def input_delay(self, value: Tuple[int, float64]):
        """
        Set delay of input channel

        Args:
            value (Tuple[int, float64]): Tuple of (channel, delay)
        """

        n: int = self.number_of_channels
        channel: int = value[0]
        if (channel < 0) or (channel >= n):
            raise ValueError(f"channel must be in range 0 <= channel < {n}")

        max_delay: float = ((2**18) - 1) * self.resolution
        delay: int = value[0] // self.resolution
        if (delay < 0) or (delay > max_delay):
            raise ValueError(f"Delay is out of range, must be >= 0 or < {max_delay}s")

        self._input_delay[channel] = delay

    @property
    def function_generator(self) -> Tuple[int, int]:
        """
        Function generator period and width, both in units of 5ns
        """
        return (self._function_generator_period, self._function_generator_high)

    @function_generator.setter
    def function_generator(self, value: Tuple[int, int]):
        period: int = value[0]
        high: int = value[0]
        self._c_timetag.SetFG(period, high)
        self._function_generator_period = period
        self._function_generator_high = high

    @property
    def external_10MHz_reference(self) -> bool:
        """
        """
        return self._10MHz

    @external_10MHz_reference.setter
    def external_10MHz_reference(self, value: bool):

        use: cbool
        if value is True:
            use = True
        else:
            use = False

        self._c_timetag.Use10MHz(use)
        self._external_10MHz_reference = value

    def start_timetags(self):
        """
        Start transmitting timetags from the device to the host computer
        """
        self._c_timetag.StartTimetags()

    def stop_timetags(self):
        """
        Stop transmitting timetags from the device to the host computer
        """
        self._c_timetag.StopTimetags()

    @cython.ccall
    def read_tags(self) -> Tuple[int, List[uint8], List[uint64]]:
        count: int = self._c_timetag.ReadTags(self._channel_ptr, self._timetag_ptr)
        channel_arr: uint8[:] = zeros(count, dtype=uint8)
        timetag_arr: uint64[:] = zeros(count, dtype=uint64)

        channel_view: u8[:] = channel_arr
        timetag_view: u64[:] = timetag_arr

        i: cython.Py_ssize_t
        for i in range(count):
            channel_view[i] = channel_arr[i]
            timetag_view[i] = timetag_arr[i]

        return (count, channel_arr, timetag_arr)

    @property
    def filter_min_count(self) -> int:
        """
        Minimum size of a group to be transmitted to the host computer.

        Returns:
            (int): Minimum size of a group to be transmitted
        """
        return self._filter_min_count

    @filter_min_count.setter
    def filter_min_count(self, count: int):
        """
        Set the minimum size of a group

        Args:
            count (int): size of group
        """
        self._filter_min_count = count

    @property
    def filter_max_time(self) -> cython.double:
        """
        Maximum time between two pulses in the same group.

        Returns:
            (float): maximum time between two pulses in the same group
        """
        return self._filter_max_time

    @filter_max_time.setter
    def filter_max_time(self, time: cython.double):
        """
        Maximum time between two pulses in the same group.

        Args:
            time (float): maximum time between two pulses in the same group
        """
        bins: int = time // self.resolution
        self._filter_max_time = time

    @property
    def exclusion(self) -> List[uint8]:
        """
        """
        return self._exclusion

    @exclusion.setter
    def exclusion(self, value: int):
        n: int = self.number_of_channels
        channel: int = value[0]
        if (channel < 0) or (channel >= n):
            raise ValueError(f"channel must be in range 0 <= channel < {n}")
        self._c_timetag.SetFilterException(channel)
        self._exclusion[channel] = 1

    @property
    def level_gate(self) -> bool:
        """
        """
        return self._c_timetag.LevelGateActive()

    @level_gate.setter
    def level_gate(self, value: bool):

        use: cbool
        if value is True:
            use = True
        else:
            use = False

        self._c_timetag.UseLevelGate(use)

    @property
    def time_gating(self) -> bool:
        """
        """
        return self._time_gating

    @time_gating.setter
    def time_gating(self, value: bool):
        use: cbool
        if value is True:
            use = True
        else:
            use = False
        self._c_timetag.UseTimetagGate(use)
        self._time_gating = value

    @property
    def time_gate_width(self) -> int:
        """
        """
        return self._time_gate_width

    @time_gate_width.setter
    def time_gate_width(self, duration: int):
        self._c_timetag.SetGateWidth(duration)
        self._time_gate_width = duration

    def error_text(self):
        ...

    def buffer(self) -> TangyBufferStandard:
        return self._buffer

    @cython.ccall
    def write_to_buffer(self):
        (count, channels, tags) = self.read_tags()
        self._buffer.push(channels, tags)

