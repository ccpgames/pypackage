"""Choose python classifiers with a curses frontend."""


from __future__ import unicode_literals

import os
import curses
from collections import namedtuple

from .constants import VERSION
from .constants import CHECKMARK


class BoxSelector(object):  # pragma: no cover
    """Originally designed for accman.py.

    Display options build from a list of strings in a (unix) terminal.
    The user can browser though the textboxes and select one with enter.

    Used in pypackage to display the python trove classifiers in a somewhat
    logical/easy to navigate way. The unfortunate part is that this uses
    curses to display this to the user. Ideally a cross-platform solution can
    be found to replace this class.

    Known issues:
        curses incorrectly handles unicode, might look like crap, YMMV
        curses uses (y,x) for coordinates because fuck your logic
        curses support on winderps is sketchy/non-existant
    """

    # Author: Nikolai Tschacher
    # Date: 02.06.2013
    # adapted for use in pypackage by Adam Talsma in May 2015

    def __init__(self, classifier, screen, choices=None, current=0):
        """Create a BoxSelector object.

        Args:
            classifier: the Classifier root to find choices inside of
            screen: the curses screen object
            choices: a list of values in the classifier that are selected
            current: integer index of classifiers/values to start on
        """

        self.stdscr = screen

        choices = choices or []
        self.current_selected = current

        selections = []
        if classifier.name != "__root__":
            selections.append("..")

        for group in classifier.classifiers:
            selections.append("[+] {}".format(group.name))

        for value in classifier.values:
            selections.append(" {}  {}".format(
                CHECKMARK if value in choices else " ",
                value,
            ))

        # Element parameters. Change them here.
        self.TEXTBOX_WIDTH = max(79, max([len(i) for i in selections]) + 2)
        self.TEXTBOX_HEIGHT = 3

        if classifier.name == "__root__":
            selections.append("Done".center(self.TEXTBOX_WIDTH - 4, " "))

        self.L = selections

        self.PAD_WIDTH = 600
        self.PAD_HEIGHT = 10000

    def pick(self):
        """Runs the user selection proccess, returns their choice index."""

        self._init_curses()
        self._create_pad()

        windows = self._make_textboxes()
        picked = self._select_textbox(windows)

        self._end_curses()

        return picked

    def _init_curses(self):
        """Initializes the curses appliation."""

        # turn off automatic echoing of keys to the screen
        curses.noecho()
        # Enable non-blocking mode. Keys are read without hitting enter
        curses.cbreak()
        # Disable the mouse cursor.
        curses.curs_set(0)
        self.stdscr.keypad(1)
        # Enable colorous output.
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.stdscr.bkgd(curses.color_pair(2))
        self.stdscr.refresh()

    def _end_curses(self):
        """Terminates the curses application."""

        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def _create_pad(self):
        """Creates a big self.pad to place the textboxes in."""

        self.pad = curses.newpad(self.PAD_HEIGHT, self.PAD_WIDTH)
        self.pad.box()

    def _make_textboxes(self):
        """Build the textboxes in the center of the pad."""

        # Get the actual screensize.
        maxy, maxx = self.stdscr.getmaxyx()

        banner = "{} -- choose python trove classifiers".format(VERSION)
        self.stdscr.addstr(0, maxx // 2 - len(banner) // 2, banner)

        windows = []
        i = 2
        for item in self.L:
            pad = self.pad.derwin(
                self.TEXTBOX_HEIGHT,
                self.TEXTBOX_WIDTH,
                i,
                self.PAD_WIDTH // 2 - self.TEXTBOX_WIDTH // 2,
            )
            pad.box()
            try:
                pad.addstr(1, 2, item)
            except UnicodeEncodeError:
                # curses has fucked unicode support
                item = item.replace(CHECKMARK, "*")
                pad.addstr(1, 2, item)
            windows.append(pad)
            i += self.TEXTBOX_HEIGHT

        return windows

    def _center_view(self, window):
        """Centers and aligns the view according to the window argument given.

        Returns:
            the (y, x) coordinates of the centered window
        """

        # The refresh() and noutrefresh() methods of a self.pad require 6 args
        # to specify the part of self.pad to be displayed and the location on
        # the screen to be used for the display. The arguments are pminrow,
        # pmincol, sminrow, smincol, smaxrow, smaxcol; the p arguments refer
        # to the top left corner of the self.pad region to be displayed and the
        # s arguments define a clipping box on the screen within which the
        # self.pad region is to be displayed.
        cy, cx = window.getbegyx()
        maxy, maxx = self.stdscr.getmaxyx()
        self.pad.refresh(cy, cx, 1, maxx // 2 - self.TEXTBOX_WIDTH // 2,
                         maxy - 1, maxx - 1)
        return (cy, cx)

    def _select_textbox(self, windows):
        """Handles keypresses and user selection."""

        # See at the root textbox.
        topy, topx = self._center_view(windows[0])

        last = self.current_selected - 1
        top_textbox = windows[0]

        while True:
            # Highligth the selected one, the last selected textbox should
            # become normal again.
            windows[self.current_selected].bkgd(curses.color_pair(1))
            windows[last].bkgd(curses.color_pair(2))

            # While the textbox can be displayed on the page with the current
            # top_textbox, don't alter the view. When this becomes impossible,
            # center the view to last displayable textbox on the previous view.
            maxy, maxx = self.stdscr.getmaxyx()
            cy, cx = windows[self.current_selected].getbegyx()

            # The current window is to far down. Switch the top textbox.
            if ((topy + maxy - self.TEXTBOX_HEIGHT) <= cy):
                top_textbox = windows[self.current_selected]

            # The current window is to far up. There is a better way though...
            if topy >= cy + self.TEXTBOX_HEIGHT:
                top_textbox = windows[self.current_selected]

            if last != self.current_selected:
                last = self.current_selected

            topy, topx = self._center_view(top_textbox)

            c = self.stdscr.getch()

            # Vim like KEY_UP/KEY_DOWN with j(DOWN) and k(UP).
            if c in (106, curses.KEY_DOWN):  # 106 == j
                if self.current_selected >= len(windows) - 1:
                    self.current_selected = 0  # wrap around.
                else:
                    self.current_selected += 1
            elif c in (107, curses.KEY_UP):  # 107 == k
                if self.current_selected <= 0:
                    self.current_selected = len(windows) - 1  # wrap around.
                else:
                    self.current_selected -= 1
            elif c == 113:  # 113 = q == Quit without selecting.
                break
            # At hitting enter, return the index of the selected list element.
            elif c == curses.KEY_ENTER or c == 10:
                return int(self.current_selected)
            elif c == 27:  # esc or alt, try to determine which
                self.stdscr.nodelay(True)
                n_seq = self.stdscr.getch()
                self.stdscr.nodelay(False)
                if n_seq == -1:
                    # Escape was pressed, check if the top option has .. in it
                    if ".." in str(windows[0].instr(1, 0)):
                        return 0  # backs up a level
                    else:
                        break  # exits


Classifier = namedtuple("Classifier", ("name", "values", "classifiers"))


def _ensure_chain(top_level, sub_categories):
    """Ensure a chain of Classifiers from top_level through sub_categories."""

    def _chain_in(level, item):
        for sub_class in level.classifiers:
            if sub_class.name == item:
                return sub_class
        else:
            new_sub = Classifier(item, [], [])
            level.classifiers.append(new_sub)
            return new_sub

    for sub_cat in sub_categories:
        top_level = _chain_in(top_level, sub_cat)

    return top_level


def read_classifiers():
    """Reads the trove file and returns a Classifier representing all."""

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
              "classifiers")) as openc:
        classifiers = [c.strip() for c in openc.read().splitlines() if c]

    all_classifiers = []

    def _get_classifier(categories):
        """Find or create the classifier for categories."""

        top_level = categories[0]
        sub_categories = categories[1:]
        for classifier in all_classifiers:
            if classifier.name == top_level:
                top_level = classifier
                break
        else:
            top_level = Classifier(top_level, [], [])
            all_classifiers.append(top_level)

        return _ensure_chain(top_level, sub_categories)

    for clsifier in classifiers:
        _get_classifier(clsifier.split(" :: ")[:-1]).values.append(clsifier)

    return Classifier("__root__", [], all_classifiers)


