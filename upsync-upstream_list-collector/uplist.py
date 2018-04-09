# coding=utf-8
import urllib2

import diamond.collector
import re
from diamond.utils.signals import SIGALRMException


class UpsyncUpstreamListCollector(diamond.collector.Collector):
    upstream_nameRE = re.compile('Upstream name: (?P<upstreamName>.*); '
                                 'Backend server count: (?P<backendCount>\d+)')

    serverRE = re.compile('\s+server (?P<addr>.*) '
                          'weight=(?P<weight>\d+) '
                          'max_fails=(?P<max_fails>\d+) '
                          'fail_timeout=(?P<fail_timeout>\d+)s '
                          'current_weight=(?P<current_weight>[+-]?\d+) '
                          'conns=(?P<conns>\d+) '
                          'max_conns=(?P<max_conns>\d+) '
                          'fails=(?P<fails>\d+)'
                          ';')

    log = None

    def get_default_config_help(self):
        config_help = super(UpsyncUpstreamListCollector, self).get_default_config_help()
        config_help.update({
            'url': 'http://127.0.0.1/upstream_list'
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(UpsyncUpstreamListCollector, self).get_default_config()
        config.update({
            'url': 'http://127.0.0.1/upstream_list'
        })
        return config

    def collect(self):
        headers = {}
        req = urllib2.Request(url=self.config['url'], headers=headers)
        try:
            handle = urllib2.urlopen(req)
            upstream = {}
            s = 0
            for l in handle.readlines():
                l = l.rstrip('\r\n')
                if l == "":
                    # self.log.info("upstream: %s" % repr(upstream))

                    prefix = "%s" % upstream["name"]
                    self.publish_gauge('%s.backendCount' % prefix, upstream["backendCount"])

                    for id in upstream["servers"]:
                        serversPrefix = "%s.servers.%d" % (prefix, id)
                        items = upstream["servers"][id]
                        for key, value in items.iteritems():
                            self.publish_gauge('%s.%s' % (serversPrefix, key), int(value))
                            # self.log.debug('%s.%s = %d' % (serversPrefix, key, int(value)))

                    upstream = {}
                    s = 0
                    continue

                if l.startswith('Upstream name: '):
                    m = self.upstream_nameRE.match(l)
                    if m:
                        upstream["name"] = m.group('upstreamName')
                        upstream["backendCount"] = m.group('backendCount')

                if l.startswith('        server') and upstream["name"]:
                    m = self.serverRE.match(l)
                    if m:
                        s = s + 1
                        if "servers" not in upstream:
                            upstream["servers"] = {}

                        upstream["servers"][s] = {}
                        # upstream["servers"][s]["weight"] = m.group('weight')
                        upstream["servers"][s]["max_fails"] = m.group('max_fails')
                        # upstream["servers"][s]["fail_timeout"] = m.group('fail_timeout')
                        # upstream["servers"][s]["current_weight"] = m.group('current_weight')
                        upstream["servers"][s]["conns"] = m.group('conns')
                        upstream["servers"][s]["max_conns"] = m.group('max_conns')
                        upstream["servers"][s]["fails"] = m.group('fails')

            return True
        except SIGALRMException as e:
            # sigalrm is raised if the collector takes too long
            raise e
        except Exception as e:
            self.log.exception("Couldn't collect: %s", e)
            return None


# from uplist_lib import *
#
# logging.TRACE = 5
# logging.setLoggerClass(Logger)
# logging.addLevelName(logging.TRACE, "TRACE")
#
# formatter = logging.Formatter('%(levelname)-5s %(module)s %(funcName)s(%(lineno)d): %(message)s')
# colorHandler = ColorizingStreamHandler(sys.stdout)
# colorHandler.setFormatter(formatter)
#
# root_logger = logging.getLogger()
# root_logger.addHandler(colorHandler)
# root_logger.setLevel(0)
#
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
# c = UpsyncUpstreamListCollector()
# c.log = logger
#
# c.collect()
