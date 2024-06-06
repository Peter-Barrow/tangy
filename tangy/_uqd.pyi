import cython
from ._tangy import TangyBuffer
from _typeshed import Incomplete
from cython.cimports.numpy import npy_intp as npy_intp
from numpy import float64, ndarray as ndarray, uint64, uint8

UQD_ERROR_FLAG: Incomplete

def error_from_bit_set(bit_set: int) -> list[int]: ...

class UQDLogic16:
    '''

    NOTE:
        Linux users will need to add the following file to their system,         ``/etc/udev/rules.d/UQDLogic16.rules`` that contains the following line         ``ATTR{idVendor}=="0bd0", ATTR{idProduct}=="f100", MODE="666"``. This         will ensure that the device does not need additional root privaledges to         operate. After this file has been created the user will have to log out         and the log in again or run the following command         ``sudo udevadm control --reload-rules && udevadm trigger`` to update the         current device rules.

    '''
    def __init__(self, device_id: int = 1, calibrate: bool = True, add_buffer: bool = False, buffer_size: int | None = 10000000) -> None: ...
    def is_open(self) -> bool: ...
    def __close__(self) -> None: ...
    def __exit__(self) -> None: ...
    def calibrate(self) -> None: ...
    @property
    def led_brightness(self) -> int:
        """
        Brightness of front panel LED.

        Args:
            percent (int): brightness in percent
        """
    @led_brightness.setter
    def led_brightness(self, percent: int):
        """
        Brightness of front panel LED.

        Returns:
            percent (int): brightness in percent
        """
    @property
    def fpga_version(self) -> cython.int:
        """
        Version of FPGA design on device.

        Returns:
            (int): fpga design version
        """
    @property
    def resolution(self) -> float:
        """
        Get the resolution of the device.

        Depending on the device firmware this will return either 78.125ps or
        156.25ps.

        Returns:
            (float): resolution
        """
    @property
    def number_of_channels(self) -> int:
        """
        Number of channels enabled on the device.

        Depending on loaded firmware this will return either 8 or 16

        Returns:
            (int): number of useable input channels
        """
    @property
    def input_threshold(self) -> list[float64]:
        """
        Input thresholds

        Returns:
            List[float64]: Currently set input thresholds
        """
    @input_threshold.setter
    def input_threshold(self, value: tuple[int, float64]):
        """
        Set input threshold for a channel.

        Takes a tuple in the form Tuple[channel, voltage], channel is the range
        0 <= channel < UQD.number_of_channels and voltage must be the range of
        -2V to + 2V in steps of 15mV

        Args:
            value (Tuple[int, float64]): Tuple of (channel, voltage)

        """
    @property
    def inversion(self) -> list[uint8]:
        """
        Channels set to use negative edge triggering

        Returns:
            (List[uint8]): List of channels set to trigger on negative edges
        """
    @inversion.setter
    def inversion(self, invert: tuple[uint8, uint8]):
        """
        Channels set to use negative edge triggering

        Args:
            channel (uint8): channel to enable negative edge triggering on
        """
    def inversion_apply(self) -> None: ...
    @property
    def input_delay(self) -> float64:
        """
        Delays in seconds set on each channel

        Returns:
            (float64): delays on each channel in seconds
        """
    @input_delay.setter
    def input_delay(self, value: tuple[int, float64]):
        """
        Set delay of input channel

        Args:
            value (Tuple[int, float64]): Tuple of (channel, delay)
        """
    @property
    def function_generator(self) -> tuple[int, int]:
        """
        Function generator period and width, both in units of 5ns
        """
    @function_generator.setter
    def function_generator(self, value: tuple[int, int]): ...
    @property
    def external_10MHz_reference(self) -> bool:
        """
        """
    @external_10MHz_reference.setter
    def external_10MHz_reference(self, value: bool): ...
    def start_timetags(self) -> None:
        """
        Start transmitting timetags from the device to the host computer
        """
    def stop_timetags(self) -> None:
        """
        Stop transmitting timetags from the device to the host computer
        """
    def read_tags(self) -> tuple[int, list[uint8], list[uint64]]: ...
    @property
    def filter_min_count(self) -> int:
        """
        Minimum size of a group to be transmitted to the host computer.

        Returns:
            (int): Minimum size of a group to be transmitted
        """
    @filter_min_count.setter
    def filter_min_count(self, count: int):
        """
        Set the minimum size of a group

        Args:
            count (int): size of group
        """
    @property
    def filter_max_time(self) -> cython.double:
        """
        Maximum time between two pulses in the same group.

        Returns:
            (float): maximum time between two pulses in the same group
        """
    @filter_max_time.setter
    def filter_max_time(self, max_time: cython.double):
        """
        Maximum time between two pulses in the same group.

        Args:
            time (float): maximum time between two pulses in the same group
        """
    @property
    def exclusion(self) -> list[uint8]:
        """
        """
    @exclusion.setter
    def exclusion(self, value: tuple[int, int]): ...
    def exclusion_apply(self) -> None: ...
    @property
    def level_gate(self) -> bool:
        """
        """
    @level_gate.setter
    def level_gate(self, value: bool): ...
    @property
    def time_gating(self) -> bool:
        """
        """
    @time_gating.setter
    def time_gating(self, value: bool): ...
    @property
    def time_gate_width(self) -> int:
        """
        """
    @time_gate_width.setter
    def time_gate_width(self, duration: int): ...
    def check_errors(self) -> dict: ...
    def buffer(self) -> TangyBuffer:
        """
        Acquire buffer
        """
    def write_to_buffer(self):
        """
        Write tags directly into buffer
        """
