import os
import warnings

from calm.dsl.builtins.server_interface import get_blueprint_api_handle


def get_api_client(**kwargs):
    """Convenience wrapper over get_blueprint_api_handle"""

    pc_ip = kwargs.get('pc_ip')
    pc_port = kwargs.get('pc_port')
    auth = kwargs.get('auth')

    return get_blueprint_api_handle(pc_ip, pc_port, auth=auth)


def ping(ip):

    # check if ip is reachable
    ecode = os.system("ping -c 1 " + ip)
    if ecode != 0:
        warnings.warn(
            UserWarning("Cannot reach PC server at {}".format(ip)))
        return False
    return True
