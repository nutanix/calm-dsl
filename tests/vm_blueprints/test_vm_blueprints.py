import pytest
import sys
import json
import time
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

# for tcs
from calm.dsl.store import Version
from distutils.version import LooseVersion as LV
from tests.helper.status_map_helper import remove_status_map_from_bp
from tests.helper.output_variables_helper import remove_output_variables_from_bp
from tests.helper.vtpm_helper import remove_vtpm_config_from_bp
from tests.helper.global_variables_helper import remove_global_variables_from_spec

# Setting the recursion limit to max for
sys.setrecursionlimit(100000)

LOG = get_logging_handle(__name__)

SINGLE_VM_SINGLE_PROFILE_BP_PATH = (
    "tests/vm_blueprints/single_vm_blueprint/blueprint.py"
)
SINGLE_VM_SINGLE_PROFILE_BP_OUT_PATH = (
    "tests/vm_blueprints/single_vm_blueprint/single_vm_bp_output.json"
)
SINGLE_VM_MULTIPLE_PROFILE_BP_PATH = (
    "tests/vm_blueprints/single_vm_multi_profile_blueprint/blueprint.py"
)
SINGLE_VM_MULTIPLE_PROFILE_BP_OUT_PATH = "tests/vm_blueprints/single_vm_multi_profile_blueprint/single_vm_multi_profile_bp_output.json"


class TestVmBlueprints:
    def setup_method(self):
        """Method to instantiate to created_bp_list and reset context"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        self.created_bp_list = []
        self.created_app_list = []

    def teardown_method(self):
        """Method to delete creates bps and apps during tests"""

        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        self.created_bp_list = []

    @pytest.mark.parametrize(
        "bp_file_path",
        [SINGLE_VM_SINGLE_PROFILE_BP_PATH, SINGLE_VM_MULTIPLE_PROFILE_BP_PATH],
    )
    def test_single_vm_bp_create(self, bp_file_path):
        """tests bp creation of DSL Vm Blueprint"""

        runner = CliRunner()
        created_dsl_bp_name = "Test_Single_VM_DSL_{}".format(int(time.time()))
        LOG.info("Creating Bp {}".format(created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_file_path),
                "--name={}".format(created_dsl_bp_name),
                "--description='Test DSL Blueprint; to delete'",
            ],
        )
        self.created_bp_list.append(created_dsl_bp_name)
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
            pytest.fail("BP creation from python file failed")
        LOG.info("Success")

    @pytest.mark.parametrize(
        "bp_file_path,bp_output_file_path",
        [
            (SINGLE_VM_SINGLE_PROFILE_BP_PATH, SINGLE_VM_SINGLE_PROFILE_BP_OUT_PATH),
            (
                SINGLE_VM_MULTIPLE_PROFILE_BP_PATH,
                SINGLE_VM_MULTIPLE_PROFILE_BP_OUT_PATH,
            ),
        ],
    )
    def test_vm_bp_compile(self, bp_file_path, bp_output_file_path):

        runner = CliRunner()

        LOG.info("Compiling bp at {}".format(bp_file_path))
        result = runner.invoke(
            cli, ["-vv", "compile", "bp", "--file={}".format(bp_file_path)]
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
            pytest.fail("BP compile command failed")

        bp_json = json.loads(result.output)
        generated_json = bp_json["spec"]["resources"]
        generated_json["client_attrs"] = {}
        for profile in generated_json["app_profile_list"]:
            profile.pop("snapshot_config_list", None)
            profile.pop("restore_config_list", None)
            profile.pop("patch_list", None)
        known_json = json.loads(open(bp_output_file_path).read())

        # Replaces ahv images and nic & uuids and account_uuid
        for ind, sub in enumerate(known_json["substrate_definition_list"]):
            sub["create_spec"]["resources"]["nic_list"] = generated_json[
                "substrate_definition_list"
            ][ind]["create_spec"]["resources"]["nic_list"]
            sub["create_spec"]["resources"]["disk_list"] = generated_json[
                "substrate_definition_list"
            ][ind]["create_spec"]["resources"]["disk_list"]
            sub["create_spec"]["resources"]["account_uuid"] = generated_json[
                "substrate_definition_list"
            ][ind]["create_spec"]["resources"]["account_uuid"]

        # calm_version
        CALM_VERSION = Version.get_version("Calm")
        # For versions > 3.4, cred_class is needed to cred-payload
        if LV(CALM_VERSION) >= LV("3.4.0"):
            for cred in known_json["credential_definition_list"]:
                cred["cred_class"] = "static"

        if LV(CALM_VERSION) < LV("3.9.0"):
            remove_status_map_from_bp(known_json)
        if LV(CALM_VERSION) < LV("4.2.0"):
            remove_vtpm_config_from_bp(known_json)
        if LV(CALM_VERSION) < LV("4.3.0"):
            remove_global_variables_from_spec(known_json)

        remove_output_variables_from_bp(known_json)
        remove_output_variables_from_bp(generated_json)
        assert generated_json == known_json