def back_it_up(current_level, all_classifiers, recursive=False):
    """Returns the classifier up a level from current."""

    for classifier in all_classifiers.classifiers:
        if current_level in classifier.classifiers:
            return classifier

    for classifier in all_classifiers.classifiers:
        attempt = back_it_up(current_level, classifier, True)
        if attempt:
            return attempt

    if not recursive:
        return all_classifiers


def choose_classifiers(config):
    """Get some user input for the classifiers they'd like to use.

    Returns:
        list of valid classifier names
    """

    all_classifiers = read_classifiers()
    root_classifier = all_classifiers
    old_delay = os.getenv("ESCDELAY")
    os.environ["ESCDELAY"] = "25"  # the default delay is a full second...
    screen = curses.initscr()
    choices = getattr(config, "classifiers", [])
    choice = BoxSelector(root_classifier, screen, choices).pick()
    while choice is not None:
        init = 0
        if choice == 0 and root_classifier.name != "__root__":
            root_classifier = back_it_up(root_classifier, all_classifiers)
        elif choice == 9 and root_classifier.name == "__root__":
            break   # the "done" box from the top level
        elif choice > len(root_classifier.classifiers):
            choice_index = (choice - len(root_classifier.classifiers) -
                            int(root_classifier.name != "__root__"))
            choice_as_str = root_classifier.values[choice_index]
            if choice_as_str not in choices:
                choices.append(choice_as_str)
            else:
                choices.remove(choice_as_str)
            init = choice
        else:
            choice_index = choice - int(root_classifier.name != "__root__")
            root_classifier = root_classifier.classifiers[choice_index]

        choice = BoxSelector(root_classifier, screen, choices, init).pick()

    if old_delay:
        os.environ["ESCDELAY"] = old_delay
    else:
        os.environ.pop("ESCDELAY")

    return choices
