import pytest
import time
import json
import sys
import uuid
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from tests.utils import Application as ApplicationHelper

LOG = get_logging_handle(__name__)

DSL_BP_FILEPATH = "tests/blueprint_example/test_blueprint_example.py"
DSL_LAUNCH_PARAM_FILEPATH = (
    "tests/blueprint_example/test_blueprint_example_launch_params.py"
)
CUSTOM_ACTION_NAME = "sample_profile_action"


@pytest.mark.slow
class TestAppCommands:
    app_helper = ApplicationHelper()

    def test_apps_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps"])
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
            pytest.fail("BP Get failed")
        LOG.info("Success")

    def test_apps_list_with_limit_offset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps", "--limit=15", "--offset=5"])
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
        LOG.info("Success")

    def test_apps_list_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps", "--name=MSSQL"])
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
        LOG.info("Success")

    def _create_bp(self):
        runner = CliRunner()
        self.created_dsl_bp_name = "Test_Existing_VM_DSL_{}".format(int(time.time()))
        LOG.info("Creating Bp {} ".format(self.created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(DSL_BP_FILEPATH),
                "--name={}".format(self.created_dsl_bp_name),
                "--description='Test DSL Blueprint; to delete'",
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
        LOG.info("Success")

    def test_app_create_describe_actions(self):
        runner = CliRunner()
        self._create_bp()
        self.created_app_name = "TestAppLaunch_{}".format(self.created_dsl_bp_name)
        LOG.info("Launching Bp {}".format(self.created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                self.created_dsl_bp_name,
                "--app_name={}".format(self.created_app_name),
            ],
            input="\n".join(["1", "DEV"]),
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
        LOG.info("Success")

        self._test_describe_app()
        self._test_run_custom_action()
        self._test_dsl_bp_delete()
        self._test_app_delete()

    def test_app_create_noninteractive_input(self):
        runner = CliRunner()
        self._create_bp()
        self.created_app_name = "TestAppLaunch_{}".format(self.created_dsl_bp_name)
        LOG.info("Launching Bp {}".format(self.created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                self.created_dsl_bp_name,
                "--app_name={}".format(self.created_app_name),
                "--launch_params={}".format(DSL_LAUNCH_PARAM_FILEPATH),
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
        LOG.info("Success")

        self._test_describe_app()
        self._test_run_custom_action()
        self._test_restart_app()
        self._test_stop_app()
        self._test_start_app()
        self._test_dsl_bp_delete()
        self._test_app_delete()

    def _test_describe_app(self):
        runner = CliRunner()
        LOG.info("Running 'calm describe app' command")
        result = runner.invoke(cli, ["describe", "app", self.created_app_name])
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
        LOG.info("Success")

    def _test_run_custom_action(self):
        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(self.created_app_name)
        LOG.info(
            "Running {} action on app {}".format(
                CUSTOM_ACTION_NAME, self.created_app_name
            )
        )
        result = runner.invoke(
            cli,
            [
                "run",
                "action",
                CUSTOM_ACTION_NAME,
                "--app={}".format(self.created_app_name),
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
        LOG.info("Success")

    def _test_restart_app(self):

        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(self.created_app_name)
        LOG.info("Restarting app {}".format(self.created_app_name))
        result = runner.invoke(cli, ["restart", "app", self.created_app_name])
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
        LOG.info("Success")

    def _test_stop_app(self):

        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(self.created_app_name)
        LOG.info("Stopping app {}".format(self.created_app_name))
        result = runner.invoke(cli, ["stop", "app", self.created_app_name])
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
        LOG.info("Success")

    def _test_start_app(self):

        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(self.created_app_name)
        LOG.info("Starting app {}".format(self.created_app_name))
        result = runner.invoke(cli, ["start", "app", self.created_app_name])
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
        LOG.info("Success")

    def _test_app_delete(self):
        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(self.created_app_name)
        LOG.info("Deleting App {} ".format(self.created_app_name))
        result = runner.invoke(cli, ["delete", "app", self.created_app_name])
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
        LOG.info("Success")

    def _test_dsl_bp_delete(self):
        runner = CliRunner()
        LOG.info("Deleting Bp {} ".format(self.created_dsl_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_dsl_bp_name])
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
        LOG.info("Success")

    def test_app_create(self):
        runner = CliRunner()

        self.created_app_name = "Application{}".format(str(uuid.uuid4())[:10])
        LOG.info("Creating App '{}'".format(self.created_app_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "app",
                "--file={}".format(DSL_BP_FILEPATH),
                "--name={}".format(self.created_app_name),
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
        LOG.info("Success")
        self._test_app_delete()


if __name__ == "__main__":
    tester = TestAppCommands()
