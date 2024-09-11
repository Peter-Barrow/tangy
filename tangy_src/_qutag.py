import cython
from cython.cimports import _qutag as _qutag

from enum import Enum

import time
from typing import Optional, List, Tuple
from cython.cimports.libc.stdint import uint8_t as u8
from cython.cimports.libc.stdint import uint16_t as u16
from cython.cimports.libc.stdint import uint32_t as u32
from cython.cimports.libc.stdint import uint64_t as u64
from cython.cimports.libc.stdint import int8_t as i8
from cython.cimports.libc.stdint import int32_t as i32
from cython.cimports.libc.stdint import int64_t as i64
from numpy import uint8 as u8n
from numpy import int32 as i32n
from numpy import uint32 as u32n
from numpy import uint64 as u64n
from numpy import float64 as f64n

from numpy import ndarray, zeros, uint8, uint64, float64, asarray
from cython.cimports.numpy import PyArray_SimpleNewFromData, npy_intp, NPY_UINT8, NPY_INT64

from ._tangy import TangyBuffer


@cython.cfunc
def bool_from_bl32(boolean: i32):
    return boolean == 1


@cython.cfunc
def bl32_from_bool(boolean: bool):
    if boolean is True:
        return 1

    return 0


@cython.cfunc
def set_field(bit_flag: _qutag.Int32,
              target: _qutag.Int32,
              max_field: _qutag.Int32) -> _qutag.Int32:

    if target > max_field:
        return 0

    return bit_flag | target


@cython.ccall
def _check_error_and_raise(rc: cython.int):
    lib_tdc_error_messages: dict[int, str] = {
        0: "TDC_Ok, Success",
        -1: "TDC_Error, Unspecified error",
        1: "TDC_Timeout, Receive timed out",
        2: "TDC_NotConnected, No connection was established",
        3: "TDC_DriverError, Error accessing the USB driver",
        7: "TDC_DeviceLocked, Can't connect device because already in use",
        8: "TDC_Unknown, Unknown error",
        9: "TDC_NoDevice, Invalid device number used in call",
        10: "TDC_OutOfRange, Parameter in function call is out of range",
        11: "TDC_CantOpen, Failed to open specified file",
        12: "TDC_NotInitialized, Library has not been initialized",
        13: "TDC_NotEnabled, Requested feature is not enabled",
        14: "TDC_NotAvailable, Requested feature is not available",
    }

    if rc != 0:
        raise OSError(lib_tdc_error_messages[rc])


# @cython.cfunc
# def _extract_positions_from_bitflags(
#     bit_flag: _qutag.Int32,
#         total_flags: cython.int
# ) -> Optional[List[int]]:
#
#     positions = zeros(total_flags, dtype=u8n)
#     positions_view: u8n[:] = positions
#
#     result: _qutag.bf__Int32_Result = _qutag.bf__Int32_extract_positions(
#         bit_flag, total_flags, cython.address(positions_view[0]))
#
#     if result.Ok is False:
#         return None
#
#     return positions.to_list()


class SignalConditioning(Enum):
    LVTTL = 1
    NIM = 2
    MISC = 3
    NONE = 4


class SignalEdge(Enum):
    Falling = 0
    Rising = 1


@cython.dataclasses.dataclass(frozen=True)
class DeviceChannel:
    channel: i32 = cython.dataclasses.field()
    conditioning: SignalConditioning = cython.dataclasses.field()
    edge: SignalEdge = cython.dataclasses.field()
    threshold: cython.double = cython.dataclasses.field()


class FilterType(Enum):
    No_Filter = 0
    Mute = 1
    Coincidence = 2
    Sync = 3
    Invalid = 4


@cython.dataclasses.dataclass(frozen=True)
class OutputFilter:
    channel: cython.int = cython.dataclasses.field()
    filter_type: FilterType = cython.dataclasses.field()
    stop_channels: List[cython.int] = cython.dataclasses.field()


