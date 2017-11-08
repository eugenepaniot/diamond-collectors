# coding=utf-8
import os
import diamond.collector
from decimal import Decimal
from itertools import islice
from subprocess import check_output, CalledProcessError
from diamond.utils.signals import SIGALRMException

def get_pid(name):
    return map(int,check_output(["pidof",name]).split())

def sanitize_delim(name, delim):
    return ".".join(name.strip(delim).split(delim))


class SchedStatCollector(diamond.collector.Collector):
    log = None

    def get_default_config_help(self):
        config_help = super(SchedStatCollector, self).get_default_config_help()
        config_help.update({
            'procname': 'nginx,brubeck'
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(SchedStatCollector, self).get_default_config()
        config.update({
            'procname': 'nginx,brubeck'
        })
        return config

    def collect(self):
        try:
            for procname in self.config['procname'].strip().split(","):
                self.log.debug("procname: %s" % procname)
                try:
                    for pid in get_pid(procname):
                        self.log.debug("-----------------------------------------------------------------------")

                        file_schedstat = "/proc/%d/schedstat" % pid
                        file_sched = "/proc/%d/sched" % pid

                        with open(file_schedstat, "r") as fs:
                            time_spent_on_the_cpu, time_spent_waiting_on_a_runqueue, num_of_timeslices_run_on_this_cpu = fs.readline().strip().split(" ")
                            self.log.debug(time_spent_on_the_cpu)
                            self.log.debug(time_spent_waiting_on_a_runqueue)
                            self.log.debug(num_of_timeslices_run_on_this_cpu)
                            self.publish_gauge("%s.schedstat.%s.time_spent_on_the_cpu" % (procname, pid), Decimal(time_spent_on_the_cpu) )
                            self.publish_gauge("%s.schedstat.%s.time_spent_waiting_on_a_runqueue" % (procname, pid), Decimal(time_spent_waiting_on_a_runqueue) )
                            self.publish_gauge("%s.schedstat.%s.num_of_timeslices_run_on_this_cpu" % (procname, pid), Decimal(num_of_timeslices_run_on_this_cpu) )

                        fs.close()

                        self.log.debug(file_sched)
                        with open(file_sched, "r") as fsc:
                            try:
                                for line in islice(fsc, 2, None):
                                    k, v = line.split(":")

                                    metric = k.strip().replace("->", "_")
                                    value = Decimal(v.strip())*1000

                                    self.log.debug("%s = %s" % (metric, value))
                                    self.publish_gauge("%s.sched.%s.%s" % (procname, pid, metric), Decimal(value) )

                            except ValueError, InvalidOperation:
                                pass

                            except Exception as e:
                                self.log.exception("Error: %s" % e)

                        fsc.close()

                except CalledProcessError:
                    pass

                except Exception as e:
                    self.log.exception("Couldn't collect for procname: %s", e)
            

            return True


        except SIGALRMException as e:
            # sigalrm is raised if the collector takes too long
            raise e
        except Exception as e:
            self.log.exception("Couldn't collect: %s", e)
            return None


# from schedstat_lib import *

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

# c = SchedStatCollector()
# c.log = logger

# c.collect()
