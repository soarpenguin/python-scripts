#!/usr/bin/env python
import os

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

def _ioctl_GWINSZ(fd):                  #### TABULATION FUNCTIONS
    try:                                ### Discover terminal width
        import fcntl
        import termios
        import struct
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
        return
    return cr

def terminal_size():                    ### decide on *some* terminal size
    """Return (lines, columns)."""
    cr = _ioctl_GWINSZ(0) or _ioctl_GWINSZ(1) or _ioctl_GWINSZ(2) # try open fds
    if not cr:                                                  # ...then ctty
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = _ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
        if not cr:                            # env vars or finally defaults
            try:
                cr = os.environ['LINES'], os.environ['COLUMNS']
            except:
                cr = 25, 80
    return int(cr[1]), int(cr[0])         # reverse rows, cols

