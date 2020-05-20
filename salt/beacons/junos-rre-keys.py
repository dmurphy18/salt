#
# Junos redundant routing engine beacon
#
# NOTE this beacon only works on the Juniper native minion
#
# Copies salt-minion keys to the backup RE when present
#
# Configure with
#
# beacon:
#   beacons:
#     junos-rre-keys:
#       - interval: 43200
#
# `interval` above is in seconds, 43200 is recommended (every 12 hours)

## DGM
import logging

__virtualname__ = 'junos-rre-keys'

## DGM
log = logging.getLogger(__name__)

def beacon(config):
    ret = []

    engine_status = __salt__['junos.routing_engine']()

    if not engine_status['success']:
        return []

    log.debug("DGM junos-rre-keys beacon engine_status {0}".format(engine_status))
    for e in engine_status['backup']:
        result = __salt__['junos.dir_copy']('/var/local/salt/etc', e)
        ret.append({'result': result, 'success': True})

    return ret
