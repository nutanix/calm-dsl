import json

from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref
from calm.dsl.builtins.models.utils import read_local_file
from tests.utils import get_local_az_overlay_details_from_dsl_config

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

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
    quotas = {
        "vcpus": 1,
        "storage": 2,
        "memory": 1,
    }
