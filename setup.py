from setuptools import setup, Extension
from Cython.Build import cythonize

# Definimos nuestra extensión, incluyendo el código puente y el código C real
extension = Extension(
    name="mininet_ng_core",
    sources=["mininet_ng_core.pyx", "core_namespaces.c"],
)

setup(
    name="MininetNG Core",
    ext_modules=cythonize([extension], compiler_directives={"language_level": "3"}),
)
