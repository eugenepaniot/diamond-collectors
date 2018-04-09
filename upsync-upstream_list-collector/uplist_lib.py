# coding=utf-8
import os
import sys
import logging
import logging.handlers

class ColorizingStreamHandler(logging.StreamHandler):
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    BROWN = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    GREY = '\033[0;37m'

    DARK_GREY = '\033[1;30m'
    LIGHT_RED = '\033[1;31m'
    LIGHT_GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    LIGHT_BLUE = '\033[1;34m'
    LIGHT_PURPLE = '\033[1;35m'
    LIGHT_CYAN = '\033[1;36m'
    WHITE = '\033[1;37m'

    DIM = '\033[2m'
    BOLD = '\033[1m'
    BLINK = '\033[5m'

    RESET = "\033[0m"

    TRACE = "%s" % (DARK_GREY)
    DEBUG = "%s%s" % (LIGHT_CYAN, DIM)
    INFO = "%s%s" % (GREEN, DIM)
    WARNING = "%s%s" % (YELLOW, BOLD)
    ERROR = "%s" % RED
    CRITICAL = "%s%s%s" % (BLINK, RED, BOLD)

    def __init__(self, *args, **kwargs):
        self._colors = {logging.TRACE: self.TRACE,
                        logging.DEBUG: self.DEBUG,
                        logging.INFO: self.INFO,
                        logging.WARNING: self.WARNING,
                        logging.ERROR: self.ERROR,
                        logging.CRITICAL: self.CRITICAL}
        super(ColorizingStreamHandler, self).__init__(*args, **kwargs)

    @property
    def is_tty(self):
        # isatty = getattr(self.stream, 'isatty', None)
        # return isatty and isatty()
        return True

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.is_tty:
                stream.write(message)
            else:
                message = self._colors[record.levelno] + message + self.RESET
                stream.write(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def setLevelColor(self, logging_level, escaped_ansi_code):
        self._colors[logging_level] = escaped_ansi_code


class Logger(logging.getLoggerClass()):
    def __init__(self, name, level=logging.NOTSET):
        super(Logger, self).__init__(name, level)

    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.TRACE):
            self._log(logging.TRACE, msg, args, **kwargs)


