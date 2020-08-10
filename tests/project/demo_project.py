from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref


ACCOUNT = "NTNX_LOCAL_AZ"
SUBNET = "vlan.0"
CLUSTER = "calmdev1"
USER = "sspuser1@systest.nutanix.com"


class TestProject(Project):
    """Test project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account(ACCOUNT),
            subnets=[Ref.Subnet(name=SUBNET, cluster=CLUSTER)],
        ),
    ]

    users = [
        Ref.User(name=USER),
    ]
