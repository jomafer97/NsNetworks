from setuptools import setup, Extension
from Cython.Build import cythonize

extension = Extension(
    name="c_core",
    sources=["c_core.pyx", "core_namespaces.c"],
)

setup(
    name="C Core",
    ext_modules=cythonize([extension], compiler_directives={"language_level": "3"}),
)
