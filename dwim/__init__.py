# dwim: Location aware application launcher.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 8, 2017
# URL: https://dwim.readthedocs.io

# Standard library modules.
import functools
import getopt
import os
import random
import shlex
import sys
import time

# Semi-standard module versioning.
__version__ = '0.2'

# External dependencies.
import coloredlogs
from executor import execute, which, quote
from verboselogs import VerboseLogger

# Python 2.x / 3.x compatibility.
try:
    from enum import Enum
except ImportError:
    from flufl.enum import Enum

# Initialize a logger for this module.
logger = VerboseLogger(__name__)
execute = functools.partial(execute, logger=logger)


def main():
    """Command line interface for the ``dwim`` program."""
    # Initialize logging to the terminal.
    coloredlogs.install()
    # Define the command line option defaults.
    profile = '~/.dwimrc'
    # Parse the command line arguments.
    try:
        options, _ = getopt.getopt(sys.argv[1:], 'c:vqh', ['config=', 'verbose', 'quiet', 'help'])
        for option, value in options:
            if option in ('-c', '--config'):
                profile = value
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage()
                sys.exit(0)
    except Exception:
        logger.exception("Failed to parse command line arguments!")
        sys.exit(1)
    # Execute the requested action(s).
    try:
        logger.info("Initializing dwim %s ..", __version__)
        # Load the user's profile script.
        filename = os.path.expanduser(profile)
        environment = dict(__file__=filename,
                           __name__='dwimrc',
                           launch_program=launch_program,
                           LaunchStatus=LaunchStatus,
                           set_random_background=set_random_background,
                           wait_for_internet_connection=wait_for_internet_connection)
        logger.info("Loading %s ..", filename)
        execfile(filename, environment, environment)
    except Exception:
        logger.exception("Caught a fatal exception! Terminating ..")
        sys.exit(1)


def usage():
    """Print a user friendly usage message to the terminal."""
    print("""
Usage: dwim [OPTIONS]

The dwim program is a location aware application launcher. To use it you are
required to create a profile at ~/.dwimrc. This profile is a simple Python
script that defines which applications you want to start automatically, in
which order the applications should start and whether some applications should
only be started given a specific physical location.

The location awareness works by checking the MAC address of your gateway (the
device on your network that connects you to the outside world, usually a
router) to a set of known MAC addresses that you define in ~/.dwimrc.

Every time you run the dwim program your ~/.dwimrc profile is evaluated and
your applications are started automatically. If you run dwim again it will not
start duplicate instances of your applications, but when you quit an
application and then rerun dwim the application will be started again.

Supported options:

  -c, --config=FILE  override profile location
  -v, --verbose      make more noise
  -q, --quiet        make less noise
  -h, --help         show this message and exit
""".strip())


def launch_program(command, is_running=None):
    """
    Start a program if it's not already running.

    This function makes it easy to turn any program into a single instance
    program. If the default "Is the program already running?" check fails to
    work you can redefine the way this check is done.

    :param command: The shell command used to launch the application (a string).
    :param is_running: The shell command used to check whether the application
                       is already running (a string, optional).
    :returns: One of the values from the :py:class:`LaunchStatus` enumeration.

    Examples of custom "is running" checks:

    .. code-block:: python

       # Chromium uses a wrapper script, so we need to match the absolute
       # pathname of the executable.
       launch_program('chromium-browser', is_running='pidof /usr/lib/chromium-browser/chromium-browser')

       # Dropbox does the same thing as Chromium, but the absolute pathname of
       # the executable contains a version number that I don't want to hard
       # code in my ~/.dwimrc profile :-)
       launch_program('dropbox start', is_running='pgrep -f "$HOME/.dropbox-dist/*/dropbox"')
    """
    try:
        pathname = resolve_program(extract_program(command))
        if not is_running:
            is_running = 'pidof %s' % quote(pathname)
        logger.verbose("Checking if program is running (%s) ..", pathname)
        if execute(is_running, silent=True, check=False):
            logger.info("Command already running: %s", command)
            return LaunchStatus.already_running
        else:
            logger.info("Starting command: %s", command)
            execute('sh', '-c', '(%s >/dev/null 2>&1) &' % command)
            return LaunchStatus.started
    except MissingProgramError:
        logger.warning("Program not installed! (%s)", command)
        return LaunchStatus.not_installed
    except Exception as e:
        logger.warning("Failed to start program! (%s)", e)
        return LaunchStatus.unspecified_error


class LaunchStatus(Enum):

    """
    The :py:class:`LaunchStatus` enumeration defines the possible results of
    :py:func:`launch_program()`. It enables the caller to handle the possible
    results when they choose to do so, without forcing them to handle
    exceptions.

    .. data:: started

    The program wasn't running before but has just been started.

    .. data:: already_running

    The program was already running.

    .. data:: not_installed

    The program is not installed / available on the ``$PATH``.

    .. data:: unspecified_error

    Any other type of error, e.g. the command line given to
    :py:func:`launch_program()` can't be parsed.
    """

    started = 1
    already_running = 2
    not_installed = 3
    unspecified_error = 4


def extract_program(command_line):
    """
    Parse a simple shell command to extract the program name.

    :param command_line: A shell command (a string).
    :returns: The program name (a string).
    :raises: :py:exc:`CommandParseError` when the command line cannot be parsed.

    Some examples:

    >>> extract_program('dropbox start')
    'dropbox'
    >>> extract_program(' "/usr/bin/dropbox" start ')
    '/usr/bin/dropbox'
    """
    logger.debug("Parsing command line: %s", command_line)
    tokens = shlex.split(command_line)
    if not tokens:
        raise CommandParseError("Failed to parse command line! (%r)" % command_line)
    logger.debug("Extracting program name from parsed command line: %s", tokens)
    return tokens[0]


