import cython
import time
from typing import List, Tuple
from cython.cimports.libc.stdint import uint8_t as u8
from cython.cimports.libc.stdint import uint16_t as u16
from cython.cimports.libc.stdint import uint32_t as u32
from cython.cimports.libc.stdint import uint64_t as u64
from cython.cimports.libc.stdint import int8_t as i8
from cython.cimports.libc.stdint import int32_t as i32
from cython.cimports.libc.stdint import int64_t as i64
from numpy import uint8 as u8n
from numpy import uint64 as u64n
from numpy import float64 as f64n

from cython.cimports import _qutag


@cython.cfunc
def bool_from_bl32(boolean: i32) -> bool:
    return boolean == 1


@cython.cfunc
def bl32_from_bool(boolean: bool) -> i32:
    if bool is True:
        return 1

    return 0


lib_tdc_error_messages: dict[int, str] = {
    0: 'TDC_Ok, Success',
    -1: 'TDC_Error, Unspecified error',
    1: 'TDC_Timeout, Receive timed out',
    2: 'TDC_NotConnected, No connection was established',
    3: 'TDC_DriverError, Error accessing the USB driver',
    7: 'TDC_DeviceLocked, Can\'t connect device because already in use',
    8: 'TDC_Unknown, Unknown error',
    9: 'TDC_NoDevice, Invalid device number used in call',
    10: 'TDC_OutOfRange, Parameter in function call is out of range',
    11: 'TDC_CantOpen, Failed to open specified file',
    12: 'TDC_NotInitialized, Library has not been initialized',
    13: 'TDC_NotEnabled, Requested feature is not enabled',
    14: 'TDC_NotAvailable, Requested feature is not available',
}


@cython.cclass
class QuTag:

    _device_id: cython.int
    _resolution: cython.double
    _device_type: _qutag.TDC_DevType
    _number_of_channels: u8
    _features_flag: _qutag.TDC_FeatureFlags

    def __init__(self, device_id: int = -1):
        self._device_id = device_id

        rc = _qutag.TDC_init(self._device_id)
        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

    @property
    def version(self) -> float:
        """doc"""
        version: cython.double = _qutag.TDC_getVersion()
        return version

    @property
    def resolution(self) -> float:
        _qutag.TDC_get_Timebase(cython.address(self._resolution))
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
    def number_of_channels(self) -> int:
        self._number_of_channels = _qutag. TDC_getChannelCount()
        return self._number_of_channels

    @property
    def features(self) -> dict[str, bool]:
        self._features_flag = _qutag.RDC_checkFeatures()

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
    def clock_state(self) -> dict[str, bool]:
        locked: i32 = 0
        uplink: i32 = 0

        rc: cython.int = _qutag.TDC_getClockState(
            cython.address(locked), cython.address(uplink))

        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

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
        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

        return disabled == 1

    @disable_clock_reset.setter
    def disable_clock_reset(self, disable: bool):
        disabled: i32 = 0

        if disable is True:
            disabled = 1

        rc: cython.int = _qutag.TDC_disableClockReset(cython.address(disabled))

        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

    @property
    def single_stop(self) -> bool:
        """doc"""
        preselect: i32 = bl32_from_bool(False)
        rc: _qutag.TDC_getSingleStopPreselection(cython.address(preselect))

        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

        return bool_from_bl32(preselect)

    @single_stop.setter
    def single_stop(self, value: bool):
        preselect: i32 = bl32_from_bool(value)
        rc = _qutag.TDC_preselectSingleStop(cython.address(preselect))

        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

    def calibrate(self):
        rc: i32 = _qutag.TDC_startCalibration()
        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

        calibrating: i32 = bl32_from_bool(False)
        rc = _qutag.TDC_getCalibrationState(cython.address(calibrating))
        if rc != 0:
            raise OSError(lib_tdc_error_messages[rc])

        while calibrating is True:
            rc = _qutag.TDC_getCalibrationState(cython.address(calibrating))
            if rc != 0:
                raise OSError(lib_tdc_error_messages[rc])
            time.sleep(0.5)

    @property
    def enabled_channels(self) -> List[int]:
        """doc"""


    @enabled_channels.setter
    def enabled_channels(self, value: List[int]):
        self._enabled_channels = value
