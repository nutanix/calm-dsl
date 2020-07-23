from calm.dsl.builtins import AhvProject
from calm.dsl.builtins import Provider, Ref


ACCOUNT = "NTNX_LOCAL_AZ"
SUBNET = "vlan.0"
CLUSTER = "calmdev1"
USER = "sspuser1@systest.nutanix.com"


class TestProject(AhvProject):
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
