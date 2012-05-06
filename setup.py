# Copyright 2012 Kevin Goodsell
#
# This software is licensed under the Eclipse Public License (EPL) V1.0.

from setuptools import setup
from setuptools.dist import Distribution
from setuptools.command.build_py import build_py

setup(
    name='Caduceus',
    version='0.1',
    description='Improved Python bindings for STAF',
    author='Kevin Goodsell',
    author_email='kevin-opensource@omegacrash.net',
    url='https://github.com/KevinGoodsell/caduceus',
    packages=['STAF'],
    license='Eclipse Public License v1.0',
)
