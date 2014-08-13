import sys
import abc

if sys.hexversion < 0x020700f0:  # hex number for 2.7.0 final release
    sys.exit("Python 2.7.0 or newer is required to run this program.")


# Colors (http://en.wikipedia.org/wiki/ANSI_escape_code#Colors)

RED   = "\x1b[31m"
GREEN = "\x1b[32m"
CYAN  = "\x1b[36m"
WHITE = "\x1b[37m"
YELLOW = "\x1b[33m"
BLUE   = "\x1b[34m"
MAGENTA = "\x1b[35m"
COL_RESET = "\x1b[0m"

class PygressBar(object):
    """Progress bar abstract base class"""

    __metaclass__ = abc.ABCMeta

    def __init__(self, length, filled_repr, empty_repr, left_limit, right_limit,
                 start, head_repr, format, scale_start, scale_end):
        """Constructor of the abstract base class

        :param length: The length of the bar (without limits)
        :type length: int
        :param filled_repr: This will be represent one filled space
        :type filled_repr: string
        :param empty_repr: This will be represent one empty space
        :type empty_repr: string
        :param left_limit: The limit representation of the left side
        :type left_limit: string
        :param right_limit: The limit representation of the right side
        :type right_limit: string
        :param start: The point the progress bar progress will start
        :type start: int
        :param head_repr: The representation space of the head (Coul be None)
        :type head_repr: string
        :param format: The format of the bar (By default there is one)
        :type format: string
        :param scale_start: The scale number where starts
        :type scale_start: int
        :param scale_end: The scale number where ends
        :type scale_end: int
        """
        self._length = length
        self._filled_repr = filled_repr
        self._empty_repr = empty_repr
        self._left_limit = left_limit
        self._right_limit = right_limit
        self._head_repr = head_repr
        self._start = start
        self._progress = self._start

        #Check the scale
        if scale_start >= scale_end:
            raise ValueError("scale start must be less than scale end")

        self._scale_start = scale_start
        self._scale_end = scale_end
        if not format:
            self._format = "{left_limit}{{:{filled_repr}>{filled_length}}}" +\
                            "{{:{empty_repr}<{empty_length}}}{right_limit}"
        else:
            self._format = format
        # Initialize progress bar
        self._progress_bar = None
        self._make_progress_bar()

    @abc.abstractmethod
    def _create_bar_format(self, filled_length, empty_length):
        """Creates the format of the bar ready to fill in

        :param filled_length: The length of the filled area
        :type filled_length: int
        :param empty_length: The length of the empty area
        :type empty_length: int
        """
        # Create the formatting string for the bar
        return self._format.format(left_limit=self._left_limit,
                                   filled_repr=self._filled_repr,
                                   filled_length=filled_length,
                                   empty_repr=self._empty_repr,
                                   empty_length=empty_length,
                                   right_limit=self._right_limit)

    def _make_progress_bar(self):
        """Creates the progress bar based on the object information and stores
        the bar in the object
        """

        # Create the length of the bar (0 to 100)
        scale = self._scale_end - self._scale_start
        filled_length = (self._length * self._progress // scale)

        # The rest of the bar
        empty_length = self._length - filled_length

        #create the format
        repr_format_str = self._create_bar_format(filled_length, empty_length)

        # Get the head char. This depends on the progress of the bar
        # If the filled lenght is 0 (0 chars) then is no head nor body
        if not filled_length:
            head = ''
        else:  # If there is no head, then is the fill char representation
            head = self._filled_repr if not self._head_repr else self._head_repr

        # Create the progress bar (right head char is always blank)
        self._progress_bar = repr_format_str.format(head, '')

    def increase(self, incr):
        """Increases by a number the progress bar"""
        self._progress += incr

        # Check bounds
        if self._progress > self._scale_end:
            self._progress = self._scale_end

        self._make_progress_bar()  # Update

    def decrease(self, incr):
        """decreases by a number the progress bar"""
        self._progress -= incr

        # Check bounds
        if self._progress < self._scale_start:
            self._progress = self._scale_start

        self._make_progress_bar()

    def completed(self):
        """Returns true if the progress has finished"""
        return self._progress >= self._scale_end

    def show_progress_bar(self):
        """Prints in the terminal the progress bar. valid for animation"""
        if sys.stderr.isatty():
            sys.stderr.write(self._progress_bar + '\r')
        else:
            print(self._progress_bar + "\n")

    @staticmethod
    def hide_cursor():
        sys.stdout.write("\x1b[?25l")

    @staticmethod
    def show_cursor():
        sys.stdout.write("\x1b[?25h")

    def __str__(self):
        return self.progress_bar

    @property
    def progress_bar(self):
        return self._progress_bar

    @property
    def progress(self):
        return self._progress


class SimpleProgressBar(PygressBar):
    def __init__(self):
        super(SimpleProgressBar, self).__init__(length=20,
                                               filled_repr='=',
                                               empty_repr=' ',
                                               left_limit='[',
                                               right_limit=']',
                                               start=0,
                                               head_repr='>',
                                               format=None,
                                               scale_start=0,
                                               scale_end=100)

    def _create_bar_format(self, filled_length, empty_length):
        return super(SimpleProgressBar, self)._create_bar_format(filled_length,
                                                                 empty_length)


class SimplePercentProgressBar(PygressBar):
    def __init__(self):
        super(SimplePercentProgressBar, self).__init__(length=20,
                                                       filled_repr='=',
                                                       empty_repr=' ',
                                                       left_limit='[',
                                                       right_limit=']',
                                                       start=0,
                                                       head_repr='>',
                                                       format=None,
                                                       scale_start=0,
                                                       scale_end=100)

    def _create_bar_format(self, filled_length, empty_length):
        scale = self._scale_end - self._scale_start
        percent = 100 * self._progress // scale
        percent = 100 if percent > 100 else percent  # Not greater than 100
        percent = "({0}%)".format(percent)

        return self._format.format(left_limit=self._left_limit,
                                   filled_repr=self._filled_repr,
                                   filled_length=filled_length,
                                   empty_repr=self._empty_repr,
                                   empty_length=empty_length,
                                   right_limit=self._right_limit) + percent


class SimpleAnimatedProgressBar(PygressBar):
    """Simple progress bar with the head animated"""

    def __init__(self, animation=('|', '/', '-', '\\'), speed=50):
        """Constructor

        :param animation: The head animation sequence
        :type animation: tuple
        :param speed: The speed of the animation head (0-2000)
        :type speed: int
        """

        self._animation = animation
        self._animation_state = 0
        head = animation[0]

        max_speed = 2000
        if speed < 0 or speed > max_speed:
            raise ValueError("Speed needs to e between 0(slow) and 2000(fast)")

        # Reverse number
        self._speed_control = max_speed - speed
        self._speed_status = 0

        super(SimpleAnimatedProgressBar, self).__init__(length=20,
                                                       filled_repr='=',
                                                       empty_repr=' ',
                                                       left_limit='[',
                                                       right_limit=']',
                                                       start=0,
                                                       head_repr=head,
                                                       format=None,
                                                       scale_start=0,
                                                       scale_end=100)

    def _create_bar_format(self, filled_length, empty_length):
        # To control the speed we need to check if we have to change the head
        # If we have reach to the spped control, means that we have printed
        # the needed times to change the head (see below show_progress_bar)
        if self._speed_status == self._speed_control:

            #Adjust next state of the animation
            if self._animation_state == len(self._animation) - 1:
                self._animation_state = 0
            else:
                self._animation_state += 1
            #Update head
            self._head_repr = self._animation[self._animation_state]

        return super(SimpleAnimatedProgressBar, self)._create_bar_format(
                                                                filled_length,
                                                                empty_length)

    def _increment_speed_status(self):
        # If we hace reach to the needed printed times then update the progress
        # bar with the new head
        if self._speed_status >= self._speed_control:
            # First update the bar with the new head and then reload
            # the speed counter
            self._make_progress_bar()
            self._speed_status = 0
        else:
            self._speed_status += 1

    @property
    def progress_bar(self):
        self._increment_speed_status()
        return super(SimpleAnimatedProgressBar, self).progress_bar

    def show_progress_bar(self):
        self._increment_speed_status()
        return super(SimpleAnimatedProgressBar, self).show_progress_bar()


class SimpleColorBar(PygressBar):
    def __init__(self,
                 left_limit_clr=GREEN,
                 right_limit_clr=GREEN,
                 head_clr=RED,
                 filled_clr=BLUE,
                 empty_clr=MAGENTA):
        """Constructor

        :param left_limit_clr: Color of the left limit
        :type left_limit_clr: string (ANSI terminal color)
        :param right_limit_clr: Color of the right limit
        :type right_limit_clr: string (ANSI terminal color)
        :param head_clr: Head character color
        :type head_clr: string (ANSI terminal color)
        :param filled_clr: Filled character color
        :type filled_clr: string (ANSI terminal color)
        :param empty_clr: Empty character color
        :type empty_clr: string (ANSI terminal color)
        """

        self._left_limit_clr = left_limit_clr
        self._right_limit_clr = right_limit_clr
        self._head_clr = head_clr
        self._filled_clr = filled_clr
        self._empty_clr = empty_clr

        # Create the new color format

        format = left_limit_clr + "{left_limit}" + COL_RESET +\
                 filled_clr + "{{:{filled_repr}>{filled_length}}}" +\
                                                         COL_RESET +\
                 empty_clr + "{{:{empty_repr}<{empty_length}}}" +\
                                                      COL_RESET +\
                 right_limit_clr + "{right_limit}" + COL_RESET

        # Format the head
        head = COL_RESET + head_clr + '>'

        super(SimpleColorBar, self).__init__(length=20,
                                             filled_repr='=',
                                             empty_repr='.',
                                             left_limit='[',
                                             right_limit=']',
                                             start=0,
                                             head_repr=head,
                                             format=format,
                                             scale_start=0,
                                             scale_end=100)

    def _create_bar_format(self, filled_length, empty_length):
        #Fix the head lenght
        if filled_length > 0:
            filled_length += len(self._head_clr) + len(COL_RESET) * 1

        return super(SimpleColorBar, self)._create_bar_format(filled_length,
                                                              empty_length)


class CustomProgressBar(PygressBar):
    def __init__(self,
                length,
                filled_repr,
                empty_repr,
                left_limit,
                right_limit,
                start,
                head_repr,
                scale_start,
                scale_end):
        super(CustomProgressBar, self).__init__(length=length,
                                                filled_repr=filled_repr,
                                                empty_repr=empty_repr,
                                                left_limit=left_limit,
                                                right_limit=right_limit,
                                                start=start,
                                                head_repr=head_repr,
                                                format=None,
                                                scale_start=scale_start,
                                                scale_end=scale_end)

    def _create_bar_format(self, filled_length, empty_length):
        return super(CustomProgressBar, self)._create_bar_format(filled_length,
                                                                 empty_length)
