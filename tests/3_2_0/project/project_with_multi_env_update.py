# Note: In given example, we not added environment reference anywhere.
# Project create command will pick one Environment module from file and attaches to project

import json

from calm.dsl.builtins import Project, read_local_file
from calm.dsl.builtins import Provider, Ref


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
SQL_SERVER_IMAGE = DSL_CONFIG["AHV"]["IMAGES"]["CD_ROM"]["SQL_SERVER_2014_x64"]

# Accounts
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]

NTNX_ACCOUNT_1 = ACCOUNTS["NUTANIX_PC"][0]
NTNX_ACCOUNT_1_NAME = NTNX_ACCOUNT_1["NAME"]
NTNX_ACCOUNT_1_SUBNET_1 = NTNX_ACCOUNT_1["SUBNETS"][0]["NAME"]
NTNX_ACCOUNT_1_SUBNET_1_CLUSTER = NTNX_ACCOUNT_1["SUBNETS"][0]["CLUSTER"]
NTNX_ACCOUNT_1_SUBNET_2 = NTNX_ACCOUNT_1["SUBNETS"][1]["NAME"]
NTNX_ACCOUNT_1_SUBNET_2_CLUSTER = NTNX_ACCOUNT_1["SUBNETS"][1]["CLUSTER"]

AWS_ACCOUNT = ACCOUNTS["AWS"][0]
AWS_ACCOUNT_NAME = AWS_ACCOUNT["NAME"]

AZURE_ACCOUNT = ACCOUNTS["AZURE"][0]
AZURE_ACCOUNT_NAME = AZURE_ACCOUNT["NAME"]

GCP_ACCOUNT = ACCOUNTS["GCP"][0]
GCP_ACCOUNT_NAME = GCP_ACCOUNT["NAME"]

VMWARE_ACCOUNT = ACCOUNTS["VMWARE"][0]
VMWARE_ACCOUNT_NAME = VMWARE_ACCOUNT["NAME"]

K8S_ACCOUNT = ACCOUNTS["K8S"][0]
K8S_ACCOUNT_NAME = K8S_ACCOUNT["NAME"]

USER = DSL_CONFIG["USERS"][0]
USER_NAME = USER["NAME"]


class SampleDslProject(Project):
    """Sample DSL Project with environments"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_1_NAME),
            subnets=[
                Ref.Subnet(
                    name=NTNX_ACCOUNT_1_SUBNET_2,
                    cluster=NTNX_ACCOUNT_1_SUBNET_2_CLUSTER,
                ),
                Ref.Subnet(
                    name=NTNX_ACCOUNT_1_SUBNET_1,
                    cluster=NTNX_ACCOUNT_1_SUBNET_1_CLUSTER,
                ),
            ],
        ),
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
        Provider.Vmware(account=Ref.Account(VMWARE_ACCOUNT_NAME)),
        Provider.K8s(account=Ref.Account(K8S_ACCOUNT_NAME)),
        Provider.Aws(account=Ref.Account(AWS_ACCOUNT_NAME)),
        Provider.Azure(account=Ref.Account(AZURE_ACCOUNT_NAME)),
    ]

    users = [Ref.User(USER_NAME)]

    quotas = {
        "vcpus": 1,
        "storage": 2,
        "memory": 1,
    }
