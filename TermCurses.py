# -*- coding: utf-8 -*-

"""Curses interface class."""

# Import system lib
import sys

try:
    import curses
    import curses.panel
except ImportError:
    print('Curses module not found.')
    sys.exit(1)


class TermCurses(object):

    """This class manages the curses display (and key pressed)."""

    def __init__(self, args=None):
        # Init args
        self.args = args

        # Init windows positions
        self.term_w = 80
        self.term_h = 24

        # Space between stats
        self.space_between_column = 3
        self.space_between_line = 2

        # Init the curses screen
        self.screen = curses.initscr()
        if not self.screen:
            print(_("Error: Cannot init the curses library.\n"))
            sys.exit(1)

        # Set curses options
        if hasattr(curses, 'start_color'):
            curses.start_color()
        if hasattr(curses, 'use_default_colors'):
            curses.use_default_colors()
        if hasattr(curses, 'noecho'):
            curses.noecho()
        if hasattr(curses, 'cbreak'):
            curses.cbreak()
        if hasattr(curses, 'curs_set'):
            try:
                curses.curs_set(0)
            except Exception:
                pass

        # Init colors
        self.hascolors = False
        if curses.has_colors() and curses.COLOR_PAIRS > 8:
            self.hascolors = True
            # FG color, BG color
            curses.init_pair(1, curses.COLOR_WHITE, -1)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)
            curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
            curses.init_pair(6, curses.COLOR_RED, -1)
            curses.init_pair(7, curses.COLOR_GREEN, -1)
            curses.init_pair(8, curses.COLOR_BLUE, -1)
            curses.init_pair(9, curses.COLOR_MAGENTA, -1)
        else:
            self.hascolors = False

        if args.disable_bold:
            A_BOLD = curses.A_BOLD
        else:
            A_BOLD = 0

        self.title_color = A_BOLD
        self.title_underline_color = A_BOLD | curses.A_UNDERLINE
        self.help_color = A_BOLD
        if self.hascolors:
            # Colors text styles
            self.no_color = curses.color_pair(1)
            self.default_color = curses.color_pair(3) | A_BOLD
            self.nice_color = curses.color_pair(9) | A_BOLD
            self.ifCAREFUL_color = curses.color_pair(4) | A_BOLD
            self.ifWARNING_color = curses.color_pair(5) | A_BOLD
            self.ifCRITICAL_color = curses.color_pair(2) | A_BOLD
            self.default_color2 = curses.color_pair(7) | A_BOLD
            self.ifCAREFUL_color2 = curses.color_pair(8) | A_BOLD
            self.ifWARNING_color2 = curses.color_pair(9) | A_BOLD
            self.ifCRITICAL_color2 = curses.color_pair(6) | A_BOLD
        else:
            # B&W text styles
            self.no_color = curses.A_NORMAL
            self.default_color = curses.A_NORMAL
            self.nice_color = A_BOLD
            self.ifCAREFUL_color = curses.A_UNDERLINE
            self.ifWARNING_color = A_BOLD
            self.ifCRITICAL_color = curses.A_REVERSE
            self.default_color2 = curses.A_NORMAL
            self.ifCAREFUL_color2 = curses.A_UNDERLINE
            self.ifWARNING_color2 = A_BOLD
            self.ifCRITICAL_color2 = curses.A_REVERSE

        # Define the colors list (hash table) for stats
        self.__colors_list = {
            'DEFAULT': self.no_color,
            'UNDERLINE': curses.A_UNDERLINE,
            'BOLD': A_BOLD,
            'SORT': A_BOLD,
            'OK': self.default_color2,
            'TITLE': self.title_color,
            'PROCESS': self.default_color2,
            'STATUS': self.default_color2,
            'NICE': self.nice_color,
            'CAREFUL': self.ifCAREFUL_color2,
            'WARNING': self.ifWARNING_color2,
            'CRITICAL': self.ifCRITICAL_color2,
            'OK_LOG': self.default_color,
            'CAREFUL_LOG': self.ifCAREFUL_color,
            'WARNING_LOG': self.ifWARNING_color,
            'CRITICAL_LOG': self.ifCRITICAL_color
        }

        # Init main window
        self.term_window = self.screen.subwin(0, 0)

        # Init refresh time
        if args.time:
            self.__refresh_time = args.time
        else:
            self.__refresh_time = 3

        # Init process sort method
        self.args.process_sorted_by = 'auto'

        # Catch key pressed with non blocking mode
        self.term_window.keypad(1)
        self.term_window.nodelay(1)
        self.pressedkey = -1


    def __get_key(self, window):
        # Catch ESC key AND numlock key (issue #163)
        keycode = [0, 0]
        keycode[0] = window.getch()
        keycode[1] = window.getch()

        if keycode[0] == 27 and keycode[1] != -1:
            # Do not escape on specials keys
            return -1
        else:
            return keycode[0]


    def __catch_key(self):
        # Catch the pressed key
        # ~ self.pressedkey = self.term_window.getch()
        self.pressedkey = self.__get_key(self.term_window)

        # Actions...
        if self.pressedkey == ord('\x1b') or self.pressedkey == ord('q'):
            # 'ESC'|'q' > Quit
            self.end()
            sys.exit(0)

        # Return the key code
        return self.pressedkey


    def end(self):
        """Shutdown the curses window."""
        curses.echo()
        curses.nocbreak()
        curses.curs_set(1)
        curses.endwin()


    def get_display_width(self, curse_msg, without_option=False):
        """Return the width of the formatted curses message.

        The height is defined by the maximum line.
        """
        try:
            if without_option:
                # Size without options
                c = len(max(''.join([(i['msg'] if not i['optional'] else "")
                        for i in curse_msg['msgdict']]).split('\n'), key=len))
            else:
                # Size with all options
                c = len(max(''.join([i['msg']
                        for i in curse_msg['msgdict']]).split('\n'), key=len))
        except:
            return 0
        else:
            return c

    def get_display_height(self, curse_msg):
        r"""Return the height of the formatted curses message.

        The height is defined by the number of '\n' (new line).
        """
        try:
            c = [i['msg'] for i in curse_msg['msgdict']].count('\n')
        except:
            return 0
        else:
            return c + 1
