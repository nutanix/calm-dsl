# THIS FILE IS AUTOMATICALLY GENERATED.
# Disclaimer: Please test this file before using in production.
"""
Generated project DSL (.py)
Decompiles project's  providers, users and quotas if available.
"""
from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref


class test_dsl_decompile(Project):

    providers = [
        Provider.Vmware(
            account=Ref.Account("vmware_second"),
        ),
        Provider.Gcp(
            account=Ref.Account("GCP"),
        ),
        Provider.Ntnx(
            account=Ref.Account("NTNX_LOCAL_AZ"),
            subnets=[
                Ref.Subnet(
                    name="vlan.154",
                    cluster="auto_cluster_prod_4faf4699cdea",
                )
            ],
        ),
        Provider.Aws(
            account=Ref.Account("primary"),
        ),
    ]

    users = [
        Ref.User(name="local_ad_user_admin@adfs19.com"),
    ]

    quotas = {"vcpus": 5, "storage": 5, "memory": 5}
