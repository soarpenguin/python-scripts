#!/usr/bin/env python


def clrscr():
    """ Clear screen and move cursor to 1,1 (upper left) pos. """
    print '\033[2J\033[1;1H'


def clreol():
    """ Erases from the current cursor position to the end of the current line. """
    print '\033[K'


def delline():
    """ Erases the entire current line. """
    print '\033[2K'


def gotoxy(x, y):
    """ Moves the cursor to the specified position. """
    print "\033[%d;%dH" % (x, y)
