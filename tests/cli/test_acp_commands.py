import pytest
import json
import uuid
import click
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_PROJECT_PATH = "tests/project/test_project_in_pc.py"


class TestACPCommands:
    def setup_method(self):
        runner = CliRunner()
        self.dsl_project_name = "Test_DSL_Project_{}".format(str(uuid.uuid4()))
        result = runner.invoke(
            cli,
            [
                "create",
                "project",
                "--file={}".format(DSL_PROJECT_PATH),
                "--name={}".format(self.dsl_project_name),
                "--description='Test DSL Project to delete'",
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Project creation from python file failed")

    def teardown_method(self):

        runner = CliRunner()
        result = runner.invoke(cli, ["delete", "project", self.dsl_project_name])
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("Project delete call failed")

    def test_acp_crud(self):
        """
        It will cover create/describe/update/delete/get commands on project acps
        This test assumes users/groups mentioned in project file are already created
        """

        # Create ACP operation
        self._test_acp_create()

        # Read operations
        click.echo("")
        self._test_acp_describe_out_json()
        click.echo("")
        self._test_acp_describe_out_text()
        click.echo("")
        self._test_acp_get_command()

        # Update operations
        click.echo("")
        self._test_update_acp_using_cli_switches()

        # Delete operations
        click.echo("")
        self._test_acp_delete()

    def _test_acp_create(self):

        runner = CliRunner()
        acp_role = "Developer"
        self.dsl_acp_name = "Test_ACP_{}".format(str(uuid.uuid4()))

        LOG.info("Testing 'calm create acp' command")
        result = runner.invoke(
            cli,
            [
                "create",
                "acp",
                "--role={}".format(acp_role),
                "--project={}".format(self.dsl_project_name),
                "--name={}".format(self.dsl_acp_name),
                "--user={}".format("sspuser1@systest.nutanix.com"),
                "--group={}".format("cn=sspgroup1,ou=pc,dc=systest,dc=nutanix,dc=com"),
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("ACP creation failed")
        LOG.info("Success")

    def _test_acp_describe_out_text(self):

        runner = CliRunner()
        LOG.info("Testing 'calm describe acp --out text' command")
        result = runner.invoke(
            cli,
            [
                "describe",
                "acp",
                self.dsl_acp_name,
                "--project={}".format(self.dsl_project_name),
            ],
        )

        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("ACP Describe command failed")

        acp_name_str = "Name: {}".format(self.dsl_acp_name)
        assert acp_name_str in result.output
        LOG.info("Success")

    def _test_acp_describe_out_json(self):

        runner = CliRunner()
        LOG.info("Testing 'calm describe acp --out json' command")
        result = runner.invoke(
            cli,
            [
                "describe",
                "acp",
                self.dsl_acp_name,
                "--project={}".format(self.dsl_project_name),
                "--out=json",
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("ACP Describe command failed")

        acp_name_str = '"name": "{}"'.format(self.dsl_acp_name)
        assert acp_name_str in result.output
        LOG.info("Success")

    def _test_acp_get_command(self):

        runner = CliRunner()
        LOG.info("Testing 'calm get acps' command")
        result = runner.invoke(
            cli, ["get", "acps", "--project={}".format(self.dsl_project_name)]
        )

        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("ACPs Get command failed")

        assert self.dsl_acp_name in result.output
        LOG.info("Success")

    def _test_update_acp_using_cli_switches(self):
        """
        Removes user `sspuser1@systest.nutanix.com` from created acp.
        """

        runner = CliRunner()
        LOG.info("Testing 'calm update project' command using cli switches")
        result = runner.invoke(
            cli,
            [
                "update",
                "acp",
                self.dsl_acp_name,
                "--project={}".format(self.dsl_project_name),
                "--remove_user={}".format("sspuser1@systest.nutanix.com"),
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("ACP update call failed")
        LOG.info("Success")

    def _test_acp_delete(self):

        runner = CliRunner()
        LOG.info("Testing 'calm delete acp' command")
        result = runner.invoke(
            cli,
            [
                "delete",
                "acp",
                self.dsl_acp_name,
                "--project={}".format(self.dsl_project_name),
            ],
        )
        if result.exit_code:
            cli_res_dict = {"Output": result.output, "Exception": str(result.exception)}
            LOG.debug(
                "Cli Response: {}".format(
                    json.dumps(cli_res_dict, indent=4, separators=(",", ": "))
                )
            )
            LOG.debug(
                "Traceback: \n{}".format(
                    "".join(traceback.format_tb(result.exc_info[2]))
                )
            )
            pytest.fail("ACP delete call failed")
        LOG.info("Success")
