#!/usr/bin/env python

# Setup script for the `dwim' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 1, 2014
# URL: https://github.com/xolox/python-dwim

import os
import re
import setuptools
import sys

# External dependencies.
install_requires = [
    'coloredlogs >= 0.8',
    'executor >= 1.6',
    'verboselogs >= 1.0.1',
]

# External dependency on Python < 3.4.
if sys.version_info[:2] < (3, 4):
    install_requires.append('flufl.enum >= 4.0.1')

def get_contents(filename):
    """Get the contents of a file relative to the source distribution directory."""
    root = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(root, filename)) as handle:
        return handle.read()

def get_version(filename):
    """Extract the version number from a Python module."""
    contents = get_contents(filename)
    metadata = dict(re.findall('__([a-z]+)__ = [\'"]([^\'"]+)', contents))
    return metadata['version']

setuptools.setup(
    name='dwim',
    version=get_version('dwim/__init__.py'),
    description="Location aware application launcher",
    long_description=get_contents('README.rst'),
    url='https://dwim.readthedocs.org/en/latest/',
    author='Peter Odding',
    author_email='peter@peterodding.com',
    packages=setuptools.find_packages(),
    entry_points=dict(console_scripts=['dwim = dwim:main']),
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Desktop Environment',
    ])
