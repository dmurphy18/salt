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

## DGM __virtualname__ = 'junos-rre-keys'
def __virtual__():
    '''
    Returning False to disable as part of memory leak test
    '''
    return (False, 'DGM Disabled to allow for memory leak test')


def beacon(config):
    ret = []

    engine_status = __salt__['junos.routing_engine']()

    if not engine_status['success']:
        return []

    for e in engine_status['backup']:
        result = __salt__['junos.dir_copy']('/var/local/salt/etc', e)
        ret.append({'result': result, 'success': True})

    return ret
