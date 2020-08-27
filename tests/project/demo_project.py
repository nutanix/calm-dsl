from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref


ACCOUNT = "NTNX_LOCAL_AZ"
SUBNET = "vlan.0"
CLUSTER = "calmdev1"
USER = "sspuser1@systest.nutanix.com"
GROUP = "cn=sspgroup1,ou=pc,dc=systest,dc=nutanix,dc=com"
VCPUS = 1
STORAGE = 2  # GiB
MEMORY = 1  # GiB


class TestDemoProject(Project):
    """Test project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account(ACCOUNT),
            subnets=[Ref.Subnet(name=SUBNET, cluster=CLUSTER)],
        )
    ]

    users = [Ref.User(name=USER)]

    groups = [Ref.Group(name=GROUP)]

    quotas = {"vcpus": VCPUS, "storage": STORAGE, "memory": MEMORY}
