import json
import pytest

from calm.dsl.builtins import CalmRefType
from calm.dsl.builtins import read_file
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


DSL_CONFIG = json.loads(read_file("~/calm-dsl/config_test.json", 0))
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]
PROJECTS = DSL_CONFIG["PROJECTS"]
AHV_ACCOUNT_NAME = "NTNX_LOCAL_AZ"
AHV_ACCOUNT_UUID = DSL_CONFIG["METADATA"]["ACCOUNT"].get(AHV_ACCOUNT_NAME, None)
DEFAULT_PROJECT_NAME = "default"
DEFAULT_PROJECT = DSL_CONFIG["METADATA"]["PROJECT"].get(DEFAULT_PROJECT_NAME, None)


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


@pytest.mark.skipif(not DEFAULT_PROJECT, reason="No default project on the setup")
def test_decompile_environment():

    envs = PROJECTS.get(DEFAULT_PROJECT, {}).get("ENVIRONMENTS", [])
    if not envs:
        pytest.skip("No envs found in {} project".format(DEFAULT_PROJECT_NAME))

    cdict = {
        "kind": "environment",
        "uuid": envs[0]["UUID"],
    }
    cls = CalmRefType.decompile(cdict)
    assert cls.name == envs[0]["NAME"]
    assert cls.project_name == DEFAULT_PROJECT_NAME
    assert cls.compile() == {
        "kind": "environment",
        "uuid": envs[0]["UUID"],
        "name": envs[0]["NAME"],
    }
