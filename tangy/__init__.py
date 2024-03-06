from ._tangy import standard_records, clocked_records
from ._tangy import stdbuffer, clkbuffer, PTUFile
from ._tangy import singles, coincidences, timetrace, find_zero_delay
from ._tangy import coincidence_measurement

# __all__ - ["standard_records", "clocked_records", "stdbuffer", "clkbuffer",
#            "PTUFile"]

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