def resolve_program(executable):
    """
    Expand the name of a program into an absolute pathname.

    :param executable: The name of a program (a string).
    :returns: The absolute pathname of the program (a string).
    :raises: :py:exc:`MissingProgramError` when the program doesn't exist.

    An example:

    >>> extract_program('dropbox start')
    'dropbox'
    >>> resolve_program(extract_program('dropbox start'))
    '/usr/bin/dropbox'
    """
    # Check if the executable name contains no directory components.
    if os.path.basename(executable) == executable:
        # Transform the executable name into an absolute pathname.
        matching_programs = which(executable)
        logger.debug("Programs matching executable name: %s", matching_programs)
        if not matching_programs:
            raise MissingProgramError("Program not found on $PATH! (%s)" % executable)
        executable = matching_programs[0]
    else:
        # Make sure the executable exists and is in fact executable.
        logger.debug("Validating executable name: %s", executable)
        if not os.access(executable, os.X_OK):
            raise MissingProgramError("Program not found! (%s)" % executable)
    return executable


def set_random_background(command, directory):
    """
    Set a random desktop wallpaper / background.

    :param command: The command to set the wallpaper (a string containing an
                    ``{image}`` marker).
    :param directory: The pathname of a directory containing wallpapers (a
                      string).
    """
    assert '{image}' in command, "The 1st argument should contain an {image} marker!"
    backgrounds = []
    logger.verbose("Searching for desktop backgrounds in %s ..", directory)
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                backgrounds.append(os.path.join(root, filename))
    logger.verbose("Found %i desktop backgrounds.", len(backgrounds))
    selected_background = random.choice(backgrounds)
    logger.info("Selected random background: %s", selected_background)
    execute(command.format(image=quote(selected_background)))


def determine_network_location(**gateways):
    """
    Determine the physical location of this computer.

    This works by matching the MAC address of the current gateway against a set
    of known MAC addresses, which provides a simple but robust way to identify
    the current network. Because networks usually have a physical location,
    identifying the current network tells us our physical location.

    :param gateways: One or more keyword arguments with lists of strings
                     containing MAC addresses of known networks.
    :returns: The name of the matched MAC address (a string) or ``None`` when
              the MAC address of the current gateway is unknown.

    Here's an example from my ``~/.dwimrc`` involving multiple networks and a
    physical location with multiple gateways:

    .. code-block:: python

       location = determine_network_location(home=['84:9C:A6:76:23:8E'],
                                             office=['00:15:C5:5F:92:79',
                                                     'B6:25:B2:19:28:61',
                                                     '00:18:8B:F8:AF:33'])
    """
    current_gateway_mac = find_gateway_mac()
    for network_name, known_gateways in gateways.items():
        if any(current_gateway_mac.upper() == gateway.upper() for gateway in known_gateways):
            logger.info("We're connected to the %s network.", network_name)
            return network_name
    logger.info("We're not connected to a known network (unknown gateway MAC address %s).", current_gateway_mac)


def find_gateway_address():
    """
    Find the IP address of the current gateway using the ``ip route`` command.

    :returns: The IP address of the gateway (a string) or ``None``.

    An example:

    >>> find_gateway_address()
    '192.168.1.1'
    """
    logger.verbose("Looking for IP address of current gateway ..")
    for line in execute('ip', 'route', capture=True).splitlines():
        tokens = line.split()
        logger.debug("Parsing 'ip route' output: %s", tokens)
        if len(tokens) >= 3 and tokens[:2] == ['default', 'via']:
            ip_address = tokens[2]
            logger.verbose("Found gateway IP address: %s", ip_address)
            return ip_address


def find_gateway_mac():
    """
    Find the MAC address of the current gateway using the ``arp -n`` command.

    :returns: The MAC address of the gateway (a string) or ``None``.

    An example:

    >>> find_gateway_address()
    '192.168.1.1'
    >>> find_gateway_mac(find_gateway_address())
    '84:9c:a6:76:23:8e'
    """
    ip_address = find_gateway_address()
    if ip_address:
        logger.verbose("Looking for MAC address of current gateway (%s) ..", ip_address)
        for line in execute('arp', '-n', capture=True).splitlines():
            tokens = line.split()
            logger.debug("Parsing 'arp -n' output: %s", tokens)
            if len(tokens) >= 3 and tokens[0] == ip_address:
                mac_address = tokens[2]
                logger.verbose("Found gateway MAC address: %s", mac_address)
                return mac_address


def wait_for_internet_connection():
    """
    Wait for an active internet connection.

    This works by sending ``ping`` requests to ``8.8.8.8`` (one of the Google
    public DNS IPv4 addresses) and returning as soon as a ping request gets a
    successful response. The ping interval and timeout is one second.
    """
    logger.info("Checking internet connection ..")
    while not execute('ping -c1 -w1 8.8.8.8', silent=True, check=False):
        logger.info("Not connected yet, retrying in a second ..")
        time.sleep(1)
    logger.info("Internet connection is ready.")


class ProgramError(Exception):
    """Super class for exceptions raised in :py:func:`launch_program()`."""


class CommandParseError(ProgramError):
    """Raised by :py:func:`extract_program()` when a program doesn't exist."""


class MissingProgramError(ProgramError):
    """Raised by :py:func:`resolve_program()` when a program doesn't exist."""
