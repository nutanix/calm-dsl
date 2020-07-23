from calm.dsl.builtins import AhvProject
from calm.dsl.builtins import Provider, Ref


class TestDslProject(AhvProject):
    """Sample DSL Project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account("NTNX_LOCAL_AZ"),
            subnets=[Ref.Subnet(name="vlan.0", cluster="calmdev1")],
        )
    ]

    users = [
        Ref.User(name="sspuser1@systest.nutanix.com"),
    ]
