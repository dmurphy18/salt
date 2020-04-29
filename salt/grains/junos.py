# -*- coding: utf-8 -*-
'''
Grains for junos.
'''

# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import logging

# Import Salt libs
from salt.ext import six

__virtualname__ = 'junos'

# Get looging started
log = logging.getLogger(__name__)


def __virtual__():
    if 'proxy' not in __opts__:
        return False
    else:
        return __virtualname__


def _remove_complex_types(dictionary):
    '''
    junos-eznc is now returning some complex types that
    are not serializable by msgpack.  Kill those.
    '''
    for k, v in six.iteritems(dictionary):
        if isinstance(v, dict):
            dictionary[k] = _remove_complex_types(v)
        elif hasattr(v, 'to_eng_string'):
            dictionary[k] = v.to_eng_string()

    return dictionary


def defaults():
    return {'os': 'junos FIXME', 'kernel': 'junos FIXME', 'osrelease': 'junos FIXME', 'kernel':'junos FIXME'}


def facts(proxy=None):
    if proxy is None:
        return __proxy__['junos.get_serialized_facts']()
    return {'junos_facts': proxy['junos.get_serialized_facts']()}


def os_family():
    return {'os_family': 'junos'}
