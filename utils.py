import os
import warnings

from calm.dsl.builtins.server_interface import get_blueprint_api_handle

PC_IP = "10.51.152.102"


def get_api_client(pc_ip=PC_IP, pc_port=9440,
                   auth=("admin", "***REMOVED***")):
    """using calm dsl PC as default. TODO - remove pc ip n auth"""

    return get_blueprint_api_handle(pc_ip, pc_port, auth=auth)


def ping(ip=PC_IP):

    # check if ip is reachable
    ecode = os.system("ping -c 1 " + ip)
    if ecode != 0:
        warnings.warn(
            UserWarning("Cannot reach PC server at {}".format(ip)))
        return False
    return True
