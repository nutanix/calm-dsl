import uuid
import time
import json
import traceback
import pytest
import sys
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.cli.constants import APPLICATION
from calm.dsl.tools import make_file_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_BP_FILEPATH = "tests/brownfield/separate_file_example/blueprint.py"
DSL_BP_BD_FILEPATH = "tests/brownfield/separate_file_example/brownfield.py"
LOCAL_VM_IP_PATH = "tests/brownfield/separate_file_example/.local/vm_ip"
NON_BUSY_APP_STATES = [
    APPLICATION.STATES.STOPPED,
    APPLICATION.STATES.RUNNING,
    APPLICATION.STATES.ERROR,
]

NON_BUSY_APP_DELETE_STATES = [APPLICATION.STATES.ERROR, APPLICATION.STATES.DELETED]


@pytest.mark.slow
class TestBrownFieldCommands:
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
            self._delete_app(app_name)

        self.created_app_list = []
        self.created_bp_list = []

    def _wait_for_non_busy_state(self, app_name):

        runner = CliRunner()
        non_busy_statuses = [
            "Status: {}".format(state) for state in NON_BUSY_APP_STATES
        ]
        result = runner.invoke(cli, ["describe", "app", app_name])
        while not any([state_str in result.output for state_str in non_busy_statuses]):
            time.sleep(5)
            result = runner.invoke(cli, ["describe", "app", app_name])

    def _wait_for_app_delete_busy_state(self, app_name):

        runner = CliRunner()
        non_busy_statuses = [
            "Status: {}".format(state) for state in NON_BUSY_APP_DELETE_STATES
        ]
        result = runner.invoke(cli, ["describe", "app", app_name])
        while not any([state_str in result.output for state_str in non_busy_statuses]):
            time.sleep(5)
            result = runner.invoke(cli, ["describe", "app", app_name])

    def _delete_app(self, app_name):

        runner = CliRunner()
        self._wait_for_non_busy_state(app_name)
        LOG.info("Deleting App {} ".format(app_name))
        result = runner.invoke(cli, ["delete", "app", app_name])
        assert result.exit_code == 0
        self._wait_for_app_delete_busy_state(app_name=app_name)
        LOG.info("App {} deleted successfully".format(app_name))

    def _create_bp(self, name):

        runner = CliRunner()

        LOG.info("Creating Bp {}".format(name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(DSL_BP_FILEPATH),
                "--name={}".format(name),
                "--description='Test DSL Blueprint; to delete'",
            ],
        )

        LOG.debug("Response: {}".format(result.output))
        assert result.exit_code == 0

    def test_app_vm_in_brownfield_bp(self):
        """
        Steps:
            1. Create Blueprint
            2. Create App
            3. Soft Delete app and extract vm-ip from it
            4. Create Brownfield Application using that vm-ip
            5. Delete brownfield application
        """

        runner = CliRunner()

        # Create blueprint
        bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
        self._create_bp(bp_name)
        self.created_bp_list.append(bp_name)

        # Create application
        app_name = "App{}".format(str(uuid.uuid4())[:10])
        LOG.info("Creating App {}".format(app_name))
        result = runner.invoke(
            cli,
            [
                "launch",
                "bp",
                bp_name,
                "--app_name={}".format(app_name),
                "--ignore_runtime_variables",
            ],
        )
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Creation of app {} failed".format(app_name))

        # Wait for app creation completion
        self._wait_for_non_busy_state(app_name)
        LOG.info("Application {} created successfully".format(app_name))

        LOG.info("Extracting vm ip from the app")
        result = runner.invoke(cli, ["describe", "app", app_name, "--out=json"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Describe of app {} failed".format(app_name))

        # Extracting vm+ip from the app_json
        app_json = json.loads(result.output)
        app_state = app_json["status"]["state"]
        if app_state != APPLICATION.STATES.RUNNING:
            LOG.error("App went to {} state".format(app_state))
            sys.exit(-1)

        vm_ip = app_json["status"]["resources"]["deployment_list"][0][
            "substrate_configuration"
        ]["element_list"][0]["address"]

        LOG.info("Soft deleting the app {}".format(app_name))
        result = runner.invoke(cli, ["delete", "app", app_name, "--soft"])
        if result.exit_code:
            LOG.error(result.output)
            pytest.fail("Deletion of app {} failed".format(app_name))

        # Wait for app deletion completion
        self._wait_for_app_delete_busy_state(app_name)
        LOG.info("Soft Delete of app {} completed".format(app_name))

        # Writing vm_ip to local directory file
        LOG.info("Writing vm_ip {} to file '{}'".format(vm_ip, LOCAL_VM_IP_PATH))
        make_file_dir(LOCAL_VM_IP_PATH)
        with open(LOCAL_VM_IP_PATH, "w") as f:
            f.write(vm_ip)

        # Creating brownfield blueprint
        app_name = "BrownfieldApplication{}".format(str(uuid.uuid4())[:10])
        LOG.info("Creating Brownfield Application {}".format(app_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "app",
                "--file={}".format(DSL_BP_FILEPATH),
                "--brownfield_deployments={}".format(DSL_BP_BD_FILEPATH),
                "--name={}".format(app_name),
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
            pytest.fail("Brownfield App creation failed")

        self._wait_for_non_busy_state(app_name)
        LOG.info("Brownfield App {} created successfully".format(app_name))
        self.created_app_list.append(app_name)

    @pytest.mark.parametrize(
        "vm_type", ["AHV_VM", "AWS_VM", "AZURE_VM", "GCP_VM", "VMWARE_VM"]
    )
    @pytest.mark.parametrize("project", ["default"])
    def test_get_brownfield_vms(self, vm_type, project):
        """
        Test get command on brownfield vms
        Note: Test will fail for provider = VMWARE_VM for version less than 2.9.8.1 and 3.0.0 (https://jira.nutanix.com/browse/CALM-18635)
        """

        runner = CliRunner()
        LOG.info("Testing 'calm get brownfield vms --type {}' command".format(vm_type))
        result = runner.invoke(
            cli,
            [
                "get",
                "brownfield",
                "vms",
                "--project={}".format(project),
                "--type={}".format(vm_type),
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
            pytest.fail("Brownfield Vm Get failed")
        LOG.info("Success")
