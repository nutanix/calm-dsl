from click.testing import CliRunner
import time
import pytest
import json
import sys
import traceback

from calm.dsl.cli import main as cli
from calm.dsl.cli.constants import APPLICATION
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
BP_FILE_PATH = "tests/cli/runtime_helpers/ahv/blueprint.py"
LAUNCH_PARAMS = "tests/cli/runtime_helpers/ahv/editable_params.py"
ACTION_LAUNCH_PARAMS = "tests/cli/runtime_helpers/ahv/profile_action_editable_params.py"
PROFILE_ACTION_NAME = "test_profile_action"
NON_BUSY_APP_STATES = [
    APPLICATION.STATES.STOPPED,
    APPLICATION.STATES.RUNNING,
    APPLICATION.STATES.ERROR,
]


class TestEditables:
    def setup_method(self):
        """Method to instantiate to created_bp_list and created_app_list"""

        self.created_bp_list = []
        self.created_app_list = []

    def teardown_method(self):
        """Method to delete creates bps and apps during tests"""

        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        for app_name in self.created_app_list:
            LOG.info("Deleting app {}".format(app_name))
            runner = CliRunner()
            self._wait_for_non_busy_state(app_name)
            result = runner.invoke(cli, "delete app {}".format(app_name))
            LOG.debug(result.output)
            assert result.exit_code == 0, "Error occured in application deletion"

        self.created_app_list = []
        self.created_bp_list = []

    @pytest.mark.slow
    def test_ahv_substrate_editables_interactive_mode(self):
        """Tests interactive mode for getting runtime values under ahv substrate"""

        runner = CliRunner()
        command = "launch bp --file {}".format(BP_FILE_PATH)
        result = runner.invoke(cli, command)

        # create blueprint
        BP_NAME = "Test_Runtime_Bp_{}".format(int(time.time()))
        command = "create bp --file={} --name={}".format(BP_FILE_PATH, BP_NAME)

        LOG.info("Creating Bp {}".format(BP_NAME))
        result = runner.invoke(cli, command)
        self.created_bp_list.append(BP_NAME)

        LOG.debug(result.output)
        if result.exit_code:
            pytest.fail("Error occured in bp creation")

        # launch blueprint
        APP_NAME = "Test_Runtime_App_{}".format(int(time.time()))
        command = "launch bp {} -a {}".format(BP_NAME, APP_NAME)

        input = [
            "5",
            "22",
            "@@{calm_application_name}@@-@@{calm_array_index}@@",
            "y",  # Edit categories
            "y",  # Delete category
            "AppFamily",  # Category Family
            "y",  # Delete more cetgories
            "AppTier",  # Category Family
            "n",  # Delete category
            "y",  # Add category
            "6",  # Index of category (AppFamily:DevOps)
            "n",  # Add more category
            "vlan.0",  # Nic name
            "CLONE_FROM_IMAGE",  # Opertaion
            "CentOS-7-Cloud-Init",  # Image name
            "DISK",  # Device Type of 2nd disk
            "PCI",  # Device Bus
            "ALLOCATE_STORAGE_CONTAINER",  # Operation
            "10",  # Disk size
            "1",  # vCPUS
            "1",  # Cores per vCPU
            "1",  # Memory(GiB)
            "y",  # Connection status for serail port 0
            "n",  # Connection status for serail port 0
            "y",  # Edit guest customization
            "Sample data",  # User data
            "bar1",  # Variable value
            "bar2",  # Variable value
        ]

        input = "\n".join(input)

        LOG.info(
            "Launching blueprint '{}' to create app '{}'".format(BP_NAME, APP_NAME)
        )
        result = runner.invoke(cli, command, input=input)
        self.created_app_list.append(APP_NAME)

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
            pytest.fail("App creation failed")

    @pytest.mark.slow
    def test_ahv_substrate_editables_non_interactive_mode(self):
        """Tests non-interactive mode for getting runtime values under ahv substrate"""

        runner = CliRunner()
        command = "launch bp --file {}".format(BP_FILE_PATH)
        result = runner.invoke(cli, command)

        # create blueprint
        BP_NAME = "Test_Runtime_Bp_{}".format(int(time.time()))
        command = "create bp --file={} --name={}".format(BP_FILE_PATH, BP_NAME)

        LOG.info("Creating Bp {}".format(BP_NAME))
        result = runner.invoke(cli, command)
        self.created_bp_list.append(BP_NAME)

        LOG.debug(result.output)
        if result.exit_code:
            pytest.fail("Error occured in bp creation")

        APP_NAME = "Test_Runtime_App_{}".format(int(time.time()))
        command = "launch bp {} -a {} -l {}".format(BP_NAME, APP_NAME, LAUNCH_PARAMS)

        LOG.info(
            "Launching blueprint '{}' to create app '{}'".format(BP_NAME, APP_NAME)
        )
        result = runner.invoke(cli, command)
        self.created_app_list.append(APP_NAME)

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
            pytest.fail("App creation failed")

        # Test actions
        self._test_run_action_on_app(app_name=APP_NAME)

    def _test_run_action_on_app(self, app_name):

        runner = CliRunner()

        self._wait_for_non_busy_state(app_name)

        # Run profile action
        command = "run action {} -a {} ".format(PROFILE_ACTION_NAME, app_name)

        LOG.info("Testing run action command")
        cli_input = ["mail_new_val", "secret_new_val", "mail2"]
        cli_input = "\n".join(cli_input)

        result = runner.invoke(cli, command, input=cli_input)
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
                "Failed to run action {} on app {} using --ignore_runtime_variables flag".format(
                    PROFILE_ACTION_NAME, app_name
                )
            )
        LOG.info("Success")

        self._wait_for_non_busy_state(app_name)

        # Run using --ignore_runtime_variables flag
        command = "run action {} -a {} --ignore_runtime_variables".format(
            PROFILE_ACTION_NAME, app_name
        )

        LOG.info("Testing --ignore_runtime_variables flag for running profile actions")
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
                "Failed to run action {} on app {} using --ignore_runtime_variables flag".format(
                    PROFILE_ACTION_NAME, app_name
                )
            )
        LOG.info("Success")

        self._wait_for_non_busy_state(app_name)

        # Run using --launch_params flag
        command = "run action {} -a {} --launch_params {}".format(
            PROFILE_ACTION_NAME, app_name, ACTION_LAUNCH_PARAMS
        )

        LOG.info("Testing --launch_params option for running profile actions")
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
                "Failed to run action {} on app {} using --launch_params option".format(
                    PROFILE_ACTION_NAME, app_name
                )
            )

        LOG.info("Success")

    def _wait_for_non_busy_state(self, name):
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", name, "--out=json"])
        app_data = json.loads(result.output)
        LOG.info("App State: {}".format(app_data["status"]["state"]))
        LOG.debug("App Terminal states: {}".format(NON_BUSY_APP_STATES))
        cnt = 0
        while app_data["status"]["state"] not in NON_BUSY_APP_STATES:
            time.sleep(5)
            result = runner.invoke(cli, ["describe", "app", name, "--out=json"])
            app_data = json.loads(result.output)
            LOG.info("App State: {}".format(app_data["status"]["state"]))
            if cnt > 20:
                LOG.error("Failed to reach terminal state in 100 seconds")
                sys.exit(-1)
            cnt += 1
