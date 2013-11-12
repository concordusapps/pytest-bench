#! /usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from imp import load_source


setup(
    name='pytest-bench',
    version=load_source('', 'pytest_bench/_version.py').__version__,
    description='',
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
