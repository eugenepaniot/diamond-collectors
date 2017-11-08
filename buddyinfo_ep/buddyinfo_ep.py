# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 textwidth=79 autoindent

"""
Python source code
Last modified: 15 Feb 2014 - 13:38
Last author: lmwangi at gmail  com

Displays the available memory fragments
by querying /proc/buddyinfo

Example:
# python buddyinfo.py

"""
import diamond.collector
from diamond.utils.signals import SIGALRMException
from decimal import Decimal
from itertools import islice
from collections import defaultdict

import os
import re
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



class BuddyInfo(object):
    """BuddyInfo DAO"""
    def __init__(self, logger):
        super(BuddyInfo, self).__init__()
        self.log = logger
        self.buddyinfo = self.load_buddyinfo()

    def parse_line(self, line):
        line = line.strip()
        self.log.debug("Parsing line: %s" % line)
        parsed_line = re.match("Node\s+(?P<numa_node>\d+).*zone\s+(?P<zone>\w+)\s+(?P<nr_free>.*)", line).groupdict()
        self.log.debug("Parsed line: %s" % parsed_line)
        return parsed_line

    def read_buddyinfo(self):
        buddyhash = defaultdict(list)
        buddyinfo = open("/proc/buddyinfo").readlines()
        for line in map(self.parse_line, buddyinfo):
            numa_node =  int(line["numa_node"])
            zone = line["zone"]
            free_fragments = map(int, line["nr_free"].split())
            max_order = len(free_fragments)
            fragment_sizes = self.get_order_sizes(max_order)
            usage_in_bytes =  [block[0] * block[1] for block in zip(free_fragments, fragment_sizes)]
            buddyhash[numa_node].append({
                "zone": zone,
                "nr_free": free_fragments,
                "sz_fragment": fragment_sizes,
                "usage": usage_in_bytes })
        return buddyhash

    def load_buddyinfo(self):
        buddyhash = self.read_buddyinfo()
        self.log.debug(buddyhash)
        return buddyhash

    def page_size(self):
        return os.sysconf("SC_PAGE_SIZE")

    def get_order_sizes(self, max_order):
        return [self.page_size() * 2**order for order in range(0, max_order)]

    def __str__(self):
        ret_string = ""
        width = 20
        for node in self.buddyinfo:
            ret_string += "Node: %s\n" % node
            for zoneinfo in self.buddyinfo.get(node):
                ret_string += " Zone: %s\n" % zoneinfo.get("zone")
                ret_string += " Free KiB in zone: %.2f\n" % (sum(zoneinfo.get("usage")) / (1024.0))
                ret_string += '\t{0:{align}{width}} {1:{align}{width}} {2:{align}{width}}\n'.format(
                        "Fragment size", "Free fragments", "Total available KiB",
                        width=width,
                        align="<")
                for idx in range(len(zoneinfo.get("sz_fragment"))):
                    ret_string += '\t{order:{align}{width}} {nr:{align}{width}} {usage:{align}{width}}\n'.format(
                        width=width,
                        align="<",
                        order = zoneinfo.get("sz_fragment")[idx],
                        nr = zoneinfo.get("nr_free")[idx],
                        usage = zoneinfo.get("usage")[idx] / 1024.0)

        return ret_string



class BuddyInfoEPCollector(diamond.collector.Collector):
    log = None

    def get_default_config_help(self):
        config_help = super(BuddyInfoEPCollector, self).get_default_config_help()
        config_help.update({ })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(BuddyInfoEPCollector, self).get_default_config()
        config.update({
            'path':     'buddyinfoep'
        })
        return config

    def collect(self):
        try:
            buddy = BuddyInfo(self.log)
            self.log.debug(buddy)

            for node in buddy.buddyinfo:
                metric_node = "nodes.%d" % node

                for zoneinfo in buddy.buddyinfo.get(node):
                    metric_zone = "%s.zones.%s" % (metric_node, zoneinfo.get("zone"))

                    free = sum(zoneinfo.get("usage"))
                    self.publish_gauge("%s.free" % metric_zone, Decimal(free))

                    for idx in range(len(zoneinfo.get("sz_fragment"))):
                        metric_fz = "%s.fragments.%dk" % (metric_zone, (zoneinfo.get("sz_fragment")[idx] / 1024.0) )
                        # self.log.debug(metric_fz)

                        nr_free = zoneinfo.get("nr_free")[idx]
                        self.publish_gauge("%s.nr_free" % metric_fz, Decimal(nr_free))

                        free = zoneinfo.get("usage")[idx]
                        self.publish_gauge("%s.free" % metric_fz, Decimal(free))

                    # self.log.info(metric_zone)
                    # self.log.debug(zoneinfo)

            # metric = metric_zone

            # self.log.info(metric)

            # return True

        except SIGALRMException as e:
            # sigalrm is raised if the collector takes too long
            raise e

        except Exception as e:
            self.log.exception("Couldn't collect: %s", e)
            return None

# def main():
#     """Main function. Called when this file is a shell script"""
#     usage = "usage: %prog [options]"
#     parser = optparse.OptionParser(usage)
#     parser.add_option("-s", "--size", dest="size", choices=["B","K","M"],
#                       action="store", type="choice", help="Return results in bytes, kib, mib")

#     (options, args) = parser.parse_args()
#     logger = Logger(logging.DEBUG).get_logger()
#     logger.info("Starting....")
#     logger.info("Parsed options: %s" % options)
#     print logger
#     buddy = BuddyInfo(logger)
#     

# logging.TRACE = 5
# logging.setLoggerClass(Logger)
# logging.addLevelName(logging.TRACE, "TRACE")

# formatter = logging.Formatter('%(levelname)-5s %(module)s %(funcName)s(%(lineno)d): %(message)s')
# colorHandler = ColorizingStreamHandler(sys.stdout)
# colorHandler.setFormatter(formatter)

# root_logger = logging.getLogger()
# root_logger.addHandler(colorHandler)
# root_logger.setLevel(0)

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# c = BuddyInfoEPCollector()
# c.log = logger

# c.collect()