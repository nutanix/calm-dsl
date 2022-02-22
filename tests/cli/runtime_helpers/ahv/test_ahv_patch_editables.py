from click.testing import CliRunner
import time
import pytest
import json
import os
import sys
import traceback

from calm.dsl.cli import main as cli
from calm.dsl.cli.constants import APPLICATION
from calm.dsl.builtins import read_local_file
from calm.dsl.log import get_logging_handle
from tests.utils import Application as ApplicationHelper

LOG = get_logging_handle(__name__)
BP_FILE_PATH = "tests/cli/runtime_helpers/ahv/app_edit_test_blueprint.py"
LAUNCH_PARAMS = "tests/cli/runtime_helpers/ahv/editable_params.py"
PATCH_EDITABLE_PARAMS_DIR = "tests/cli/runtime_helpers/ahv/patch_editable_params"
PATCH_UPDATE_NAME = "patch_update"
NON_BUSY_APP_STATES = [
    APPLICATION.STATES.STOPPED,
    APPLICATION.STATES.RUNNING,
    APPLICATION.STATES.ERROR,
]

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]  # TODO change network constants
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
SUBNET_UUID = NTNX_LOCAL_ACCOUNT["SUBNETS"][0]["UUID"]


class TestEditables:
    app_helper = ApplicationHelper()

    def setup_method(self):
        """Method to instantiate to created_bp_list and created_app_list"""

        self.created_bp_list = []
        self.created_app_list = []
        self.created_local_files_list = []

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
            self.app_helper._wait_for_states(app_name, NON_BUSY_APP_STATES)
            result = runner.invoke(cli, "delete app {}".format(app_name))
            assert result.exit_code == 0, "Error occured in application deletion"

        for local_file in self.created_local_files_list:
            LOG.info("Deleting file {}".format(local_file))
            try:
                os.remove(local_file)
                LOG.debug("File {} removed successfully".format(local_file))
            except FileNotFoundError:
                LOG.info("File {} not found".format(local_file))

        self.created_app_list = []
        self.created_bp_list = []
        self.created_local_files_list = []

    @pytest.mark.slow
    def test_ahv_patch_update_from_file(self):
        """Tests non-interactive mode for getting runtime values under ahv substrate"""
        APP_NAME = self._create_app()
        FILE_NAME = self._get_editables_file(APP_NAME)
        patch_name = PATCH_UPDATE_NAME + "1"
        self._test_run_patch_update_on_app_editables_file(
            app_name=APP_NAME, file_name=FILE_NAME, patch_name=patch_name
        )
        app_platform_data = self.app_helper.get_substrates_platform_data(APP_NAME)
        assert (
            app_platform_data["resources"]["num_sockets"] == 2
            and app_platform_data["resources"]["num_vcpus_per_socket"] == 2
            and app_platform_data["resources"]["memory_size_mib"] == 2048
        )
        assert len(app_platform_data["resources"]["nic_list"]) == 1
        assert len(app_platform_data["resources"]["disk_list"]) == 2

        patch_name = PATCH_UPDATE_NAME + "2"
        self._test_run_patch_update_on_app_editables_file(
            app_name=APP_NAME, file_name=FILE_NAME, patch_name=patch_name
        )
        app_platform_data = self.app_helper.get_substrates_platform_data(APP_NAME)
        assert (
            app_platform_data["resources"]["num_sockets"] == 1
            and app_platform_data["resources"]["num_vcpus_per_socket"] == 3
            and app_platform_data["resources"]["memory_size_mib"] == 3072
        )
        assert len(app_platform_data["resources"]["nic_list"]) == 2
        assert len(app_platform_data["resources"]["disk_list"]) == 3

        patch_name = PATCH_UPDATE_NAME + "3"
        self._test_run_patch_update_on_app_editables_file(
            app_name=APP_NAME, file_name=FILE_NAME, patch_name=patch_name
        )
        app_platform_data = self.app_helper.get_substrates_platform_data(APP_NAME)
        assert (
            app_platform_data["resources"]["num_sockets"] == 2
            and app_platform_data["resources"]["num_vcpus_per_socket"] == 2
            and app_platform_data["resources"]["memory_size_mib"] == 2048
        )
        assert len(app_platform_data["resources"]["nic_list"]) == 3
        assert app_platform_data["resources"]["disk_list"][0]["disk_size_mib"] == 10240

    @pytest.mark.slow
    def test_ahv_patch_update_ignore_editables(self):
        """Tests non-interactive mode for getting runtime values under ahv substrate"""
        APP_NAME = self._create_app()
        patch_name = PATCH_UPDATE_NAME + "1"
        self._test_run_patch_update_on_app_ignore_runtime_variables(
            app_name=APP_NAME, patch_name=patch_name
        )
        app_platform_data = self.app_helper.get_substrates_platform_data(APP_NAME)
        assert (
            app_platform_data["resources"]["num_sockets"] == 2
            and app_platform_data["resources"]["num_vcpus_per_socket"] == 2
            and app_platform_data["resources"]["memory_size_mib"] == 2048
        )
        assert len(app_platform_data["resources"]["nic_list"]) == 1
        assert len(app_platform_data["resources"]["disk_list"]) == 2

        patch_name = PATCH_UPDATE_NAME + "2"
        self._test_run_patch_update_on_app_ignore_runtime_variables(
            app_name=APP_NAME, patch_name=patch_name
        )
        app_platform_data = self.app_helper.get_substrates_platform_data(APP_NAME)
        assert (
            app_platform_data["resources"]["num_sockets"] == 1
            and app_platform_data["resources"]["num_vcpus_per_socket"] == 3
            and app_platform_data["resources"]["memory_size_mib"] == 3072
        )
        assert len(app_platform_data["resources"]["nic_list"]) == 2
        assert len(app_platform_data["resources"]["disk_list"]) == 3

        patch_name = PATCH_UPDATE_NAME + "3"
        self._test_run_patch_update_on_app_ignore_runtime_variables(
            app_name=APP_NAME, patch_name=patch_name
        )
        app_platform_data = self.app_helper.get_substrates_platform_data(APP_NAME)
        assert (
            app_platform_data["resources"]["num_sockets"] == 2
            and app_platform_data["resources"]["num_vcpus_per_socket"] == 2
            and app_platform_data["resources"]["memory_size_mib"] == 2048
        )
        assert len(app_platform_data["resources"]["nic_list"]) == 3
        assert app_platform_data["resources"]["disk_list"][0]["disk_size_mib"] == 10240

    def _get_editables_file(self, app_name):
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "app", app_name, "--out=json"])
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

        app_data = json.loads(result.output)
        patch_attrs_uuid = app_data["spec"]["resources"]["patch_list"][0]["attrs_list"][
            0
        ]["uuid"]

        template_file = "{}/template.py".format(PATCH_EDITABLE_PARAMS_DIR)
        editables_file = "{}/{}.py".format(PATCH_EDITABLE_PARAMS_DIR, patch_attrs_uuid)

        replaced_text = ""

        with open(template_file, "r") as f:
            for line in f.readlines():
                replaced_text += line.replace("PATCH_ATTRS_UUID", patch_attrs_uuid)

        replaced_text = replaced_text.replace("NIC_UUID", SUBNET_UUID)

        with open(editables_file, "w") as f:
            f.write(replaced_text)
            self.created_local_files_list.append(editables_file)

        return editables_file

    def _create_app(self):
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
        return APP_NAME

    def _test_run_patch_update_on_app_editables_file(
        self, app_name, file_name, patch_name
    ):

        runner = CliRunner()

        self.app_helper._wait_for_states(app_name, NON_BUSY_APP_STATES)

        command = "update app {} {} -r {}".format(app_name, patch_name, file_name)

        LOG.info("Testing --runtime_params option for running patch update actions")
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
                "Failed to run patch {} on app {} using --runtime_params option".format(
                    patch_name, app_name
                )
            )

        self.app_helper._wait_for_states(app_name, ["updating"], timeout=200)
        self.app_helper._wait_for_states(app_name, NON_BUSY_APP_STATES, timeout=500)

        LOG.info("Success")

    def _test_run_patch_update_on_app_ignore_runtime_variables(
        self, app_name, patch_name
    ):

        # Run using --ignore_runtime_variables flag
        runner = CliRunner()

        self.app_helper._wait_for_states(app_name, NON_BUSY_APP_STATES)

        command = "update app {} {} --ignore_runtime_variables".format(
            app_name, patch_name
        )

        LOG.info("Testing --ignore_runtime_variables flag for running patch actions")
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
                "Failed to run patch {} on app {} using -ignore_runtime_variables- option".format(
                    patch_name, app_name
                )
            )

        self.app_helper._wait_for_states(app_name, ["updating"], timeout=200)
        self.app_helper._wait_for_states(app_name, NON_BUSY_APP_STATES, timeout=500)

        LOG.info("Success")
