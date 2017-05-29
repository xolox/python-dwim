#!/usr/bin/env python

# Setup script for the `dwim' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 29, 2017
# URL: https://dwim.readthedocs.io

"""
Setup script for the `dwim` package.

**python setup.py install**
  Install from the working directory into the current Python environment.

**python setup.py sdist**
  Build a source distribution archive.

**python setup.py bdist_wheel**
  Build a wheel distribution archive.
"""

# Standard library modules.
import codecs
import os
import re
import sys

# De-facto standard solution for Python packaging.
from setuptools import find_packages, setup


def get_contents(*args):
    """Get the contents of a file relative to the source distribution directory."""
    with codecs.open(get_absolute_path(*args), 'r', 'UTF-8') as handle:
        return handle.read()


def get_version(*args):
    """Extract the version number from a Python module."""
    contents = get_contents(*args)
    metadata = dict(re.findall('__([a-z]+)__ = [\'"]([^\'"]+)', contents))
    return metadata['version']


def get_install_requires():
    """Get the installation requirements."""
    install_requires = get_requirements('requirements.txt')
    if 'bdist_wheel' not in sys.argv:
        if sys.version_info[:2] < (3, 4):
            install_requires.append('flufl.enum >= 4.0.1')
    return sorted(install_requires)


def get_extras_require():
    """Get the conditional requirements (for wheel distributions)."""
    extras_require = {}
    if have_environment_marker_support():
        expression = ':%s' % ' or '.join([
            'python_version == "2.6"',
            'python_version == "2.7"',
            'python_version == "3.0"',
            'python_version == "3.1"',
            'python_version == "3.2"',
            'python_version == "3.3"',
        ])
        extras_require[expression] = ['flufl.enum >= 4.0.1']
    return extras_require


def get_requirements(*args):
    """Get requirements from pip requirement files."""
    requirements = set()
    with open(get_absolute_path(*args)) as handle:
        for line in handle:
            # Strip comments.
            line = re.sub(r'^#.*|\s#.*', '', line)
            # Ignore empty lines
            if line and not line.isspace():
                requirements.add(re.sub(r'\s+', '', line))
    return sorted(requirements)


def get_absolute_path(*args):
    """Transform relative pathnames into absolute pathnames."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


def have_environment_marker_support():
    """
    Check whether setuptools has support for PEP-426 environment marker support.

    Based on the ``setup.py`` script of the ``pytest`` package:
    https://bitbucket.org/pytest-dev/pytest/src/default/setup.py
    """
    try:
        from pkg_resources import parse_version
        from setuptools import __version__
        return parse_version(__version__) >= parse_version('0.7.2')
    except Exception:
        return False


setup(name='dwim',
      version=get_version('dwim', '__init__.py'),
      description="Location aware application launcher",
      long_description=get_contents('README.rst'),
      url='https://dwim.readthedocs.io/en/latest/',
      author="Peter Odding",
      author_email='peter@peterodding.com',
      packages=find_packages(),
      entry_points=dict(console_scripts=[
          'dwim = dwim.cli:main',
      ]),
      install_requires=get_install_requires(),
      extras_require=get_extras_require(),
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
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Desktop Environment',
      ])
