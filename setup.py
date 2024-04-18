import os
import shutil
from numpy import get_include
from Cython.Build import build_ext, cythonize

import sys
from setuptools import setup, Extension, Distribution

cython_dir = os.path.join("tangy/_ext")

extensions = [
    Extension(
        # "tangy._tangy",
        "tangy.tangy",
        [
            os.path.join(cython_dir, "tangy.py"),
        ],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
        include_dirs=[get_include()],
        extra_compile_args=["-O2", "-march=native"],
        optional=os.environ.get('CIBUILDWHEEL', '0') != '1',
    ),
]

ext_modules = cythonize(
    extensions,
    include_path=[cython_dir, cython_dir+"./src"],
    compiler_directives={'language_level': '3'},
    annotate=True)

dist = Distribution({"ext_modules": ext_modules})
cmd = build_ext(dist)
cmd.ensure_finalized()
cmd.run()

for output in cmd.get_outputs():
    relative_extension = os.path.relpath(output, cmd.build_lib)
    shutil.copyfile(output, relative_extension)
