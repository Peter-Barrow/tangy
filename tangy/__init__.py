from ._tangy import tangy_config_location, buffer_list_update, buffer_list_append, buffer_list_show, buffer_list_delete_all
from ._tangy import RecordsStandard, RecordsClocked
from ._tangy import TangyBuffer, TangyBufferStandard, TangyBufferClocked
# from ._tangy import JointDelayHistogram, JointHistogram
from ._tangy import JointHistogramMeasurement, JointHistogram
from ._tangy import timetrace, find_delay, delay_result
from ._tangy import PTUFile

# from .tangy import singles, coincidences, timetrace, find_zero_delay
# from .tangy import coincidence_measurement

# __all__ - ["standard_records", "clocked_records", "stdbuffer", "clkbuffer",
#            "PTUFile"]

# __all__ = ["RecordsStandard", "RecordsClocked", "TangyBuffer", "singles",
#            "timetrace", "find_zero_delay", "zero_delay_result", "Coincidences",
#            "JointDelayHistogram", "JointHistogram", "PTUFile"]

from sys import platform
from ctypes.util import find_library

uqd_lib = None

if platform.startswith("linux"):
    uqd_lib = find_library("timetag64")

if platform.startswith("win32"):
    uqd_lib = find_library("CTimeTagLib")
    from ._uqd import UQDLogic16

if uqd_lib is not None:
    from ._uqd import UQDLogic16
