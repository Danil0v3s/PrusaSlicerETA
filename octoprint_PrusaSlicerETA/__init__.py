# coding=utf-8
from __future__ import absolute_import, unicode_literals
import octoprint.plugin
import re
import time
from octoprint.printer.estimation import PrintTimeEstimator
from octoprint.events import eventManager, Events
from datetime import timedelta

eta = 0
oldZ = 0.0

ts = int(time.time())
# estimated printing time (normal mode) = 1d 18h 5m 28s
r = re.compile(
    r'(?<=estimated printing time \(normal mode\) = ).*')
p = re.compile(
    r'^X:\d+\.\d+ Y:\d+\.\d+ Z:(\d+\.\d+) ')

UNITS = {'s':'seconds', 'm':'minutes', 'h':'hours', 'd':'days', 'w':'weeks'}

def convert_to_seconds(s):
    return int(timedelta(**{
        UNITS.get(m.group('unit').lower(), 'seconds'): float(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds())

def pETAeveryLine(comm, line, *args, **kwargs):
    global eta, r, ts, oldZ
    m = r.search(line)
    if m:
        eta = int(convert_to_seconds(m.group(0)))
        ts = int(time.time())
        # comm._sendCommand("M114")
    z = p.search(line)
    if z:
        newZ = float(z.group(1))
        if newZ != oldZ:
            eventManager().fire(Events.Z_CHANGE, {"new": newZ, "old": oldZ})
            oldZ = newZ
    return line

class PrusasliceretaPlugin(octoprint.plugin.OctoPrintPlugin):
    def get_update_information(self):
        return {
            "PrusaSlicerETA": {
                "displayName": "Prusaslicereta Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "danil0v3s",
                "repo": "PrusaSlicerETA",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/danil0v3s/PrusaSlicerETA/archive/{target_version}.zip",
            }
        }

class pETAPrintTimeEstimator(PrintTimeEstimator):
    
    def __init__(self, job_type):
        super(pETAPrintTimeEstimator, self).__init__(job_type)

    def estimate(self, progress, printTime, cleanedPrintTime, statisticalTotalPrintTime, statisticalTotalPrintTimeType):
        print("### " + eta + " >>> " + eta - (int(time.time()) - ts))
        return eta - (int(time.time()) - ts), "estimate"


def pETAfactory(*args, **kwargs):
    return pETAPrintTimeEstimator

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "PrusaSlicerETA Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrusasliceretaPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.received": pETAeveryLine,
        "octoprint.printer.estimation.factory": pETAfactory
    }
