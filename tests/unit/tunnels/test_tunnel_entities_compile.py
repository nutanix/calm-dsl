import json
import pytest

from examples.Tunnel.runbook import TestRunbook as Runbook
from calm.dsl.constants import TUNNEL
from click.testing import CliRunner
from calm.dsl.cli import main as cli, compile_runbook_command as compile_runbook
from calm.dsl.store.version import Version
from distutils.version import LooseVersion as LV
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

RunbookFilePath = "examples/Tunnel/runbook.py"
CustomProviderFilePath = "examples/Tunnel/custom_provider.py"
AccountFilePath = "examples/Tunnel/account.py"
CredentialProviderFilePath = "examples/Tunnel/credential_provider.py"
EndpointFilePaths = [
    "examples/Tunnel/endpoints/http_ep.py",
    "examples/Tunnel/endpoints/linux_ep.py",
    "examples/Tunnel/endpoints/windows_ep.py",
]
ProjectPath = "examples/Tunnel/project.py"

TUNNEL_2 = "Tunnel_2"
TUNNEL_1 = "Tunnel_1"


@pytest.mark.skipif(
    LV(Version.get_version("Calm")) < LV(TUNNEL.FEATURE_MIN_VERSION),
    reason="Tunnel feature not available in this version",
)
@pytest.mark.tunnel
class TestEntityWithTunnelCompile:
    def test_compile_in_runbook_with_tunnels(self):
        """Checks if the compiled runbook payload contains apt tunnel entities."""

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "compile",
                "runbook",
                "--file={}".format(RunbookFilePath),
            ],
        )
        if result.exit_code != 0:
            LOG.error("Runbook compilation failed with error: {}".format(result.output))
            pytest.fail("Runbook compilation failed")

        runbook_json = None
        try:
            runbook_json = json.loads(result.output)
        except json.JSONDecodeError as e:
            LOG.error("Error decoding JSON output: {}".format(e))
            pytest.fail("Runbook compilation failed with invalid JSON output")

        task_list = runbook_json["spec"]["resources"]["runbook"]["task_definition_list"]
        variable_list = runbook_json["spec"]["resources"]["runbook"]["variable_list"]

        assert task_list[1]["type"] == "EXEC"
        assert task_list[1]["attrs"]["tunnel_reference"]["name"] == TUNNEL_2

        assert task_list[2]["type"] == "SET_VARIABLE"
        assert task_list[2]["attrs"]["tunnel_reference"]["name"] == TUNNEL_1

        assert task_list[7]["type"] == "DECISION"
        assert task_list[7]["attrs"]["tunnel_reference"]["name"] == TUNNEL_2

        assert variable_list[0]["options"]["type"] == "HTTP"
        assert variable_list[0]["options"]["attrs"]["method"] == "DELETE"
        assert (
            variable_list[0]["options"]["attrs"]["tunnel_reference"]["name"] == TUNNEL_1
        )

        assert variable_list[1]["options"]["type"] == "HTTP"
        assert variable_list[1]["options"]["attrs"]["method"] == "PUT"
        assert (
            variable_list[1]["options"]["attrs"]["tunnel_reference"]["name"] == TUNNEL_2
        )

        assert variable_list[2]["options"]["type"] == "HTTP"
        assert variable_list[2]["options"]["attrs"]["method"] == "POST"
        assert (
            variable_list[2]["options"]["attrs"]["tunnel_reference"]["name"] == TUNNEL_1
        )

        assert variable_list[3]["options"]["type"] == "HTTP"
        assert variable_list[3]["options"]["attrs"]["method"] == "GET"
        assert (
            variable_list[3]["options"]["attrs"]["tunnel_reference"]["name"] == TUNNEL_2
        )

        assert variable_list[4]["options"]["type"] == "EXEC"
        assert (
            variable_list[4]["options"]["attrs"]["tunnel_reference"]["name"] == TUNNEL_1
        )

        LOG.info("JSON compilation successful for Runbook.")

    def test_compile_in_custom_provider_with_tunnels(self):
        """Checks if the compiled custom provider payload contains apt tunnel entities."""

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "compile",
                "provider",
                "--file={}".format(CustomProviderFilePath),
            ],
        )
        if result.exit_code != 0:
            LOG.error(
                "Custom provider compilation failed with error: {}".format(
                    result.output
                )
            )
            pytest.fail("Custom provider compilation failed")

        provider_json = None
        try:
            provider_json = json.loads(result.output)
        except json.JSONDecodeError as e:
            LOG.error("Error decoding JSON output: {}".format(e))
            pytest.fail("Custom provider compilation failed with invalid JSON output")

        test_account = provider_json["spec"]["resources"]["test_account"]
        resource_type = provider_json["spec"]["resources"]["resource_type_list"][0]
        action_1 = resource_type["action_list"][0]["runbook"]
        action_2 = resource_type["action_list"][1]["runbook"]
        action_3 = resource_type["action_list"][2]["runbook"]
        action_4 = resource_type["action_list"][3]["runbook"]

        assert test_account["tunnel_reference"]["name"] == TUNNEL_1

        for i in range(1, 5):
            assert action_1["task_definition_list"][i]["type"] == "EXEC"
            assert (
                action_1["task_definition_list"][i]["attrs"]["tunnel_reference"]["name"]
                == TUNNEL_2
            )
            if i < 4:
                assert action_1["variable_list"][i - 1]["options"]["type"] == "EXEC"
                assert (
                    action_1["variable_list"][i - 1]["options"]["attrs"][
                        "tunnel_reference"
                    ]["name"]
                    == TUNNEL_2
                )

        for i in range(1, 5):
            assert action_2["task_definition_list"][i]["type"] == "SET_VARIABLE"
            assert (
                action_2["task_definition_list"][i]["attrs"]["tunnel_reference"]["name"]
                == TUNNEL_2
            )

        for i in range(1, 5):
            assert action_3["task_definition_list"][i * 5]["type"] == "DECISION"
            assert (
                action_3["task_definition_list"][i * 5]["attrs"]["tunnel_reference"][
                    "name"
                ]
                == TUNNEL_2
            )

        for i in range(1, 5):
            assert action_4["task_definition_list"][i]["type"] == "HTTP"
            assert (
                action_4["task_definition_list"][i]["attrs"]["tunnel_reference"]["name"]
                == TUNNEL_2
            )
            assert action_4["variable_list"][i - 1]["options"]["type"] == "HTTP"
            assert (
                action_4["variable_list"][i - 1]["options"]["attrs"][
                    "tunnel_reference"
                ]["name"]
                == TUNNEL_2
            )

        LOG.info("JSON compilation successful for Custom Provider.")

    def test_compile_in_account_with_tunnel(self):
        """Checks if the compiled account payload contains apt tunnel."""

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "compile",
                "account",
                "--file={}".format(AccountFilePath),
            ],
        )
        if result.exit_code != 0:
            LOG.error("Account compilation failed with error: {}".format(result.output))
            pytest.fail("Account compilation failed")

        account_json = None
        try:
            account_json = json.loads(result.output)
        except json.JSONDecodeError as e:
            LOG.error("Error decoding JSON output: {}".format(e))
            pytest.fail("Account compilation failed with invalid JSON output")

        assert account_json["spec"]["resources"]["tunnel_reference"]["name"] == TUNNEL_1
        LOG.info("JSON compilation successful for Account.")

    def test_compile_in_credential_provider_with_tunnel(self):
        """Checks if the compiled credential provider payload contains apt tunnel."""

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "compile",
                "account",
                "--file={}".format(CredentialProviderFilePath),
            ],
        )
        if result.exit_code != 0:
            LOG.error(
                "Credential provider compilation failed with error: {}".format(
                    result.output
                )
            )
            pytest.fail("Credential provider compilation failed")

        credential_provider_json = None
        try:
            credential_provider_json = json.loads(result.output)
        except json.JSONDecodeError as e:
            LOG.error("Error decoding JSON output: {}".format(e))
            pytest.fail(
                "Credential provider compilation failed with invalid JSON output"
            )

        assert (
            credential_provider_json["spec"]["resources"]["tunnel_reference"]["name"]
            == TUNNEL_1
        )
        LOG.info("JSON compilation successful for Credential Provider.")

    def test_compile_in_endpoint_with_tunnel(self):
        """Checks if the compiled endpoint payload contains apt tunnel."""

        runner = CliRunner()
        for file in EndpointFilePaths:
            result = runner.invoke(
                cli,
                [
                    "compile",
                    "endpoint",
                    "--file={}".format(file),
                ],
            )
            if result.exit_code != 0:
                LOG.error(
                    "Endpoint compilation failed with error: {} for file '{}'".format(
                        result.output, file
                    )
                )
                pytest.fail("Endpoint compilation failed for file '{}'".format(file))

            endpoint_json = None
            try:
                endpoint_json = json.loads(result.output)
            except json.JSONDecodeError as e:
                LOG.error(
                    "For file '{}', error decoding JSON output: {}".format(file, e)
                )
                pytest.fail(
                    "Endpoint compilation failed with invalid JSON output for file '{}'".format(
                        file
                    )
                )

            assert (
                endpoint_json["spec"]["resources"]["tunnel_reference"]["name"]
                == TUNNEL_1
            )
            LOG.info("JSON compilation successful for Endpoint.")

    def test_compile_in_project_with_tunnels(self):
        """Checks if the compiled project payload contains apt tunnel entities."""

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "compile",
                "project",
                "--file={}".format(ProjectPath),
            ],
        )
        if result.exit_code != 0:
            LOG.error("Project compilation failed with error: {}".format(result.output))
            pytest.fail("Project compilation failed")

        project_json = None
        try:
            project_json = json.loads(result.output)
        except json.JSONDecodeError as e:
            LOG.error("Error decoding JSON output: {}".format(e))
            pytest.fail("Project compilation failed with invalid JSON output")

        assert (
            project_json["spec"]["resources"]["tunnel_reference_list"][0]["name"]
            == TUNNEL_1
        )
        assert (
            project_json["spec"]["resources"]["tunnel_reference_list"][1]["name"]
            == TUNNEL_2
        )
        LOG.info("JSON compilation successful for Project.")
