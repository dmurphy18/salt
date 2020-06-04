# -*- coding: utf-8 -*-
"""
Module to interact find the routing engine on  Junos devices.

:maturity: new
:dependencies: junos-eznc, jxmlease

.. note::

    Those who wish to use junos-eznc (PyEZ) version >= 2.1.0, must
    use the latest salt code from github until the next release.

Refer to :mod:`junos <salt.proxy.junos>` for information on connecting to junos proxy.

"""
# /srv/salt/modules/simple_custom_em.py

# Import Python libraries
from __future__ import absolute_import, print_function, unicode_literals

import logging

# Juniper interface libraries
# https://github.com/Juniper/py-junos-eznc
try:
    # pylint: disable=W0611
    from jnpr.junos import Device
    from jnpr.junos.utils.config import Config
    from jnpr.junos.utils.sw import SW
    from jnpr.junos.utils.scp import SCP
    import jnpr.junos.utils
    import jnpr.junos.cfg
    import jxmlease
    from jnpr.junos.factory.optable import OpTable
    from jnpr.junos.factory.cfgtable import CfgTable
    import jnpr.junos.op as tables_dir
    from jnpr.junos.factory.factory_loader import FactoryLoader
    import yamlordereddictloader
    from jnpr.junos.exception import ConnectClosedError, LockError

    # pylint: enable=W0611
    HAS_JUNOS_ENG = True
except ImportError:
    HAS_JUNOS_ENG = False

# Set up logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = "simple_custom_em"

__proxyenabled__ = ["simple_custom_em"]


def __virtual__():
    """
    We need the Junos adapter libraries for this
    module to work.  We also need a proxymodule entry in __opts__
    in the opts dictionary
    """
    if HAS_JUNOS_ENG and "proxy" in __opts__:
        return __virtualname__
    else:
        return (
            False,
            "The simple_custom_em junos module could not be loaded: "
            "junos-eznc or jxmlease or yamlordereddictloader or "
            "proxy could not be loaded.",
        )


def find_mastership():
    """
    Returns master routing-engine number via device login
    :return: master routing-engine number 0|1
    """
    ret = {}
    log.debug("DGM find_mastership start")
    conn = __proxy__['junos.conn']()
    if not conn.connected:
        log.debug("DGM find_mastership obtaining connection")
        conn.open()
    else:
        log.debug("dgm find_mastership already connected")

    mastership_xml = conn.rpc.get_route_engine_information()
    log.debug("DGM find_mastership got mastership_xml")

    try:
        master_info = mastership_xml.xpath("/rpc-reply/route-engine-information/"
                                       "route-engine[mastership-state='master']/slot")[0].text
    except Exception as exc:  # pylint: disable=broad-except
        log.debug("DGM find_mastership Execution failed due to {0}".format(exc))
        ret["message"] = 'Execution failed due to "{0}"'.format(exc)
        ret["out"] = False
        return ret

    log.debug("DGM find_mastership got master_info {0}".format(master_info))
    ret["message"] = master_info
    ret["out"] = True
    return ret
