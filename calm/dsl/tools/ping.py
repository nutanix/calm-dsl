import os
import warnings


def ping(ip):

    # check if ip is reachable
    ecode = os.system("ping -c 1 " + ip)
    if ecode != 0:
        warnings.warn(UserWarning("Cannot reach PC server at {}".format(ip)))
        return False
    return True
