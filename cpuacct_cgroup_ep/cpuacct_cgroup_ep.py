import os
import sys
import time
import pprint

import diamond.collector
from diamond.metric import Metric

class CgroupsCPUAcctEPCollector(diamond.collector.Collector):
    log = None

    def get_default_config_help(self):
        config_help = super(CgroupsCPUAcctEPCollector, self).get_default_config_help()
        config_help.update({
            'cgpath': """Directory path to where cpuacct is located,
defaults to /sys/fs/cgroup/cpuacct/. Redhat/CentOS/SL use /cgroup"""
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(CgroupsCPUAcctEPCollector, self).get_default_config()
        config.update({
            'cgpath':     '/sys/fs/cgroup/cpuacct/'
        })
        return config


    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(CgroupsCPUAcctEPCollector, self).get_default_config()
        config.update({
            'cgpath':     '/sys/fs/cgroup/cpuacct/'
        })
        return config

    def collect(self):
        # find all cpuacct.stat files
        matches = []
        for root, dirnames, filenames in os.walk(self.config['cgpath']):
            for filename in filenames:
                if filename == 'cpuacct.stat':
                    # matches will contain a tuple contain path to cpuacct.stat
                    # and the parent of the stat
                    parent = root.replace(self.config['cgpath'],
                                          "").replace("/", ".")
                    if parent == '':
                        parent = 'system'
                    # If the parent starts with a dot, remove it
                    if parent[0] == '.':
                        parent = parent[1:]
                    matches.append((parent, os.path.join(root, filename)))

        # Read utime and stime from cpuacct files
        results = {}
        for match in matches:
            results[match[0]] = {}
            stat_file = open(match[1])
            elements = [line.split() for line in stat_file]
            for el in elements:
                results[match[0]][el[0]] = el[1]
                stat_file.close()

        # create metrics from collected utimes and stimes for cgroups
        for parent, cpuacct in results.iteritems():
            for key, value in cpuacct.iteritems():
                metric_name = '.'.join([parent, key])
                self.publish(metric_name, value, metric_type='GAUGE')
        return True


#from cpuacct_cgroup_ep_lib import *

#logging.TRACE = 5
#logging.setLoggerClass(Logger)
#logging.addLevelName(logging.TRACE, "TRACE")

#formatter = logging.Formatter('%(levelname)-5s %(module)s %(funcName)s(%(lineno)d): %(message)s')
#colorHandler = ColorizingStreamHandler(sys.stdout)
#colorHandler.setFormatter(formatter)

#root_logger = logging.getLogger()
#root_logger.addHandler(colorHandler)
#root_logger.setLevel(0)

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

#c = CgroupsCPUAcctEPCollector()
#c.log = logger

#c.collect()

