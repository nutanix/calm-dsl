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
DSL_PROJECT_WITH_ENV_PATH = "tests/project/test_project_with_env.py"


class TestProjectCommands:
    def test_projects_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "projects"])
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
            pytest.fail("Project Get failed")
        LOG.info("Success")

    def test_compile_project(self):
        runner = CliRunner()
        LOG.info("Compiling Project file at {}".format(DSL_PROJECT_PATH))
        result = runner.invoke(
            cli, ["compile", "project", "--file={}".format(DSL_PROJECT_PATH)]
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
            pytest.fail("Project compile command failed")
        LOG.info("Success")

    def test_project_crud(self):
        """
        It will cover create/describe/update/delete/get commands on project
        This test assumes users/groups mentioned in project file are already created
        """

        # Create operation
        self._test_project_create_using_dsl()

        # Read operations
        click.echo("")
        self._test_project_describe_out_json()
        click.echo("")
        self._test_project_describe_out_text()
        click.echo("")
        self._test_project_list_name_filter()

        # Update operations
        click.echo("")
        self._test_update_project_using_cli_switches()
        click.echo("")
        self._test_update_project_using_dsl_file()

        # Delete operations
        click.echo("")
        self._test_project_delete()

    def _test_project_create_using_dsl(self):

        runner = CliRunner()
        self.dsl_project_name = "Test_DSL_Project_{}".format(str(uuid.uuid4()))
        LOG.info("Testing 'calm create project' command")
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
        LOG.info("Success")

    def _test_project_describe_out_text(self):

        runner = CliRunner()
        LOG.info("Testing 'calm describe project --out text' command")
        result = runner.invoke(cli, ["describe", "project", self.dsl_project_name])
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
            pytest.fail("Project Get call failed")

        project_name_str = "Name: {}".format(self.dsl_project_name)
        assert project_name_str in result.output
        LOG.info("Success")

    def _test_project_describe_out_json(self):

        runner = CliRunner()
        LOG.info("Testing 'calm describe project --out json' command")
        result = runner.invoke(
            cli, ["describe", "project", self.dsl_project_name, "--out", "json"]
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
            pytest.fail("Project Get call failed")

        project_name_str = '"name": "{}"'.format(self.dsl_project_name)
        assert project_name_str in result.output
        LOG.info("Success")

    def _test_project_list_name_filter(self):

        runner = CliRunner()
        LOG.info("Testing 'calm get projects --name <project_name>' command")
        result = runner.invoke(
            cli, ["get", "projects", "--name", self.dsl_project_name]
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
            pytest.fail("Project list call failed")

        assert self.dsl_project_name in result.output
        LOG.info("Success")

    def _test_update_project_using_cli_switches(self):
        """
        Adds user `sspuser10@systest.nutanix.com` to given project.
        (User must be prsent in db)
        """

        runner = CliRunner()
        LOG.info("Testing 'calm update project' command using cli switches")
        result = runner.invoke(
            cli,
            [
                "update",
                "project",
                self.dsl_project_name,
                "--add_user",
                "sspuser10@systest.nutanix.com",
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
            pytest.fail("Project update call failed")
        LOG.info("Success")

    def _test_update_project_using_dsl_file(self):
        """
        Removes user `sspuser10@systest.nutanix.com` to given project.
        (User must be prsent in db)
        """

        runner = CliRunner()
        LOG.info("Testing 'calm update project' command using dsl file")
        result = runner.invoke(
            cli,
            [
                "update",
                "project",
                self.dsl_project_name,
                "--file={}".format(DSL_PROJECT_PATH),
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
            pytest.fail("Project update call failed")
        LOG.info("Success")

    def _test_project_delete(self):

        runner = CliRunner()
        LOG.info("Testing 'calm delete project' command")
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
        LOG.info("Success")

    def test_project_with_env_create_and_delete(self):
        """
        Describe and update flow are already checked in `test_project_crud`
        It will test only create and delete flow on projects with environment
        """

        runner = CliRunner()
        self.dsl_project_name = "Test_DSL_Project_Env{}".format(str(uuid.uuid4()))
        LOG.info("Testing 'calm create project' command")
        result = runner.invoke(
            cli,
            [
                "create",
                "project",
                "--file={}".format(DSL_PROJECT_WITH_ENV_PATH),
                "--name={}".format(self.dsl_project_name),
                "--description='Test DSL Project with Env to delete'",
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
        LOG.info("Success")

        self._test_project_delete()
