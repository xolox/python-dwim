# dwim: Location aware application launcher.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 29, 2017
# URL: https://dwim.readthedocs.io

"""
Usage: dwim [OPTIONS]

The dwim program is a location aware application launcher. To use it you are
required to create a profile at ~/.dwimrc. This profile is a simple Python
script that defines which applications you want to start automatically, in
which order the applications should start and whether some applications
should only be started given a specific physical location.

The location awareness works by checking the MAC address of your gateway
(the device on your network that connects you to the outside world, usually
a router) to a set of known MAC addresses that you define in ~/.dwimrc.

Every time you run the dwim program your ~/.dwimrc profile is evaluated and
your applications are started automatically. If you run dwim again it will
not start duplicate instances of your applications, but when you quit an
application and then rerun dwim the application will be started again.

Supported options:

  -c, --config=FILE

    Override the default location of the profile script.

  -v, --verbose

    Increase logging verbosity (can be repeated).

  -q, --quiet

    Decrease logging verbosity (can be repeated).

  -h, --help

    Show this message and exit.
"""

# Standard library modules.
import getopt
import sys

# External dependencies.
import coloredlogs
from humanfriendly.terminal import usage, warning
from verboselogs import VerboseLogger

# Initialize a logger for this module.
logger = VerboseLogger(__name__)


def main():
    """Command line interface for the ``dwim`` program."""
    from dwim import DEFAULT_PROFILE, dwim
    # Initialize logging to the terminal.
    coloredlogs.install()
    # Define the command line option defaults.
    profile_script = DEFAULT_PROFILE
    # Parse the command line arguments.
    try:
        options, _ = getopt.getopt(sys.argv[1:], 'c:vqh', [
            'config=', 'verbose', 'quiet', 'help',
        ])
        for option, value in options:
            if option in ('-c', '--config'):
                profile_script = value
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage(__doc__)
                sys.exit(0)
    except Exception as e:
        warning("Error: Failed to parse command line arguments! (%s)", e)
        sys.exit(1)
    # Execute the requested action(s).
    try:
        dwim(profile_script)
    except Exception:
        logger.exception("Caught a fatal exception! Terminating ..")
        sys.exit(1)
