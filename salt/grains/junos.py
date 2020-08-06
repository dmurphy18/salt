# -*- coding: utf-8 -*-
"""
Grains for junos.
NOTE this is a little complicated--junos can only be accessed
via salt-proxy-minion.Thus, some grains make sense to get them
from the minion (PYTHONPATH), but others don't (ip_interfaces)
"""

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

import logging

## DGM
import inspect


# Import Salt libs
from salt.ext import six

__proxyenabled__ = ["junos"]
__virtualname__ = "junos"

# Get looging started
log = logging.getLogger(__name__)


def __virtual__():
    if "proxy" not in __opts__:
        log.debug("DGM grains junos __virtual__ proxy not in  __opts__ ")
        return False
    else:
        log.debug("DGM grains junos __virtual__ proxy in  __opts__ WILL LOAD ")
        return __virtualname__


def _remove_complex_types(dictionary):
    """
    junos-eznc is now returning some complex types that
    are not serializable by msgpack.  Kill those.
    """
    for k, v in six.iteritems(dictionary):
        if isinstance(v, dict):
            dictionary[k] = _remove_complex_types(v)
        elif hasattr(v, "to_eng_string"):
            dictionary[k] = v.to_eng_string()

    return dictionary


def defaults():
    if os.path.exists("/var/db/scripts/jet"):
        return {
            "os": "junos",
            "kernel": "junos",
            "osrelease": "junos FIXME",
        }
    else:
        return {"os": "proxy", "kernel": "unknown", "osrelease": "proxy"}


def facts(proxy=None):
    log.debug("DGM grains junos facts proxy '{0}'".format(proxy))

    log.debug("DGM grains junos facts stackframe '{0}'".format(inspect.stack()))

##    if proxy is None:
##        log.debug("DGM grains junos facts proxy '{0}', returning __proxy_ junos get serialized facts".format(proxy))
##        return __proxy__["junos.get_serialized_facts"]()
    proxy_junos_initialized = False
    if proxy:
        proxy_junos_initialized = proxy["junos.initialized"]()

    log.debug("DGM grains junos facts proxy '{0}', junos initialized '{1}'"
            .format(proxy, proxy_junos_initialized))
    if proxy is None or proxy_junos_initialized is False:
       return {}

    log.debug("DGM grains junos facts proxy '{0}', returning junos_facts".format(proxy))
##    return {"junos_facts": proxy["junos.get_serialized_facts"]()}
    ret_value = proxy["junos.get_serialized_facts"]()
    if os.path.exists("/var/db/scripts/jet"):
        ret = {"junos_facts": ret_value, "osrelease": ret_value["version"]}
    else:
        ret = {"junos_facts": ret_value}
    log.debug("DGM grains junos facts proxy '{0}', returning junos_facts dict '{1}'".format(proxy, ret))

    return ret


def os_family():
    return {"os_family": "junos"}
