dwim: Location aware application launcher
=========================================

The ``dwim`` program is a location aware application launcher. To use it you
are required to create a profile at ``~/.dwimrc``. This profile is a simple
Python_ script that defines which applications you want to start automatically,
in which order the applications should start and whether some applications
should only be started when your computer is on a specific physical location.
The location awareness works by matching a unique property of the network that
your computer is connected to (the `MAC address`_ of your current `network
gateway`_).

Every time you run the ``dwim`` program your ``~/.dwimrc`` profile is evaluated
and your applications are started automatically. If you run ``dwim`` again it
will not start duplicate instances of your applications, but when you quit an
application and then rerun ``dwim`` the application will be started again.

.. contents::
   :local:
   :depth: 2

Installation
------------

The `dwim` package is available on PyPI_ which means installation should be as
simple as:

.. code-block:: sh

   $ pip install dwim

There's actually a multitude of ways to install Python packages (e.g. the `per
user site-packages directory`_, `virtual environments`_ or just installing
system wide) and I have no intention of getting into that discussion here, so
if this intimidates you then read up on your options before returning to these
instructions ;-).

Usage
-----

There are two ways to use the `dwim` package: As the command line program
``dwim`` and as a Python API. For details about the Python API please refer to
the API documentation available on `Read the Docs`_. The command line interface
is described below.

Please note that you need to `create a profile`_ (see below) before you can use
the program.

Command line interface
~~~~~~~~~~~~~~~~~~~~~~

.. A DRY solution to avoid duplication of the `dwim --help' text:
..
.. [[[cog
.. from humanfriendly.usage import inject_usage
.. inject_usage('dwim.cli')
.. ]]]

**Usage:** `dwim [OPTIONS]`

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

**Supported options:**

.. csv-table::
   :header: Option, Description
   :widths: 30, 70


   "``-c``, ``--config=FILE``",Override the default location of the profile script.
   "``-v``, ``--verbose``",Increase logging verbosity (can be repeated).
   "``-q``, ``--quiet``",Decrease logging verbosity (can be repeated).
   "``-h``, ``--help``",Show this message and exit.

.. [[[end]]]

.. _create a profile:

Creating a profile
~~~~~~~~~~~~~~~~~~

To use ``dwim`` you need to create a profile at ``~/.dwimrc``. The profile is a
simple Python_ script that defines which applications you want to start
automatically, in which order the applications should start and whether some
applications should only be started on a specific physical location. The
profile script has access to functions provided by the ``dwim`` Python package.
Please refer to `the documentation`_ for the available functions. The examples
below show the most useful functions.

.. contents::
   :local:

Starting your first program
```````````````````````````

If you'd like to get your feet wet with a simple example, try this:

.. code-block:: python

   launch_program('pidgin')

When you've created the above profile script and you run the ``dwim`` program
it will start the Pidgin_ chat client on the first run. On the next run nothing
will happen because Pidgin is already running.

Modifying the "is running" check
````````````````````````````````

The default "is running" check comes down to the following shell command line:

.. code-block:: bash

   # Replace `pidgin' with any program name.
   pidof $(which pidgin)

This logic will not work for all programs. For example in my profile I start
the Dropbox_ client using a wrapper script. Once the Dropbox client has been
started the wrapper script terminates so the ``pidof`` check fails. The
solution is to customize the "is running" check:

.. code-block:: python

   launch_program('dropbox start', is_running='pgrep -f "$HOME/.dropbox-dist/*/dropbox"')

The example above is for the Dropbox client, but the same principle can be
applied to all other programs. The only trick is to find a shell command that
can correctly tell whether the program is running. Unfortunately this part
cannot be automated in a completely generic manner. The advanced profile
example below contains more examples of defining custom ``pidof`` checks and
``pgrep -f`` checks.

Enabling location awareness
```````````````````````````

The first step to enabling location awareness is to add the following line
to your profile:

.. code-block:: python

   determine_network_location()

Even if you don't pass any information to this function it will still report
your current gateway's MAC address. This saves me from having to document the
shell commands needed to do the same thing :-). Run the ``dwim`` command and
take note of a line that looks like this:

.. code-block:: text

   We're not connected to a known network (unknown gateway MAC address 84:9c:a6:76:23:8e).

Now edit your profile and change the line you just added:

.. code-block:: python

   location = determine_network_location(home=['84:9c:a6:76:23:8e'])

When you now rerun ``dwim`` it will say:

.. code-block:: text

   We're connected to the home network.

So what did we just do? We took note of the current gateway's MAC address and
associated that MAC address with a location named "home". In our profile we can
now start programs on the condition that we're connected to the home network:

.. code-block:: python

   if location == 'home':
      # Client for Music Player Daemon.
      launch_program('ario --minimized')
   else:
      # Standalone music player.
      launch_program('rhythmbox')

The example profile below (my profile) contains a more advanced example
combining multiple networks and networks with multiple gateways.

Example profile
```````````````

I've been using variants of ``dwim`` (previously in the form of a Bash_ script
:-) for years now so my profile has grown quite a bit. Because of this it may
provide some interesting examples of things you can do:

