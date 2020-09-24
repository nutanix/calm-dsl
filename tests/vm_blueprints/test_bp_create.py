import pytest
import json
import time
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

SINGLE_VM_SINGLE_PROFILE_BP_PATH = (
    "tests/vm_blueprints/single_vm_blueprint/test_blueprint.py"
)
SINGLE_VM_MULTIPLE_PROFILE_BP_PATH = (
    "tests/vm_blueprints/single_vm_multi_profile_blueprint/test_blueprint.py"
)


class TestVmBlueprints:
    def setup_method(self):
        """Method to instantiate to created_bp_list"""

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
        created_dsl_bp_name = "Test_Existing_VM_DSL_{}".format(int(time.time()))
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
