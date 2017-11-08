# coding=utf-8

"""
Uses /proc/vmstat to collect data

#### Dependencies

 * /proc/vmstat

"""

import diamond.collector
from decimal import Decimal
from itertools import islice
import os
import re

class VMStatEPCollector(diamond.collector.Collector):

    PROC = '/proc/vmstat'

    def get_default_config_help(self):
        config_help = super(VMStatEPCollector, self).get_default_config_help()
        config_help.update({})
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(VMStatEPCollector, self).get_default_config()
        config.update({
            'path':     'vmstatep'
        })
        return config

    def collect(self):
        if not os.access(self.PROC, os.R_OK):
            return None

        # open file
        with open(self.PROC, "r") as f:
            try:
                for line in islice(f, 2, None):
                    k, v = line.split(" ")
                    
                    self.publish_gauge(k, Decimal(v))

            except Exception as e:
                self.log.exception("Error: %s" % e)

        # Close file
        if(f):
            f.close()