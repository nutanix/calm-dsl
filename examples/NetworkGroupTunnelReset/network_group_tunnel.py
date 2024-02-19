"""
Spec file to be used for resetting(recreating) the tunnel VM in given tunnel
Command: ` calm reset network-group-tunnel-vm -f <this file path> -n <tunnel name>`
"""

from calm.dsl.builtins import NetworkGroupTunnelVMSpec

class NewNetworkGroupTunnel2(NetworkGroupTunnelVMSpec):
    """Network group tunnel spec for reset"""
    cluster = "auto_cluster_prod_4f4d4cfae296"
    subnet = "test3"
    type = "AHV"
