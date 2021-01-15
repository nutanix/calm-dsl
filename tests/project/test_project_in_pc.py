from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref


class TestDslProject(Project):
    """Sample DSL Project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account("NTNX_LOCAL_AZ"))]

    users = [Ref.User(name="sspuser1@systest.nutanix.com")]

    groups = [Ref.Group(name="cn=sspgroup1,ou=pc,dc=systest,dc=nutanix,dc=com")]

    quotas = {"vcpus": 1, "storage": 2, "memory": 1}
