# coding=utf-8

"""
This class collects data from plain text files

#### Dependencies

"""

import glob
import diamond.collector
import os
import re

_RE = re.compile(r'([A-Za-z0-9._-]+)[\s=:]+(-?[0-9]+)(\.?\d*)')


class WFilesCollector(diamond.collector.Collector):
    def get_default_config_help(self):
        config_help = super(WFilesCollector, self).get_default_config_help()
        config_help.update({
            'path': 'Prefix added to all stats collected by this module, a '
                    'single dot means don''t add prefix',
            'files': 'The bash file glob that the performance files are in'
        })
        return config_help

    def get_default_config(self):
        """
        Returns default collector settings.
        """
        config = super(WFilesCollector, self).get_default_config()
        config.update({
            'path': '.',
            'files': '/tmp/tel_*.txt'
        })
        return config

    def collect(self):
        for fn in glob.glob(self.config['files']):
            basename = fn.replace("/", ".")
            if os.path.isfile(fn):
                try:
                    with open(fn, 'r') as fh:
                        for line in fh:
                            m = _RE.match(line)
                            if m:
                                self.publish(
                                    name="%s.%s" % (basename, m.groups()[0]),
                                    value=m.groups()[1] + m.groups()[2],
                                    precision=max(0, len(m.groups()[2]) - 1)
                                )
                except:
                    pass
