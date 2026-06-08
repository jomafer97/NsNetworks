from setuptools import setup, Extension
from Cython.Build import cythonize

extension = Extension(
    name="c_core",
    sources=["src/c_ext/c_core.pyx", "src/c_ext/core_logic.c"],
    include_dirs=["c_ext"],
)

setup(
    name="C Core",
    ext_modules=cythonize([extension], compiler_directives={"language_level": "3"}),
)
