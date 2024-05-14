import platform
import os
import shutil
from numpy import get_include
from Cython.Build import build_ext, cythonize

import sys
from setuptools import setup, Extension, Distribution

cython_dir = os.path.join("tangy_src")
# os.environ["CC"] = "x86_64-w64-mingw32-gcc"

compiler_flags = []
if "Linux" in platform.platform():
    compiler_flags = ["-O2", "-march=native"]
    uqd_include_dirs = [get_include(), "./opt/CTimeTag/Include", "."]
    libusb = "usb"
    if "ubuntu" in platform.version().lower():
        libusb = "usb-1.0"

    uqd_libraries = [libusb, 'timetag64']
    uqd_libraries_dirs = ['.', './opt/CTimeTag/Linux']

link_args = []
if "Windows" in platform.platform():
    # these are needed for local development
    # os.environ['PATH'] = 'C:\\mingw64\\bin'
    # compiler_flags = ["-O2", "-march=native", "-DMS_WIN64", "-std=c++11"]
    # compiler_flags = ["-O2", "-march=native", "-DMS_WIN64"]
    # compiler_flags = ["-DMS_WIN64"]
    compiler_flags = []

    base_path = os.getcwd()

    # link_args = ['-static-libgcc',
    #              '-static-libstdc++',
    #              '-Wl,-Bstatic,--whole-archive',
    #              '-lwinpthread',
    #              '-Wl,--no-whole-archive',
    #              ]

    uqd_link_args = [
        # '-ICTimeTagLib',
        # '/d2:-AllowCompatibleILVersions'
    ]
    uqd_include_dirs = [get_include(), base_path + "\\opt\\CTimeTag\\Include\\"]
    uqd_libraries_dirs = [base_path, base_path + '\\opt\\CTimeTag\\Win64\\']
    # uqd_libraries_dirs += [base_path, base_path + '\\opt\\CTimeTag\\Linux']
    # uqd_libraries = ["timetag64"]
    uqd_libraries = ["CTimeTagLib"]


extensions = [
    Extension(
        # "tangy._tangy",
        "tangy._tangy",
        sources=[
            os.path.join(cython_dir, "_tangy.py"),
        ],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
        include_dirs=[get_include()],
        extra_compile_args=compiler_flags,
        extra_link_args=link_args,
        optional=os.environ.get('CIBUILDWHEEL', '0') != '1',
    ),
    Extension(
        "tangy._uqd",
        sources=[
            os.path.join(cython_dir, "_uqd.py")],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
        include_dirs=uqd_include_dirs,
        libraries=uqd_libraries,
        library_dirs=uqd_libraries_dirs,
        extra_link_args=link_args + uqd_link_args,
        extra_compile_args=compiler_flags,
        language="c++",
        optional=os.environ.get('CIBUILDWHEEL', '0') != '1',
    ),
]

ext_modules = cythonize(
    extensions,
    include_path=[cython_dir, cython_dir + "./src"],
    compiler_directives={'language_level': '3'},
    annotate=True)

setup(ext_modules=ext_modules, include_package_data=True)

# dist = Distribution({"ext_modules": ext_modules})
# cmd = build_ext(dist)
# # required for local testing
# if "Windows" in platform.platform():
#     cmd = build_ext(dist, compiler="mingw32")
# cmd.ensure_finalized()
# cmd.run()
#
# for output in cmd.get_outputs():
#     relative_extension = os.path.relpath(output, cmd.build_lib)
#     shutil.copyfile(output, relative_extension)
