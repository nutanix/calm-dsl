import pytest
import time
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.cli.constants import APPLICATION
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)
NON_BUSY_APP_STATES = [
    APPLICATION.STATES.STOPPED,
    APPLICATION.STATES.RUNNING,
    APPLICATION.STATES.ERROR,
]

DSL_BP_FILEPATH = "tests/blueprint_example/test_blueprint_example.py"
CUSTOM_ACTION_NAME = "sample_profile_action"


@pytest.mark.slow
class TestAppCommands:
    non_busy_statuses = ["Status: {}".format(state) for state in NON_BUSY_APP_STATES]

    def test_apps_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("BP Get failed")
        print(result.output)

    def test_apps_list_with_limit_offset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps", "--limit=15", "--offset=5"])
        assert result.exit_code == 0
        print(result.output)

    def test_apps_list_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "apps", "--name=MSSQL"])
        assert result.exit_code == 0
        print(result.output)

    def _create_bp(self):
        runner = CliRunner()
        self.created_dsl_bp_name = "Test_Existing_VM_DSL_{}".format(int(time.time()))
        LOG.info("Creating Bp {} ". format(self.created_dsl_bp_name))
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
        assert result.exit_code == 0
        LOG.info("Success")

    def test_app_create_describe_actions(self):
        runner = CliRunner()
        self._create_bp()
        self.created_app_name = "TestAppLaunch_{}".format(self.created_dsl_bp_name)
        LOG.info("Launching Bp {}". format(self.created_dsl_bp_name))
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
        assert result.exit_code == 0
        LOG.info("Success")

        self._test_describe_app()
        self._test_run_custom_action()
        self._test_dsl_bp_delete()
        self._test_app_delete()

    def _test_describe_app(self):
        runner = CliRunner()
        LOG.info("Running 'calm describe app' command")
        result = runner.invoke(cli, ["describe", "app", self.created_app_name])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Command output : {}". format(result.output))

    def _wait_for_non_busy_state(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", self.created_app_name])
        while not any(
            [state_str in result.output for state_str in self.non_busy_statuses]
        ):
            time.sleep(5)
            result = runner.invoke(cli, ["describe", "app", self.created_app_name])

    def _test_run_custom_action(self):
        runner = CliRunner()
        self._wait_for_non_busy_state()
        LOG.info("Running {} action on app {}". format(CUSTOM_ACTION_NAME, self.created_app_name))
        result = runner.invoke(
            cli,
            [
                "run",
                "action",
                CUSTOM_ACTION_NAME,
                "--app={}".format(self.created_app_name),
            ],
        )
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Command output : {}". format(result.output))

    def _test_app_delete(self):
        runner = CliRunner()
        self._wait_for_non_busy_state()
        LOG.info("Deleting App {} ". format(self.created_app_name))
        result = runner.invoke(cli, ["delete", "app", self.created_app_name])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response : {}". format(result.output))

    def _test_dsl_bp_delete(self):
        runner = CliRunner()
        LOG.info("Deleting Bp {} ". format(self.created_dsl_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_dsl_bp_name])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response : {}". format(result.output))


if __name__ == "__main__":
    tester = TestAppCommands()
    tester.test_app_create_describe_actions()
