import os
import pytest
import json

from calm.dsl.constants import TUNNEL
from calm.dsl.builtins.models.project import ProjectType
from calm.dsl.builtins.models.cloud_provider import CloudProviderType
from calm.dsl.builtins.models.runbook import RunbookType
from calm.dsl.store.version import Version
from distutils.version import LooseVersion as LV

TUNNEL_1 = "Tunnel_1"
TUNNEL_2 = "Tunnel_2"


@pytest.mark.skipif(
    LV(Version.get_version("Calm")) < LV(TUNNEL.FEATURE_MIN_VERSION),
    reason="Tunnel feature not available in this version",
)
@pytest.mark.tunnel
class TestEntityWithTunnelDecompile:
    def test_decompile_in_project_with_tunnels(self):
        file_path = os.path.join("tests/unit/jsons/project.json")
        project_dict = json.loads(open(file_path).read())

        project_dict["status"]["resources"]["user_reference_list"] = []
        project_dict["status"]["resources"]["default_subnet_reference"] = []
        project_dict["status"]["resources"]["subnet_reference_list"] = []
        project_dict["status"]["resources"]["account_reference_list"] = []

        cls = ProjectType.decompile(project_dict)

        assert cls.tunnel_references[0]["name"] == TUNNEL_1
        assert cls.tunnel_references[1]["name"] == TUNNEL_2

    def test_decompile_in_custom_provider_with_tunnels(self):
        file_path = os.path.join("tests/unit/jsons/custom_provider.json")
        cp_dict = json.loads(open(file_path).read())

        cls = CloudProviderType.decompile(cp_dict["status"]["resources"])
        action_1 = cls.resource_types[0].actions[0]
        action_2 = cls.resource_types[0].actions[1]
        action_3 = cls.resource_types[0].actions[2]
        action_4 = cls.resource_types[0].actions[3]
        test_account = cls.test_account

        for task in action_1.runbook.tasks:
            if task.type == "DAG":
                continue
            assert task.type == "EXEC"
            assert task.attrs.get("tunnel_reference") is not None
            assert task.attrs["tunnel_reference"]["name"] == TUNNEL_2

        for variable in action_1.runbook.variables:
            assert variable.options.get("type", None) == "EXEC"
            assert variable.options["attrs"].get("tunnel_reference") is not None
            assert variable.options["attrs"]["tunnel_reference"]["name"] == TUNNEL_2

        for task in action_2.runbook.tasks:
            if task.type == "DAG":
                continue
            assert task.type == "SET_VARIABLE"
            assert task.attrs.get("tunnel_reference") is not None
            assert task.attrs["tunnel_reference"]["name"] == TUNNEL_2

        for task in action_3.runbook.variables:
            if task.type == "DAG" or task.type == "EXEC" or task.type == "META":
                continue
            assert task.type == "DECISION"
            assert task.attrs.get("tunnel_reference") is not None
            assert task.attrs["tunnel_reference"]["name"] == TUNNEL_2

        for task in action_4.runbook.tasks:
            if task.type == "DAG":
                continue
            assert task.type == "HTTP"
            assert task.attrs.get("tunnel_reference") is not None
            assert task.attrs["tunnel_reference"]["name"] == TUNNEL_2

        for variable in action_4.runbook.variables:
            assert variable.options.get("type", None) == "HTTP"
            assert variable.options["attrs"].get("tunnel_reference") is not None
            assert variable.options["attrs"]["tunnel_reference"]["name"] == TUNNEL_2

        assert test_account.tunnel.name == TUNNEL_1

    def test_decompile_in_runbook_with_tunnels(self):
        file_path = os.path.join("tests/unit/jsons/runbook.json")
        runbook_dict = json.loads(open(file_path).read())

        cls = RunbookType.decompile(runbook_dict["status"]["resources"]["runbook"])

        for task in cls.tasks:
            if task.type == "DAG" or task.type == "META":
                continue
            assert task.attrs.get("tunnel_reference") is not None
            assert task.attrs["tunnel_reference"]["name"] == TUNNEL_1

        for variable in cls.variables:
            assert variable.options["attrs"].get("tunnel_reference") is not None
            assert variable.options["attrs"]["tunnel_reference"]["name"] == TUNNEL_1
