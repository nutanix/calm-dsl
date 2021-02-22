import pytest
import json
import uuid
import time
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins.models.metadata_payload import reset_metadata_obj
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
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
BP_LAUNCH_PROFILE_NAME = "AhvVmProfile"


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

        # Resetting metadata context
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

    def test_mpi_launch_flow(self):

        created_dsl_bp_name = self._create_bp()
        self.marketplace_bp_name = "Test_Marketplace_Bp_{}".format(
            str(uuid.uuid4())[-10:]
        )
        self.mpi1_version = "1.0.0"
        self.mpi2_version = "2.0.0"
        self.mpi3_with_secrets_version = "3.0.0"

        # Publish Bp to marketplace manager as new marketplace blueprint
        LOG.info(
            "Publishing Bp {} as new marketplace blueprint {}".format(
                created_dsl_bp_name, self.marketplace_bp_name
            )
        )
        command = [
            "publish",
            "bp",
            created_dsl_bp_name,
            "--version",
            self.mpi1_version,
            "--name",
            self.marketplace_bp_name,
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of blueprint as new marketplace item failed")
        LOG.info("Success")

        # Launch the bp in PENDING state
        self.pending_mpbp_app_name = "Test_MPI_APP_{}".format(str(uuid.uuid4())[-10:])
        LOG.info(
            "Launch Bp {} with version {} in PENDING state using env-configuration".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "launch",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            PROJECT_NAME,
            "--app_name",
            self.pending_mpbp_app_name,
            "--profile_name",
            BP_LAUNCH_PROFILE_NAME,
            "-i",
            "-e",
            ENV_NAME,
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Launching of marketplace blueprint in PENDING state failed")
        self.created_app_list.append(self.pending_mpbp_app_name)

        # Approve the blueprint
        LOG.info(
            "Approving marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "approve",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Approving of marketplace blueprint failed")
        LOG.info("Success")

        # Publish blueprint to marketplace
        LOG.info(
            "Publishing marketplace blueprint {} with version {} to marketplace".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "publish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            PROJECT_NAME,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Publishing of marketplace blueprint to marketplace failed")
        LOG.info("Success")

        # Launching the bp in PUBLISHED state(Marketplace Item) with launch_params
        self.published_mpbp_lp_app_name = "Test_MPI_APP_LP_{}".format(
            str(uuid.uuid4())[-10:]
        )
        LOG.info(
            "Launching Marketplace Item {} with version {} with env-configuration".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "launch",
            "marketplace",
            "item",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
            "--project",
            PROJECT_NAME,
            "--app_name",
            self.published_mpbp_lp_app_name,
            "--profile_name",
            BP_LAUNCH_PROFILE_NAME,
            "-i",
            "-e",
            ENV_NAME,
        ]
        runner = CliRunner()

        result = runner.invoke(cli, command)
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
            pytest.fail("Launching of marketplace blueprint in PUBLISHED state failed")
        self.created_app_list.append(self.published_mpbp_lp_app_name)

        # Unpublish marketplace blueprint from marketplace
        LOG.info(
            "Unpublishing marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "unpublish",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail(
                "Unpublishing of marketplace blueprint in PUBLISHED state failed"
            )
        LOG.info("Success")

        # Delete the marketplace blueprint
        LOG.info(
            "Deleting marketplace blueprint {} with version {}".format(
                self.marketplace_bp_name, self.mpi1_version
            )
        )
        command = [
            "delete",
            "marketplace",
            "bp",
            self.marketplace_bp_name,
            "--version",
            self.mpi1_version,
        ]

        result = runner.invoke(cli, command)
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
            pytest.fail("Deletion of marketplace blueprint in ACCEPTED state failed")
        LOG.info("Success")
