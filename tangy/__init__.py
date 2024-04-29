from ._tangy import RecordsStandard, RecordsClocked
from ._tangy import TangyBuffer, TangyBufferStandard, TangyBufferClocked
from ._tangy import singles  # , Coincidences
# from ._tangy import JointDelayHistogram, JointHistogram
from ._tangy import find_zero_delay, zero_delay_result
from ._tangy import timetrace, PTUFile
from ._tangy import test_class, test_impl_a, test_impl_b, print_resolution, print_resolution_cy, print_resolution_fused


from ._uqd import UQD

# from .tangy import singles, coincidences, timetrace, find_zero_delay
# from .tangy import coincidence_measurement

# __all__ - ["standard_records", "clocked_records", "stdbuffer", "clkbuffer",
#            "PTUFile"]

__all__ = ["RecordsStandard", "RecordsClocked", "TangyBuffer", "singles",
           "timetrace", "find_zero_delay", "zero_delay_result", "Coincidences",
           "JointDelayHistogram", "JointHistogram", "PTUFile"]

# from sys import platform
# from ctypes.util import find_library
#
# uqd_lib = None
#
# if platform.startswith("linux"):
#     uqd_lib = find_library("timetag64")
#
# if platform.startswith("win32"):
#     uqd_lib = find_library("CTimeTagLib")
#
# if uqd_lib is not None:
#     print("proceeding to import interface to UQD-Logic16")
