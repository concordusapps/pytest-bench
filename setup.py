#! /usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from os import path
from pkgutil import get_importer

# Calculate the base directory of the project to get relatives from.
BASE_DIR = path.abspath(path.dirname(__file__))

# Navigate, import, and retrieve the metadata of the project.
_imp = get_importer(path.join(BASE_DIR, 'src', 'pytest_bench'))
meta = _imp.find_module('meta').load_module('meta')

setup(
    name='pytest-bench',
    version=meta.version,
    description=meta.description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3'
    ],
    author='Concordus Applications',
    author_email='support@concordusapps.com',
    url='http://github.com/concordusapps/pytest-bench',
    # scripts=['bin/pytest_bench'],
    package_dir={'pytest_bench': 'src/pytest_bench'},
    packages=find_packages(path.join(BASE_DIR, 'src')),
    entry_points={'pytest11': ['pytest_bench = pytest_bench.plugin']},
    install_requires=(
        'pytest',
    ),
)
