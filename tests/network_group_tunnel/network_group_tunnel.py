import json

from calm.dsl.builtins import NetworkGroupTunnel
from calm.dsl.builtins import Provider, Ref
from calm.dsl.builtins.models.network_group_tunnel_vm_spec import (
    ahv_network_group_tunnel_vm_spec,
)
from calm.dsl.builtins.models.utils import read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


def get_local_az_overlay_without_tunnel_details_from_dsl_config(config):
    networks = config["ACCOUNTS"]["NUTANIX_PC"]
    local_az_account = None
    for account in networks:
        if account.get("NAME") == "NTNX_LOCAL_AZ":
            local_az_account = account
            break
    overlay_subnets_list = local_az_account.get("OVERLAY_SUBNETS", [])
    vlan_subnets_list = local_az_account.get("SUBNETS", [])

    cluster = ""
    vpc = ""
    overlay_subnet = ""
    vpc_tunnels = config.get("VPC_TUNNELS", {})

    def tunnel_does_not_exist(vpc_tunnels, account, vpc):
        if vpc_tunnels.get(account, {}).get(vpc):
            return False
        return True

    for subnet in overlay_subnets_list:
        if tunnel_does_not_exist(vpc_tunnels, "NTNX_LOCAL_AZ", subnet["VPC"]):
            overlay_subnet = subnet["NAME"]
            vpc = subnet["VPC"]
            break

    for subnet in vlan_subnets_list:
        if subnet["NAME"] == config["AHV"]["NETWORK"]["VLAN1211"]:
            cluster = subnet["CLUSTER"]
            break
    print("Overlay Subnet:" + overlay_subnet)
    print("VPC: " + vpc)
    print("Cluster:" + cluster)
    return overlay_subnet, vpc, cluster


VLAN_NETWORK = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]
NETWORK1, VPC1, CLUSTER1 = get_local_az_overlay_without_tunnel_details_from_dsl_config(
    DSL_CONFIG
)


class NewNetworkGroupTunnelWithoutTunnel(NetworkGroupTunnel):
    """Network group tunnel for test"""

    account = Ref.Account("NTNX_LOCAL_AZ")
    platform_vpcs = [
        Ref.Vpc(VPC1, account_name="NTNX_LOCAL_AZ")
    ]  # Resolve account name from parent.
    tunnel_vm_spec = ahv_network_group_tunnel_vm_spec(CLUSTER1, NETWORK1)
