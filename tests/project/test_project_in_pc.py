from calm.dsl.builtins import AhvProject
from calm.dsl.builtins import Provider


class TestDslProject(AhvProject):
    """Sample DSL Project"""

    provider_list = [
        Provider.Ntnx(
            name="NTNX_LOCAL_AZ",
            subnets=[{"name": "vlan.0", "cluster": "calmdev1"}],
            default_subnet=1,
        ),
        Provider.Aws(name="AWS account"),
        Provider.Azure(name="AZURE_account"),
        Provider.Gcp(name="GCP Account"),
        Provider.Vmware(name="VMWARE account"),
        Provider.K8s(name="K8S_account_basic_auth"),
    ]
