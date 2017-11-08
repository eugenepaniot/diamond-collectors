# coding=utf-8

import urllib2
import json
import diamond.collector
import re
import os


class JenkinsMetricsCollector(diamond.collector.Collector):
    def get_default_config_help(self):
        config_help = super(JenkinsMetricsCollector, self).get_default_config_help()
        config_help.update({
            'address': 'Jenkins ip/hostname address. Default read from JENKINS_SERVER env',
            'api': 'API key. Default read from JENKINS_API_KEY env',
            'filter': 'Metric regexp filter'
        })
        return config_help

    def get_default_config(self):
        config = super(JenkinsMetricsCollector, self).get_default_config()
        config.update({
            'filter': '^vm\.',
            'api': os.environ.get('JENKINS_API_KEY'),
            'address': os.environ.get('JENKINS_SERVER'),
        })
        return config

    def collect(self):
        global gauges, m
        filter = re.compile(self.config['filter'], re.IGNORECASE)

        url = "http://%s/metrics/%s/metrics" % (self.config['address'], self.config['api'])
        req = urllib2.Request(url)

        try:
            resp = urllib2.urlopen(req)
        except urllib2.URLError as e:
            self.log.error("Can't open url %s. %s", url, e)
        else:
            content = resp.read()
            try:
                data = json.loads(content)
                gauges = data['gauges']

                for m in gauges:
                    if filter.match(m):
                        # self.log.debug("%s = %s" % (m, gauges[m]['value']))
                        try:
                            value = int(gauges[m]['value'])
                        except:
                            self.log.warn("Wrong value %s for key %s", repr(gauges[m]['value']), m)
                        else:
                            self.log.debug("Publish metric %s with value %d" % (m, value))
                            self.publish(m, value)

            except ValueError as e:
                self.log.error("Can't parse JSON from %s. Error: %s", url, e)

            except TypeError as e:
                self.log.error("Can't parse value %s for key %s. Error: %s", repr(gauges[m]['value']), m, e)