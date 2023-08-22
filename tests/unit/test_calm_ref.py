import json
import pytest

from calm.dsl.builtins import CalmRefType
from calm.dsl.builtins import read_local_file
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
AHV_ACCOUNTS = DSL_CONFIG["ACCOUNTS"]["NUTANIX_PC"]
DEFAULT_PROJECT = DSL_CONFIG["PROJECTS"].get("PROJECT1", {})


@pytest.mark.skipif(len(AHV_ACCOUNTS) == 0, reason="No Ahv account on the setup")
def test_decompile_subnet():

    subnets = AHV_ACCOUNTS[0].get("SUBNETS", [])
    if not subnets:
        LOG.warning("Subnet not found")
    else:
        cdict = {"kind": "subnet", "uuid": subnets[0]["UUID"]}
        cls = CalmRefType.decompile(cdict)
        assert cls.name == subnets[0]["NAME"]
        assert cls.cluster == subnets[0]["CLUSTER"]
        assert cls.account_uuid == AHV_ACCOUNTS[0]["UUID"]


@pytest.mark.skipif(len(AHV_ACCOUNTS) == 0, reason="No Ahv account on the setup")
def test_decompile_cluster():

    subnets = AHV_ACCOUNTS[0].get("SUBNETS", [])
    if not subnets:
        pytest.skip("No subnets found in {} account".format(AHV_ACCOUNTS[0]["NAME"]))
    else:
        cdict = {"kind": "cluster", "uuid": subnets[0]["CLUSTER_UUID"]}
        cls = CalmRefType.decompile(cdict)
        assert cls.name == subnets[0]["CLUSTER"]
        assert cls.account_name == AHV_ACCOUNTS[0]["NAME"]


@pytest.mark.skipif(len(AHV_ACCOUNTS) == 0, reason="No Ahv account on the setup")
def test_decompile_account():

    cdict = {"kind": "account", "uuid": AHV_ACCOUNTS[0]["UUID"]}
    cls = CalmRefType.decompile(cdict)
    assert cls.name == AHV_ACCOUNTS[0]["NAME"]


@pytest.mark.skipif(not DEFAULT_PROJECT, reason="No Ahv account on the setup")
def test_decompile_environment():

    envs = DEFAULT_PROJECT.get("ENVIRONMENTS", [])
    if not envs:
        pytest.skip("No envs found in {} project".format(DEFAULT_PROJECT["NAME"]))

    cdict = {
        "kind": "environment",
        "uuid": envs[0]["UUID"],
    }
    cls = CalmRefType.decompile(cdict)
    assert cls.name == envs[0]["NAME"]
    assert cls.project_name == DEFAULT_PROJECT["NAME"]
    assert cls.compile() == {
        "kind": "environment",
        "uuid": envs[0]["UUID"],
        "name": envs[0]["NAME"],
    }
