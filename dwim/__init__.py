# dwim: Location aware application launcher.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 29, 2017
# URL: https://dwim.readthedocs.io

"""dwim: Location aware application launcher."""

# Standard library modules.
import functools
import os
import random
import shlex

# External dependencies.
from humanfriendly import Spinner, Timer, format_path, pluralize
from executor import execute, which, quote
from verboselogs import VerboseLogger

# Python 2.x / 3.x compatibility.
try:
    from enum import Enum
except ImportError:
    from flufl.enum import Enum

# Modules included in our package.
from dwim.exceptions import CommandParseError, MissingProgramError

# Semi-standard module versioning.
__version__ = '0.3'

# Initialize a logger for this module.
logger = VerboseLogger(__name__)

# Bind the execute() function to our logger.
execute = functools.partial(execute, logger=logger)

DEFAULT_PROFILE = '~/.dwimrc'
"""The default location of the user's profile script (a string)."""


def dwim(profile=DEFAULT_PROFILE):
    """Evaluate the user's profile script."""
    logger.info("Initializing dwim %s ..", __version__)
    filename = os.path.expanduser(profile)
    environment = dict(
        __file__=filename,
        __name__='dwimrc',
        determine_network_location=determine_network_location,
        launch_program=launch_program,
        LaunchStatus=LaunchStatus,
        set_random_background=set_random_background,
        wait_for_internet_connection=wait_for_internet_connection,
    )
    logger.info("Loading %s ..", format_path(filename))
    execfile(filename, environment, environment)


def launch_program(command, is_running=None):
    """
    Start a program if it's not already running.

    This function makes it easy to turn any program into a single instance
    program. If the default "Is the program already running?" check fails to
    work you can redefine the way this check is done.

    :param command: The shell command used to launch the application (a string).
    :param is_running: The shell command used to check whether the application
                       is already running (a string, optional).
    :returns: One of the values from the :class:`LaunchStatus` enumeration.

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
    :class:`LaunchStatus` enumerates the possible results of :func:`launch_program()`.

    It enables the caller to handle the possible results when they choose to do
    so, without forcing them to handle exceptions.
    """

    started = 1
    """The program wasn't running before but has just been started."""

    already_running = 2
    """The program was already running."""

    not_installed = 3
    """The program is not installed / available on the ``$PATH``."""

    unspecified_error = 4
    """Any other type of error, e.g. the command line can't be parsed."""


def extract_program(command_line):
    """
    Parse a simple shell command to extract the program name.

    :param command_line: A shell command (a string).
    :returns: The program name (a string).
    :raises: :exc:`.CommandParseError` when the command line cannot be parsed.

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
    :raises: :exc:`.MissingProgramError` when the program doesn't exist.

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
    :raises: :exc:`~exceptions.ValueError` when the `command` string doesn't
             contain an ``{image}`` placeholder.
    """
    if '{image}' not in command:
        raise ValueError("The 1st argument should contain an {image} marker!")
    backgrounds = []
    logger.verbose("Searching for desktop backgrounds in %s ..", directory)
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                backgrounds.append(os.path.join(root, filename))
    logger.verbose("Found %s.", pluralize(len(backgrounds), "desktop background"))
    selected_background = random.choice(backgrounds)
    logger.info("Selected random background: %s", format_path(selected_background))
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
    if current_gateway_mac:
        for network_name, known_gateways in gateways.items():
            if any(current_gateway_mac.upper() == gateway.upper() for gateway in known_gateways):
                logger.info("We're connected to the %s network.", network_name)
                return network_name
        logger.info("We're not connected to a known network (unknown gateway MAC address %s).", current_gateway_mac)
    else:
        logger.info("Failed to determine gateway, assuming network connection is down.")


def find_gateway_address():
    """
    Find the IP address of the current gateway using the ``ip route`` command.

    :returns: The IP address of the gateway (a string) or :data:`None`.

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
    timer = Timer()
    logger.info("Checking internet connection ..")
    if have_internet_connection():
        logger.info("We're already connected!")
    else:
        logger.info("We're not connected yet, waiting ..")
        with Spinner(label="Waiting for internet connection", timer=timer) as spinner:
            while not have_internet_connection():
                spinner.step()
                spinner.sleep()
        logger.info("Internet connection is now ready (waited %s).", timer)


def have_internet_connection():
    """
    Check if an internet connection is available.

    :returns: :data:`True` if an internet connection is available,
              :data:`False` otherwise.

    This works by pinging 8.8.8.8 which is one of `Google's public DNS servers
    <https://developers.google.com/speed/public-dns/>`_. This IP address was
    chosen because it is documented that Google uses anycast to keep this IP
    address available at all times.
    """
    return execute('ping', '-c1', '-w1', '8.8.8.8', check=False, silent=True)
