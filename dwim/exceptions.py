# dwim: Location aware application launcher.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 29, 2017
# URL: https://dwim.readthedocs.io

"""Custom exceptions raised by :mod:`dwim`."""


class ProgramError(Exception):

    """Super class for exceptions raised in :func:`.launch_program()`."""


class CommandParseError(ProgramError):

    """Raised by :func:`.extract_program()` when a command line can't be parsed or is empty."""


class MissingProgramError(ProgramError):

    """Raised by :func:`.resolve_program()` when a program doesn't exist."""
