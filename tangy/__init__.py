from ._tagbuffers import standard_records, clocked_records
from ._tagbuffers import stdbuffer, clkbuffer, PTUFile
from ._tagbuffers import singles, coincidences, timetrace, find_zero_delay
from ._tagbuffers import coincidence_measurement

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
