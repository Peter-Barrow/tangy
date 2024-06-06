from ._tangy import tangy_config_location, buffer_list_update
from ._tangy import buffer_list_append, buffer_list_show, buffer_list_delete_all
from ._tangy import Records
from ._tangy import TangyBuffer, TangyBufferType
from ._tangy import PTUFile

from sys import platform
from ctypes.util import find_library

# uqd_lib = None
# 
# if platform.startswith("linux"):
#     uqd_lib = find_library("timetag64")
# 
# if platform.startswith("win32"):
#     uqd_lib = find_library("CTimeTagLib")
#     from ._uqd import UQDLogic16
# 
# if uqd_lib is not None:
#     from ._uqd import UQDLogic16
