import json
import pytest
import os

from calm.dsl.builtins import CalmRefType
from calm.dsl.builtins import read_file
from calm.dsl.log import get_logging_handle
from tests.mock.constants import MockConstants

LOG = get_logging_handle(__name__)

directory_parts = os.path.abspath(__file__).split(os.path.sep)
test_config_location = os.path.join(
    os.path.sep.join(directory_parts[:-3]),
    MockConstants.MOCK_LOCATION,
    MockConstants.TEST_CONFIG_FILE_NAME,
)

DSL_CONFIG = json.loads(read_file(test_config_location, 0))
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]
PROJECTS = DSL_CONFIG["PROJECTS"]
PROVIDERS = DSL_CONFIG["PROVIDERS"]
AHV_ACCOUNT_NAME = "NTNX_LOCAL_AZ"
AHV_ACCOUNT_UUID = DSL_CONFIG["METADATA"]["ACCOUNT"].get(AHV_ACCOUNT_NAME, None)
PROJECT_NAME = "default"
PROJECT_UUID = DSL_CONFIG["METADATA"]["PROJECT"].get(PROJECT_NAME, None)
PROVIDER_NAME = "AzureVault_Cred_Provider"
PROVIDER_UUID = DSL_CONFIG["METADATA"]["PROVIDER"].get(PROVIDER_NAME, None)

@pytest.mark.pre_commit
@pytest.mark.skipif(
    not AHV_ACCOUNT_UUID, reason="No {} account on the setup".format(AHV_ACCOUNT_NAME)
)
def test_decompile_subnet():

    subnets = ACCOUNTS.get(AHV_ACCOUNT_UUID, {}).get("AHV_SUBNET", [])
    if not subnets:
        LOG.warning("Subnet not found in {} account".format(AHV_ACCOUNT_NAME))
    else:
        cdict = {"kind": "subnet", "uuid": subnets[0]["UUID"]}
        cls = CalmRefType.decompile(cdict)
        assert cls.name == subnets[0]["NAME"]
        assert cls.cluster == subnets[0]["CLUSTER_NAME"]
        assert cls.account_uuid == AHV_ACCOUNT_UUID


@pytest.mark.pre_commit
@pytest.mark.skipif(
    not AHV_ACCOUNT_UUID, reason="No {} account on the setup".format(AHV_ACCOUNT_NAME)
)
def test_decompile_cluster():

    clusters = ACCOUNTS[AHV_ACCOUNT_UUID].get("AHV_CLUSTER", [])
    if not clusters:
        pytest.skip("No clusters found in {} account".format(AHV_ACCOUNT_NAME))
    else:
        cdict = {"kind": "cluster", "uuid": clusters[0]["UUID"]}
        cls = CalmRefType.decompile(cdict)
        assert cls.name == clusters[0]["NAME"]
        assert cls.account_name == AHV_ACCOUNT_NAME


@pytest.mark.pre_commit
@pytest.mark.skipif(
    not AHV_ACCOUNT_UUID, reason="No {} account on the setup".format(AHV_ACCOUNT_NAME)
)
def test_decompile_account():

    cdict = {"kind": "account", "uuid": AHV_ACCOUNT_UUID}
    cls = CalmRefType.decompile(cdict)
    assert cls.name == AHV_ACCOUNT_NAME


@pytest.mark.pre_commit
@pytest.mark.skipif(not PROJECT_UUID, reason="No default project on the setup")
def test_decompile_environment():

    envs = PROJECTS.get(PROJECT_UUID, {}).get("ENVIRONMENTS", [])
    if not envs:
        pytest.skip("No envs found in {} project".format(PROJECT_NAME))

    cdict = {
        "kind": "environment",
        "uuid": envs[0]["UUID"],
    }
    cls = CalmRefType.decompile(cdict)
    assert cls.name == envs[0]["NAME"]
    assert cls.project_name == PROJECT_NAME
    assert cls.compile() == {
        "kind": "environment",
        "uuid": envs[0]["UUID"],
        "name": envs[0]["NAME"],
    }


@pytest.mark.pre_commit
@pytest.mark.skipif(
    not PROVIDER_UUID, reason="No {} on the setup".format(PROVIDER_NAME)
)
def test_decompile_resource_type():

    resources = PROVIDERS.get(PROVIDER_UUID, {}).get("RESOURCE_TYPE", [])

    if not resources:
        pytest.skip("No resource found in provider {}".format(PROVIDER_NAME))
    else:
        cdict = {"kind": "resource_type", "uuid": resources[0]["UUID"]}
        cls = CalmRefType.decompile(cdict)

    assert cls.name == PROVIDER_NAME
