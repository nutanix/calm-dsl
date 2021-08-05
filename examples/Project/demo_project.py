from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref


NTNX_ACCOUNT_NAME = "NTNX_LOCAL_AZ"
NTNX_SUBNET = "vlan.0"
NTNX_SUBNET_CLUSTER = "calmdev1"
AWS_ACCOUNT_NAME = "aws_account"
AZURE_ACCOUNT_NAME = "azure_account"
GCP_ACCOUNT_NAME = "gcp_account"
VMWARE_ACCOUNT_NAME = "vmware_account"
K8S_ACCOUNT_NAME = "k8s_account"
USER = "sspuser1@systest.nutanix.com"
VCPUS = 1
STORAGE = 2  # GiB
MEMORY = 1  # GiB


class TestDslDemoProject(Project):
    """Sample DSL Project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_NAME),
            subnets=[Ref.Subnet(name=NTNX_SUBNET, cluster=NTNX_SUBNET_CLUSTER)],
        ),
        Provider.Aws(account=Ref.Account(AWS_ACCOUNT_NAME)),
        Provider.Azure(account=Ref.Account(AZURE_ACCOUNT_NAME)),
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
        Provider.Vmware(account=Ref.Account(VMWARE_ACCOUNT_NAME)),
        Provider.K8s(account=Ref.Account(K8S_ACCOUNT_NAME)),
    ]

    users = [Ref.User(name=USER)]

    quotas = {"vcpus": VCPUS, "storage": STORAGE, "memory": MEMORY}
