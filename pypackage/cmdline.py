"""Parses flags passed on the command line.

If you're looking for the entry points, they're in commands.py, this only
deals with user options.
"""


import sys


def flags(*args):
    """Returns a boolean of if any of the flags are selected.

    -single character args can be compressed, ie; -e -g == -eg
    """

    cmd_line_flags = []
    for flag in sys.argv:
        if flag.startswith("-") and "--" not in flag and len(flag) > 2:
            cmd_line_flags.extend(["-{}".format(f) for f in flag[1:]])
        else:
            cmd_line_flags.append(flag)
    return any([arg in cmd_line_flags for arg in args])


def get_options():
    """Search through argv real quick and lazy like for some flags.

    Returns:
        configuration object with boolean attributes:
        re_classify, re_config, interactive, setup, metadata, extended,
        re_probe, no_guess, help
    """

    class Options(object):
        def __init__(self):
            self.re_classify = flags("-R", "--reclassify")
            self.re_config = flags("-r", "--reset", "--rebuild")
            self.interactive = flags("-i", "--interactive")
            self.setup = flags("-s", "--setup")
            self.metadata = flags("-m", "--metadata")
            self.extended = flags("-e", "--extended", "--all", "-a")
            self.re_probe = flags("-p", "--reprobe")
            self.no_guess = flags("-N", "--no-guess")
            self.help = flags("-h", "--help")
            self.version = flags("-v", "--version")

    return Options()
