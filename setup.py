# !/usr/bin/python3
from setuptools import setup

setup(
    name="vtk-raytracing",
    python_requires=">=3.7.11",
    install_requires=[
        "vtk>=9.1.0",
        "matplotlib>=3.5.1",
        "numpy>=1.21.5",
        "pyglm>=2.5.7",
        "PyQt5>=5.15.6",
        "rich-cli>=1.5.1",
    ],
    license="GNU LGPL v3",
    author="Benjamin Bourbon",
    author_email="ben.bourbon06@gmail.com",
    description="Raytracing using VTK",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/bourbonut/vtk-raytracing",
)
