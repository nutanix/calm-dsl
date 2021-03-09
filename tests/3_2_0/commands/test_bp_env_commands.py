import json
import pytest
import uuid
import time
import traceback
from distutils.version import LooseVersion as LV
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins.models.metadata_payload import reset_metadata_obj
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Version
from calm.dsl.cli.constants import APPLICATION

LOG = get_logging_handle(__name__)

DSL_BP_FILEPATH = "tests/3_2_0/blueprints/test_blueprint_having_ahv_helper/blueprint.py"
NON_BUSY_APP_STATES = [
    APPLICATION.STATES.STOPPED,
    APPLICATION.STATES.RUNNING,
    APPLICATION.STATES.ERROR,
]

# project constants
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]
ENV_NAME = PROJECT["ENVIRONMENTS"][0]["NAME"]

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.2.0"),
    reason="Tests are for env changes introduced in 3.2.0",
)
class TestBpCommands:
    def setup_method(self):
        """Method to instantiate to created_bp_list and reset context"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        self.created_bp_list = []
        self.created_app_list = []

    def _wait_for_non_busy_state(self, app_name):

        runner = CliRunner()
        non_busy_statuses = [
            "Status: {}".format(state) for state in NON_BUSY_APP_STATES
        ]
        result = runner.invoke(cli, ["describe", "app", app_name])
        while not any([state_str in result.output for state_str in non_busy_statuses]):
            time.sleep(5)
            result = runner.invoke(cli, ["describe", "app", app_name])

    def teardown_method(self):
        """Method to delete creates bps and apps during tests"""

        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        for app_name in self.created_app_list:
            LOG.info("Deleting App {}".format(app_name))
            self._wait_for_non_busy_state(app_name=app_name)
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "app", app_name])
            assert result.exit_code == 0

        self.created_bp_list = []
        self.created_app_list = []

        # Resetting metadata object
        reset_metadata_obj()

    def _create_bp(self):
        runner = CliRunner()
        created_dsl_bp_name = "Test_DSL_BP_{}".format(str(uuid.uuid4()))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(DSL_BP_FILEPATH),
                "--name={}".format(created_dsl_bp_name),
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

        self.created_bp_list.append(created_dsl_bp_name)
        return created_dsl_bp_name

    def test_bp_launch(self):
        """Tests launch flow of blueprint"""

        created_dsl_bp_name = self._create_bp()
        runner = CliRunner()
        self._create_bp()
        created_app_name = "TestAppLaunch_{}".format(created_dsl_bp_name)
        LOG.info("Launching Bp {}".format(created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                created_dsl_bp_name,
                "--app_name={}".format(created_app_name),
                "-i",
            ],
        )
        self.created_app_list.append(created_app_name)
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

    def test_bp_launch_using_env(self):
        """Tests launching of blueprint with environment as cli option"""

        created_dsl_bp_name = self._create_bp()
        runner = CliRunner()
        self._create_bp()
        created_app_name = "TestAppLaunch_{}".format(created_dsl_bp_name)
        LOG.info(
            "Launching Bp {} with environment {}".format(created_dsl_bp_name, ENV_NAME)
        )
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                created_dsl_bp_name,
                "--app_name={}".format(created_app_name),
                "-i",
                "-e",
                ENV_NAME,
            ],
        )
        self.created_app_list.append(created_app_name)
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
