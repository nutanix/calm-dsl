import json

from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref
from calm.dsl.builtins.models.utils import read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))


def get_local_az_overlay_details_from_dsl_config(config):
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

    for subnet in overlay_subnets_list:
        if subnet["NAME"] == "vpc_subnet_1" and subnet["VPC"] == "vpc_name_1":
            overlay_subnet = subnet["NAME"]
            vpc = subnet["VPC"]

    for subnet in vlan_subnets_list:
        if subnet["NAME"] == config["AHV"]["NETWORK"]["VLAN1211"]:
            cluster = subnet["CLUSTER"]
            break
    return overlay_subnet, vpc, cluster


VLAN_NETWORK = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]
NETWORK1, VPC1, CLUSTER1 = get_local_az_overlay_details_from_dsl_config(DSL_CONFIG)


class TestDslWithOverlaySubnetProject(Project):
    """Sample DSL Project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account("NTNX_LOCAL_AZ"),
            subnets=[
                Ref.Subnet(name=VLAN_NETWORK, cluster=CLUSTER1),
                Ref.Subnet(name=NETWORK1, vpc=VPC1),
            ],
            clusters=[Ref.Cluster(name=CLUSTER1, account_name="NTNX_LOCAL_AZ")],
            vpcs=[Ref.Vpc(name=VPC1, account_name="NTNX_LOCAL_AZ")],
        ),
    ]
