import pytest
import sys
import json
import time
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins import read_local_file

# for tcs
from calm.dsl.store import Version
from distutils.version import LooseVersion as LV
from tests.helper.status_map_helper import remove_status_map_from_bp
from tests.helper.output_variables_helper import remove_output_variables_from_bp

# Setting the recursion limit to max for
sys.setrecursionlimit(100000)

LOG = get_logging_handle(__name__)

SIMPLE_BP_FILE_PATH = "tests/simple_blueprint/test_simple_blueprint.py"
SIMPLE_BP_FILE_PATH2 = (
    "tests/simple_blueprint/test_simple_bp_with_downloadable_image.py"
)
SIMPLE_BP_OUT_PATH = "tests/simple_blueprint/test_simple_blueprint.json"
SIMPLE_BP_OUT_PATH2 = (
    "tests/simple_blueprint/test_simple_bp_with_downloadable_image.json"
)

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
SUBNET_UUID = NTNX_LOCAL_ACCOUNT["SUBNETS"][0]["UUID"]


class TestSimpleBlueprint:
    def setup_method(self):
        """Method to instantiate to created_bp_list"""

        self.created_bp_list = []

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
        [SIMPLE_BP_FILE_PATH, SIMPLE_BP_FILE_PATH2],
    )
    def test_create_bp(self, bp_file_path):

        runner = CliRunner()
        created_dsl_bp_name = "Test_Simple_DSL_BP_{}".format(int(time.time()))
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

        assert '"state": "ACTIVE"' in result.output

        LOG.info("Success")

    @pytest.mark.parametrize(
        "bp_file_path, json_file_path",
        [
            (SIMPLE_BP_FILE_PATH, SIMPLE_BP_OUT_PATH),
            (SIMPLE_BP_FILE_PATH2, SIMPLE_BP_OUT_PATH2),
        ],
    )
    def test_compile(self, bp_file_path, json_file_path):

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

        generated_json = json.loads(result.output)
        generated_json["spec"]["resources"]["app_profile_list"][0].pop(
            "snapshot_config_list", None
        )
        generated_json["spec"]["resources"]["app_profile_list"][0].pop(
            "restore_config_list", None
        )
        generated_json["spec"]["resources"]["app_profile_list"][0].pop(
            "patch_list", None
        )
        known_json = json.loads(open(json_file_path).read())

        # Change dynamic values in known json and remove account_uuid from generated_json
        for _sd in known_json["spec"]["resources"]["substrate_definition_list"]:
            if _sd["type"] == "AHV_VM":
                _sd["create_spec"]["resources"]["nic_list"][0]["subnet_reference"][
                    "uuid"
                ] = SUBNET_UUID

        for _sd in generated_json["spec"]["resources"]["substrate_definition_list"]:
            if _sd["type"] == "AHV_VM":
                _sd["create_spec"]["resources"].pop("account_uuid", None)

        # calm_version
        CALM_VERSION = Version.get_version("Calm")
        # For versions > 3.4, cred_class is needed to cred-payload
        if LV(CALM_VERSION) >= LV("3.4.0"):
            for cred in known_json["spec"]["resources"]["credential_definition_list"]:
                cred["cred_class"] = "static"

        # Pop the project referecne from metadata
        generated_json["metadata"].pop("project_reference", None)
        if LV(CALM_VERSION) < LV("3.9.0"):
            remove_status_map_from_bp(known_json["spec"]["resources"])

        remove_output_variables_from_bp(known_json["spec"]["resources"])
        remove_output_variables_from_bp(generated_json["spec"]["resources"])

        assert sorted(known_json.items()) == sorted(generated_json.items())
