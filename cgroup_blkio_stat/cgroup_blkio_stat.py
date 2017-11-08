#!/usr/bin/env python

from cgutils import cgroup
from cgutils import command
import diamond.collector
import json
import sys
import pprint

def format(s):
    s = s.replace('/', '_')
    s = s.replace(':', '_')

    return s

def flattenDict(d, result=None):
    if result is None:
        result = {}

    for key in d:
        value = d[key]

        if isinstance(value, dict):
            value1 = {}
            for keyIn in value:
                value1[".".join([format(key),keyIn])] = value[keyIn]
            flattenDict(value1, result)
        elif isinstance(value, (list, tuple)):
            for indexB, element in enumerate(value):
                if isinstance(element, dict):
                    value1 = {}
                    index = 0
                    for keyIn in element:
                        newkey = ".".join([format(key),keyIn])
                        value1[".".join([format(key),keyIn])] = value[indexB][keyIn]
                        index += 1
                    for keyA in value1:
                        flattenDict(value1, result)
        else:
            result[key] = int(value)

    return result

class Command(command.Command):
    def __init__(self, target_subsystem, opts={}):
        self.target_subsystem = target_subsystem

        if 'debug' in opts:
            self.debug = opts['debug']

    def run(self):
        root_cgroup = cgroup.scan_cgroups(self.target_subsystem)

        def collect_configs(_cgroup, store):
            store[_cgroup.path] = _cgroup.get_stats()

        cgroups = {}
        cgroup.walk_cgroups(root_cgroup, collect_configs, cgroups)

        if self.debug:
            json.dump(cgroups, sys.stdout, indent=4)

        return cgroups

class CgroupBlkioCollector(diamond.collector.Collector):
    def get_default_config_help(self):
        config_help = super(CgroupBlkioCollector, self).get_default_config_help()
        config_help.update({
        })

        return config_help

    def get_default_config(self):
        config = super(CgroupBlkioCollector, self).get_default_config()
        config.update({
            'path':     'cgroup_blkio'
        })

        return config

    def collect(self):
        results = {}
        r = flattenDict( Command('blkio', {'debug': 0}).run() )
        for k in r:
            self.log.debug("k: %s v: %s" % (k, r[k]))
            self.publish(k, r[k])