.. code-block:: python

   # vim: fileencoding=utf-8

   # ~/.dwimrc: Profile for dwim, my location aware application launcher.
   # For more information please see https://github.com/xolox/python-dwim/.

   # Standard library modules.
   import os
   import time

   # Packages provided by dwim and its dependencies.
   from executor import execute
   from dwim import (determine_network_location, launch_program, LaunchStatus
                     set_random_background, wait_for_internet_connection)

   # This is required for graphical Vim and gnome-terminal to have nicely
   # anti-aliased fonts. See http://awesome.naquadah.org/wiki/Autostart.
   if launch_program('gnome-settings-daemon') == LaunchStatus.started:

       # When my window manager is initially started I need to wait for a moment
       # before launching user programs because otherwise strange things can
       # happen, for example programs that place an icon in the notification area
       # might be started in the background without adding the icon, so there's
       # no way to access the program but `dwim' will never restart the program
       # because it's already running! ಠ_ಠ
       logger.debug("Sleeping for 10 seconds to give Awesome a moment to initialize ..")
       time.sleep(10)

   # Determine the physical location of this computer by matching the MAC address
   # of the gateway against a set of known MAC addresses. In my own copy I've
   # documented which MAC addresses belong to which devices, but that doesn't seem
   # very relevant for the outside world :-)
   location = determine_network_location(home=['84:9C:A6:76:23:8E'],
                                         office=['00:15:C5:5F:92:79',
                                                 'B6:25:B2:19:28:61',
                                                 '00:18:8B:F8:AF:33'])

   # Correctly configure my multi-monitor setup based on physical location.
   if location == 'home':
       # At home I use a 24" ASUS monitor as my primary screen.
       # My MacBook Air sits to the left as the secondary screen.
       execute('xrandr --output eDP1 --auto --noprimary')
       execute('xrandr --output HDMI1 --auto --primary')
       execute('xrandr --output HDMI1 --right-of eDP1')
   if location == 'work':
       # At work I use a 24" LG monitor as my primary screen.
       # My Asus Zenbook sits to the right as the secondary screen.
       execute('xrandr --output eDP1 --auto')
       execute('xrandr --output HDMI1 --auto')
       execute('xrandr --output HDMI1 --left-of eDP1')

   # Set a random desktop background from my collection of wallpapers. I use the
   # program `feh' for this because it supports my desktop environment / window
   # manager (Awesome). You can install `feh' using `sudo apt-get install feh'.
   set_random_background(command='feh --bg-scale {image}',
                         directory=os.path.expanduser('~/Pictures/Backgrounds'))

   # Start my favorite programs.
   launch_program('gvim')
   launch_program('nm-applet')
   launch_program('keepassx $HOME/Documents/Passwords/Personal.kdb -min -lock',
                  is_running='pgrep -f "keepassx $HOME/Documents/Passwords/Personal.kdb"')
   # I actually use three encrypted key passes, two of them for work. I omitted
   # those here, but their existence explains the complex is_running command.
   launch_program('fluxgui', is_running='pgrep -f $(which fluxgui)')

   # The remaining programs require an active internet connection.
   wait_for_internet_connection()

   launch_program('chromium-browser', is_running='pidof /usr/lib/chromium-browser/chromium-browser')
   launch_program('pidgin')
   if location == 'home':
       # Mozilla Thunderbird is only useful at home (at work IMAPS port 993 is blocked).
       launch_program('thunderbird', is_running='pidof /usr/lib/thunderbird/thunderbird')
   launch_program('dropbox start', is_running='pgrep -f "$HOME/.dropbox-dist/*/dropbox"')
   launch_program('spotify')

Location awareness
------------------

The location awareness works by matching the `MAC address`_ of your current
`network gateway`_ (your router). I've previously also used public IPv4
addresses but given the fact that most consumers will have a dynamic IP address
I believe the gateway MAC access is the most stable unique property to match.

About the name
--------------

In programming culture the abbreviation DWIM stands for `Do What I Mean`_. The
linked Wikipedia article refers to Interlisp_ but I actually know the term from
the world of Perl_. The reason I chose this name for my application launcher is
because I like to make computer systems anticipate what I want. Plugging in a
network cable, booting my laptop and having all my commonly used programs
(depending on my physical location) instantly available at startup is a great
example of Do What I Mean if you ask me :-)

Contact
-------

The latest version of `dwim` is available on PyPI_ and GitHub_. The
documentation is hosted on `Read the Docs`_. For bug reports please create an
issue on GitHub_. If you have questions, suggestions, etc. feel free to send me
an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2017 Peter Odding.

.. External references:
.. _Bash: http://en.wikipedia.org/wiki/Bash_(Unix_shell)
.. _Do What I Mean: http://en.wikipedia.org/wiki/DWIM
.. _Dropbox: http://en.wikipedia.org/wiki/Dropbox_(service)
.. _GitHub: https://github.com/xolox/python-dwim
.. _Interlisp: http://en.wikipedia.org/wiki/Interlisp
.. _MAC address: http://en.wikipedia.org/wiki/MAC_address
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _network gateway: http://en.wikipedia.org/wiki/Gateway_(telecommunications)
.. _per user site-packages directory: https://www.python.org/dev/peps/pep-0370/
.. _Perl: http://en.wikipedia.org/wiki/Perl
.. _peter@peterodding.com: peter@peterodding.com
.. _Pidgin: http://en.wikipedia.org/wiki/Pidgin_(software)
.. _PyPI: https://pypi.python.org/pypi/dwim
.. _Python: http://en.wikipedia.org/wiki/Python_(programming_language)
.. _Read the Docs: https://dwim.readthedocs.io/en/latest/
.. _the documentation: https://dwim.readthedocs.io/en/latest/#function-reference
.. _virtual environments: http://docs.python-guide.org/en/latest/dev/virtualenvs/