@cython.cclass
class QuTagHR:

    _device_id: cython.int
    _resolution: cython.double
    _device_type: _qutag.TDC_DevType
    _number_of_channels: u8
    _features_flag: _qutag.TDC_FeatureFlags
    _have_buffer: bool
    _buffer: TangyBuffer

    def __init__(self,
                 device_id: int = -1,
                 calibrate: bool = False,
                 add_buffer: bool = False,
                 buffer_size: Optional[int] = 10_000_000):

        self._device_id = device_id

        rc: cython.int = _qutag.TDC_init(self._device_id)
        _check_error_and_raise(rc)

        _ = self.number_of_channels

        if calibrate is True:
            self.calibrate()

        self._have_buffer = False
        if add_buffer is True:
            self._buffer = TangyBuffer(f"qutagbuffer{self._device_id}",
                                       resolution=self.resolution,
                                       capacity=buffer_size,
                                       channel_count=self.number_of_channels)
            self._have_buffer = True

    @property
    def version(self) -> float:
        """doc"""
        version: cython.double = _qutag.TDC_getVersion()
        return version

    @property
    def resolution(self) -> float:
        _qutag.TDC_getTimebase(cython.address(self._resolution))
        return self._resolution

    @property
    def device_type(self) -> str:
        self._device_type = _qutag.TDC_getDevType()

        if self._device_type == _qutag.TDC_DevType.DEVTYPE_QUTAG_MC:
            return "Multichannel"

        if self._device_type == _qutag.TDC_DevType.DEVTYPE_QUTAG_HR:
            return "High resolution"

        return "No device / simulator"

    @property
    def features(self) -> dict[str, bool]:
        self._features_flag = _qutag.TDC_checkFeatures()

        bitflags: dict[str, u16] = {
            "hbt": 0x0001,
            "lifetime": 0x0002,
            "markers": 0x0020,
            "filters": 0x0040,
            "external clock": 0x0080,
            "multi-device synchronisation": 0x0100,
        }

        enabled: dict[str, bool] = {
            "hbt": False,
            "lifetime": False,
            "markers": False,
            "filters": False,
            "external clock": False,
            "multi-device synchronisation": False,
        }

        for key, flag in bitflags.items():
            if (self._features_flag & flag) == flag:
                enabled[key] = True

        return enabled

    @property
    def number_of_channels(self) -> int:
        self._number_of_channels = _qutag. TDC_getChannelCount()
        return self._number_of_channels

    @property
    def clock_state(self) -> dict[str, bool]:
        locked: i32 = 0
        uplink: i32 = 0

        rc: cython.int = _qutag.TDC_getClockState(
            cython.address(locked), cython.address(uplink))
        _check_error_and_raise(rc)

        state: dict[str, bool] = {
            "locked": locked == 1,
            "uplink": uplink == 1,
        }

        return state

    @property
    def disable_clock_reset(self) -> bool:
        """doc"""
        disabled: i32 = 0
        rc: cython.int = _qutag.TDC_getClockResetDisabled(
            cython.address(disabled))
        _check_error_and_raise(rc)

        return disabled == 1

    @disable_clock_reset.setter
    def disable_clock_reset(self, disable: bool):
        disabled: i32 = 0

        if disable is True:
            disabled = 1

        rc: cython.int = _qutag.TDC_disableClockReset(disabled)
        _check_error_and_raise(rc)

    @property
    def single_stop(self) -> bool:
        """doc"""
        preselect: i32 = bl32_from_bool(False)
        rc: cython.int = _qutag.TDC_getSingleStopPreselection(
            cython.address(preselect))
        _check_error_and_raise(rc)

        return bool_from_bl32(preselect)

    @single_stop.setter
    def single_stop(self, value: bool):
        preselect: i32 = bl32_from_bool(value)
        rc = _qutag.TDC_preselectSingleStop(preselect)
        _check_error_and_raise(rc)

    def calibrate(self):
        rc: i32 = _qutag.TDC_startCalibration()
        _check_error_and_raise(rc)

        calibrating: i32 = bl32_from_bool(True)
        while bool_from_bl32(calibrating):
            time.sleep(1)
            rc = _qutag.TDC_getCalibrationState(cython.address(calibrating))
            _check_error_and_raise(rc)

    @property
    def enabled_channels(self) -> Tuple[bool, List[int]]:
        enabled: List[int] = []
        result: cython.bint = False

        start_enabled: _qutag.Bln32 = bl32_from_bool(True)
        channel_mask: _qutag.Int32 = 0

        rc: cython.int = _qutag.TDC_getChannelsEnabled(
            cython.address(start_enabled),
            cython.address(channel_mask))
        _check_error_and_raise(rc)

        channel_max: _qutag.Int32 = 1 << self._number_of_channels

        for i in range(self._number_of_channels):
            result = _qutag.bf__Int32_contains(
                channel_mask,
                1 << i,
                channel_max)

            if result is True:
                enabled.append(i + 1)
                _qutag.bf__Int32_unset(channel_mask,
                                       1 << i,
                                       channel_max)
        return (bool_from_bl32(start_enabled), enabled)

    @enabled_channels.setter
    def enabled_channels(self, value: Tuple[bool, List[int]]):
        enabled: _qutag.Bln32 = bl32_from_bool(value[0])
        channels: List[int] = value[1]

        channel_max: _qutag.Int32 = 1 << self._number_of_channels
        result: _qutag.bf__Int32_Result
        channel_mask: _qutag.Int32 = 0
        for c in channels:
            result = _qutag.bf__Int32_set(
                channel_mask,
                1 << (c - 1),
                channel_max
            )
            if result.Ok is False:
                raise ValueError
            channel_mask = result.bit_flag

        rc: cython.int = _qutag.TDC_enableChannels(enabled, channel_mask)

        _check_error_and_raise(rc)

    @property
    def enabled_markers(self) -> List[int]:
        marker_mask: _qutag.Int32 = 0
        rc: cython.int = _qutag.TDC_getMarkersEnabled(
            cython.address(marker_mask))

        _check_error_and_raise(rc)

        markers: List[int] = []
        marker_min: cython.int = 0
        marker_max: cython.int = 9
        result: cython.bint
        for i in range(marker_min, marker_max):
            result = _qutag.bf__Int32_contains(
                marker_mask,
                1 << i,
                1 < marker_max)

            if result is True:
                markers.append(i)
                _qutag.bf__Int32_unset(marker_mask,
                                       1 << i,
                                       1 << marker_max)
        return markers

    @enabled_markers.setter
    def enabled_markers(self, markers: List[int]):
        marker_mask: _qutag.Int32 = 0

        marker_min: cython.int = 0
        marker_max: cython.int = 9
        result: _qutag.bf__Int32_Result
        for m in markers:
            assert m >= marker_min
            assert m <= marker_max
            result = _qutag.bf__Int32_set(marker_mask,
                                          1 << m,
                                          1 << marker_max)
            if result.Ok is False:
                raise ValueError
            marker_mask = result.bit_flag

        rc: cython.int = _qutag.TDC_enableMarkers(marker_mask)

        _check_error_and_raise(rc)

    @property
    def configure_channels(self) -> List[DeviceChannel]:
        conditions: List[DeviceChannel] = []

        edge: _qutag.Bln32 = 0
        threshold: cython.double = 0
        rc: cython.int = 0
        for i in range(self._number_of_channels):
            rc = _qutag.TDC_getSignalConditioning(i,
                                                  cython.address(edge),
                                                  cython.address(threshold))
            _check_error_and_raise(rc)

            conditions.append(DeviceChannel(i,
                                            SignalConditioning.MISC,
                                            edge,
                                            threshold))
        return conditions

    @configure_channels.setter
    def configure_channels(self, conditions: List[DeviceChannel]):
        rc: cython.int = 0

        for cond in conditions:
            assert cond.channel >= 0
            assert cond.channel <= self._number_of_channels

            assert cond.threshold >= -2
            assert cond.threshold <= 3

            rc = _qutag.TDC_configureSignalConditioning(
                cond.channel,
                cond.conditioning.value,
                cond.edge.value,
                cond.threshold)

            _check_error_and_raise(rc)

    @property
    def sync_divider(self) -> Tuple[int, bool]:
        divider: _qutag.Int32 = 0
        reconstruct: _qutag.Bln32 = 0

        rc: cython.int = _qutag.TDC_getSyncDivider(cython.address(divider),
                                                   cython.address(reconstruct))

        _check_error_and_raise(rc)
        return (divider, bool_from_bl32(reconstruct))

    @sync_divider.setter
    def sync_divider(self, values: Tuple[int, bool]):
        divider: cython.int = values[0]
        reconstruct: _qutag.Bln32 = bl32_from_bool(values[1])

        rc: cython.int = _qutag.TDC_configureSyncDivider(divider, reconstruct)

        _check_error_and_raise(rc)

    @property
    def coincidence_window(self) -> cython.double:
        (cc, exp) = self._device_params()
        return cc

    @coincidence_window.setter
    def coincidence_window(self, window: cython.double):

        assert window >= 0

        coincidence_window: _qutag.Int32 = int(round(window / (1e-12)))

        assert coincidence_window <= 2_000_000_000, \
            "Max coincidence window is 2_000_000_000 ps"

        rc: cython.int = _qutag.TDC_setCoincidenceWindow(coincidence_window)

        _check_error_and_raise(rc)

    @property
    def output_filter(self) -> List[OutputFilter]:
        output_filters: List[OutputFilter] = []

        channel_in_min: cython.int = 1
        channel_in_max: cython.int = 5
        channel_mask_max: cython.int = self._number_of_channels

        filter_type: _qutag.TDC_FilterType = _qutag.TDC_FilterType.FILTER_NONE
        channel_mask: _qutag.Int32 = 0
        rc: cython.int = 0
        for i in range(channel_in_min, channel_in_max):
            rc = _qutag.TDC_getFilter(i,
                                      cython.address(filter_type),
                                      cython.address(channel_mask))
            _check_error_and_raise(rc)

            stop_channels: List[int] = []
            result: cython.bint
            for c in range(channel_in_min, channel_mask_max):
                result = _qutag.bf__Int32_contains(
                    channel_mask,
                    1 << c,
                    1 < channel_mask_max)

                if result is True:
                    stop_channels.append(c)
                    _qutag.bf__Int32_unset(
                        channel_mask,
                        1 << c,
                        1 < channel_mask_max)

            output_filters.append(OutputFilter(i, filter_type, stop_channels))
        return output_filters

    @output_filter.setter
    def output_filter(self, output_filters: List[OutputFilter]):
        rc: cython.int = 0
        for o in output_filters:
            assert o.channel >= 1
            assert o.channel <= 5

            assert min(o.stop_channels) >= 1
            assert max(o.stop_channels) <= self._number_of_channels

            channel_mask: _qutag.Int32 = 0
            for c in output_filters.stop_channels:
                result = _qutag.bf__Int32_set(
                    channel_mask,
                    1 << c,
                    1 << self._number_of_channels)

                if result.Ok is False:
                    raise ValueError
                channel_mask = result.bit_flag

            rc = _qutag.TDC_configureFilter(
                o.channel, o.filter_type, channel_mask)

            _check_error_and_raise(rc)

    @property
    def exposure_time(self) -> cython.double:
        (cc, exp) = self._device_params()
        return exp

    @exposure_time.setter
    def exposure_time(self, exposure: cython.double):
        assert exposure >= 0

        assert exposure <= ((2**16) / 1e3), \
            "Exposure time must not exceed 65.535s"

        exp_time: _qutag.Int32 = round(exposure / 1e3)

        rc: cython.int = _qutag.TDC_setExposureTime(exp_time)

        _check_error_and_raise(rc)

    def _device_params(self) -> Tuple[float, float]:
        coincidence_window: _qutag.Int32 = 0
        exposure: _qutag.Int32 = 0

        rc: cython.int = _qutag.TDC_getDeviceParams(
            cython.address(coincidence_window),
            cython.address(exposure))

        _check_error_and_raise(rc)

        return (
            float(coincidence_window) * 1e12,
            float(exposure) / 1e3
        )

    @property
    def channel_delay(self) -> List[Tuple[int, float]]:
        delays: List[Tuple[int, float]] = []

        delay: _qutag.Int32 = 0
        rc: cython.int = 0
        for i in range(self._number_of_channels):
            rc = _qutag.TDC_getChannelDelay(i, cython.address(delay))
            _check_error_and_raise(rc)
            delays.append((i, float(delay) * (1e9)))

        return delays

    @channel_delay.setter
    def channel_delay(self, delays: Tuple[int, float]):
        _ch: _qutag.Int32 = 0
        _d: _qutag.Int32 = 0
        rc: cython.int = 0
        for (ch, d) in delays:
            _ch = ch
            _d = int(d * 1e9)

            rc = _qutag.TDC_setChannelDelay(_ch, _d)
            _check_error_and_raise(rc)

    def lost_data(self) -> bool:
        lost: _qutag.Bln32 = 0
        rc: cython.int = _qutag.TDC_getDataLost(cython.address(lost))
        _check_error_and_raise(rc)
        return bool_from_bl32(lost)

    @property
    def internal_buffer_size(self) -> int:
        buffer_size: _qutag.Int32 = 0
        rc: cython.int = _qutag.TDC_getTimestampBufferSize(
            cython.address(buffer_size))
        _check_error_and_raise(rc)

        return buffer_size

    @internal_buffer_size.setter
    def internal_buffer_size(self, buffer_size: int):
        _buffer_size: _qutag.Int32 = buffer_size
        rc: cython.int = _qutag.TDC_setTimestampBufferSize(_buffer_size)
        _check_error_and_raise(rc)

    def buffer(self) -> TangyBuffer:
        return self._buffer

    @cython.ccall
    def read_from_internal_buffer(self, reset: bool = True):
        _reset: _qutag.Bln32 = bl32_from_bool(reset)
        count: _qutag.Int32 = 0
        timestamps: _qutag.Int64 = 0
        channels: _qutag.Uint8 = 0

        rc: cython.int = _qutag.TDC_getLastTimestamps(
            _reset,
            cython.address(timestamps),
            cython.address(channels),
            cython.address(count))
        _check_error_and_raise(rc)

        print(count)

        # shape: npy_intp[1] = [count]

        # array_channels = PyArray_SimpleNewFromData(
        #     1, cython.address(shape[0]), NPY_UINT8, cython.address(channels))

        # array_timestamps = PyArray_SimpleNewFromData(
        #     1, cython.address(shape[0]), NPY_INT64, cython.address(timestamps))

        # return (array_channels[:count].copy(), array_timestamps[:count].copy())

    @cython.ccall
    def write_to_buffer(self, reset: bool = True):
        _reset: _qutag.Bln32 = bl32_from_bool(reset)
        count: _qutag.Int32 = 0
        timestamps: _qutag.Int64 = 0
        channels: _qutag.Uint8 = 0

        rc: cython.int = _qutag.TDC_getLastTimestamps(
            _reset,
            cython.address(timestamps),
            cython.address(channels),
            cython.address(count))
        _check_error_and_raise(rc)

        shape: npy_intp[1] = [count]

        array_channels = PyArray_SimpleNewFromData(
            1, cython.address(shape[0]), NPY_UINT8, cython.address(channels))

        array_timestamps = PyArray_SimpleNewFromData(
            1, cython.address(shape[0]), NPY_INT64, cython.address(timestamps))

        self._buffer.push(array_channels[:count] - 1,
                          asarray(array_timestamps[:count], uint64))
        return self._buffer.count
