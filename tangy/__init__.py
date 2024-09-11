from ._tangy import tangy_config_location, buffer_list_update
from ._tangy import buffer_list_append, buffer_list_show, buffer_list_delete_all
from ._tangy import Records
from ._tangy import TangyBuffer, TangyBufferType
from ._tangy import PTUFile, QuToolsFile

from sys import platform
from ctypes.util import find_library

_uqd_lib = None
_qutag_lib = None

if platform.startswith("linux"):
    _uqd_lib = find_library("timetag64")
    _qutag_lib = find_library("tdcbase")

if platform.startswith("win32"):
    _uqd_lib = find_library("CTimeTagLib")

if _uqd_lib is not None:
    from ._uqd import UQDLogic16

if _qutag_lib is not None:
    from ._qutag import QuTagHR, DeviceChannel, SignalEdge, SignalConditioning
