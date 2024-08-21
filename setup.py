import platform
import os
from numpy import get_include
from Cython.Build import cythonize
from setuptools import setup, Extension


local = True
if os.environ.get("CIBUILDWHEEL", '0') == 1:
    local = False
local = False

cython_dir = os.path.join("tangy_src")

extensions = []

tangy_core = Extension(
    "tangy._tangy",
    sources=[
        os.path.join(cython_dir, "_tangy.py"),
    ],
    define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
    include_dirs=[get_include(), cython_dir + "/src"],
    optional=os.environ.get('CIBUILDWHEEL', '0') != '1',
)

extensions.append(tangy_core)

compiler_flags = []
if "Linux" in platform.platform():
    # compiler_flags = ["-O2", "-march=native"]
    # compiler_flags = ["-march=native"]
    uqd_include_dirs = [get_include(), "./opt/CTimeTag/Include", "."]
    libusb = "usb"
    if local is True:
        libusb = "usb-1.0"

    uqd = Extension(
        "tangy._uqd",
        sources=[
            os.path.join(cython_dir, "_uqd.py")],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
        include_dirs=uqd_include_dirs,
        libraries=[libusb, 'timetag64'],
        library_dirs=['.', './opt/CTimeTag/Linux'],
        extra_compile_args=compiler_flags,
        language="c++",
        optional=os.environ.get('CIBUILDWHEEL', '0') != '1',
    )
    extensions.append(uqd)

if "Windows" in platform.platform():
    # these are needed for local development
    # os.environ["CC"] = "x86_64-w64-mingw32-gcc"
    # os.environ['PATH'] = 'C:\\mingw64\\bin'
    # compiler_flags = ["-O2", "-march=native", "-DMS_WIN64", "-std=c++11"]
    # compiler_flags = ["-O2", "-march=native", "-DMS_WIN64"]
    # compiler_flags = ["-DMS_WIN64"]
    compiler_flags = []

    base_path = os.getcwd()

    uqd = Extension(
        "tangy._uqd",
        sources=[os.path.join(cython_dir, "_uqd.py")],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
        include_dirs=[get_include(), base_path + "\\opt\\CTimeTag\\Include\\"],
        libraries=["CTimeTagLib"],
        library_dirs=[base_path, base_path + '\\opt\\CTimeTag\\Win64\\'],
        extra_link_args=['/d2:-AllowCompatibleILVersions'],
        extra_compile_args=compiler_flags,
        language="c++",
        optional=os.environ.get('CIBUILDWHEEL', '0') != '1',
    )
    extensions.append(uqd)

ext_modules = cythonize(
    extensions,
    include_path=[cython_dir, cython_dir + "./src"],
    compiler_directives={'language_level': '3'},
    annotate=True)

setup(ext_modules=ext_modules, include_package_data=True)
