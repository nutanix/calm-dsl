from calm.dsl.api.resource import get_resource_api
import uuid
import time
import json
import traceback
import pytest
import sys
from distutils.version import LooseVersion as LV
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client, vm_recovery_point
from calm.dsl.store import Version
from calm.dsl.cli.constants import APPLICATION
from calm.dsl.tools import make_file_dir
from calm.dsl.log import get_logging_handle
from tests.utils import Application as ApplicationHelper, Task as TaskHelper

LOG = get_logging_handle(__name__)

NORMAL_DSL_BP_FILEPATH = "tests/vm_recovery_point/normal_bp.py"
VRC_DSL_BP_FILEPATH = "tests/vm_recovery_point/blueprint.py"
LOCAL_RP_NAME_PATH = "tests/vm_recovery_point/.local/vm_rp_name"

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.slow
class TestVmRecoveryPointBp:
    app_helper = ApplicationHelper()
    task_helper = TaskHelper()

    vrp_name = ""
    vrp_uuid = ""

    def setup_method(self):
        """Method to instantiate to created_bp_list and created_app_list"""

        # TODO add deletion of vms also.
        self.created_bp_list = []
        self.created_app_list = []

        if not self.vrp_name:
            vrp_data = self._create_vm_recovery_point()
            self.vrp_name = vrp_data["name"]
            self.vrp_uuid = vrp_data["uuid"]

            # Writing vm_ip to local directory file
            LOG.info(
                "Writing vrp name {} to file '{}'".format(
                    self.vrp_name, LOCAL_RP_NAME_PATH
                )
            )
            make_file_dir(LOCAL_RP_NAME_PATH)
            with open(LOCAL_RP_NAME_PATH, "w") as f:
                f.write(self.vrp_name)

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

    def _delete_app(self, app_name):

        runner = CliRunner()
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Deleting App {} ".format(app_name))
        result = runner.invoke(cli, ["delete", "app", app_name])
        assert result.exit_code == 0
        LOG.info("App {} deleted successfully".format(app_name))

    def _create_bp(self, name, bp_path):

        runner = CliRunner()

        LOG.info("Creating Bp {}".format(name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_path),
                "--name={}".format(name),
                "--description='Test DSL Blueprint to delete'",
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
            pytest.fail("Blueprint creation failed")

        else:
            LOG.debug("Response: {}".format(result.output))

    def _launch_bp(self, bp_name, app_name):

        runner = CliRunner()
        LOG.info("Launching bp {} to create app {}".format(bp_name, app_name))
        result = runner.invoke(
            cli,
            ["launch", "bp", bp_name, "--app_name={}".format(app_name), "-i"],
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
            pytest.fail("App creation failed")

        else:
            LOG.debug("Response: {}".format(result.output))

    def _get_app_uuid(self, app_name):

        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", app_name, "--out=json"])
        app_data = json.loads(result.output)
        return app_data["metadata"]["uuid"]

    def _create_vm_recovery_point(self):

        # Create blueprint
        bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
        self._create_bp(bp_name, NORMAL_DSL_BP_FILEPATH)
        self.created_bp_list.append(bp_name)

        # Create application
        app_name = "App{}".format(str(uuid.uuid4())[:10])
        self._launch_bp(bp_name, app_name)
        self.created_app_list.append(app_name)

        # Wait for app creation completion
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Application {} created successfully".format(app_name))

        sub_pd = self.app_helper.get_substrates_platform_data(
            app_name, with_metadata=True
        )
        obj_resource = "mh_vms/{}/snapshot".format(sub_pd["metadata"]["uuid"])

        client = get_api_client()
        Obj = get_resource_api(obj_resource, client.connection)

        vm_recovery_point_name = "VRP-{}".format(str(uuid.uuid4())[:10])
        payload = {
            "name": vm_recovery_point_name,
            "recovery_point_type": "CRASH_CONSISTENT",
        }

        LOG.info("Creating snapshot {}".format(vm_recovery_point_name))
        res, err = Obj.create(payload)
        if err:
            LOG.error(err)

        res = res.json()
        task_uuid = res["task_uuid"]

        task_payload = self.task_helper.poll_task_to_state(client, task_uuid)
        vm_recovery_point_uuid = task_payload["entity_reference_list"][0]["uuid"]

        self.vrp_name = vm_recovery_point_name
        self.vrp_uuid = vm_recovery_point_uuid

        return {"name": vm_recovery_point_name, "uuid": vm_recovery_point_uuid}

    def test_bp_compile_having_rp(self):
        """
        Steps:
            1. Create vm-recovery-point
            2. Compile blueprint having vm-recovery-point
        """

        runner = CliRunner()
        LOG.info("Compiling Bp {}".format(VRC_DSL_BP_FILEPATH))
        result = runner.invoke(
            cli,
            [
                "compile",
                "bp",
                "--file={}".format(VRC_DSL_BP_FILEPATH),
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
            pytest.fail("App creation failed")

        bp_json = json.loads(result.output)
        assert (
            bp_json["spec"]["resources"]["substrate_definition_list"][0][
                "recovery_point_reference"
            ]["uuid"]
            == self.vrp_uuid
        )
        assert (
            bp_json["spec"]["resources"]["substrate_definition_list"][0][
                "recovery_point_reference"
            ]["name"]
            == self.vrp_name
        )

    def test_bp_launch_having_vm_rp(self):
        """
        Steps:
            1. Create Blueprint
            2. Create App
            3. Create snapshot
            4. Create bp using that vm-recovery point
            5. Launch blueprint
        """

        # Create blueprint
        bp_name = "Blueprint{}".format(str(uuid.uuid4())[:10])
        self._create_bp(bp_name, VRC_DSL_BP_FILEPATH)
        self.created_bp_list.append(bp_name)

        # Create application
        app_name = "App{}".format(str(uuid.uuid4())[:10])
        self._launch_bp(bp_name, app_name)
        self.created_app_list.append(app_name)

        # Wait for app creation completion
        self.app_helper._wait_for_non_busy_state(app_name)
        LOG.info("Application {} created successfully".format(app_name))
