import pytest
import sys
import json
import time
import traceback
from click.testing import CliRunner
from distutils.version import LooseVersion as LV
from calm.dsl.builtins.models.utils import read_local_file
from calm.dsl.config import get_context
from calm.dsl.builtins.models.metadata_payload import reset_metadata_obj

from calm.dsl.store import Version
from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle
from tests.cli.runtime_helpers.ahv.editable_params import DSL_CONFIG
from tests.helper.status_map_helper import remove_status_map_from_bp
from tests.helper.output_variables_helper import remove_output_variables_from_bp
from tests.helper.vtpm_helper import remove_vtpm_config_from_bp_resources
from tests.helper.global_variables_helper import remove_global_variables_from_spec

# Setting the recursion limit to max for
sys.setrecursionlimit(100000)

LOG = get_logging_handle(__name__)

BP_FILE_PATH = "tests/ahv_vm_overlay_subnet/test_overlay_subnet_blueprint.py"
BP_OUT_PATH = "tests/ahv_vm_overlay_subnet/test_overlay_subnet_blueprint.json"
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
# calm_version
CALM_VERSION = Version.get_version("Calm")


# TODO add another check to check if there is any vpc present on the PC
@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.5.0") or not DSL_CONFIG.get("IS_VPC_ENABLED", False),
    reason="Overlay Subnets can be used in Calm v3.5.0+ blueprints or VPC is disabled on the setup",
)
class TestOverlaySubnetBlueprint:
    def setup_method(self):
        """Method to instantiate to created_bp_list"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

        self.created_bp_list = []

    def teardown_method(self):
        """Method to delete creates bps and apps during tests"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

        # Resetting metadata object
        reset_metadata_obj()

        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        self.created_bp_list = []

    def test_create_bp(self):

        runner = CliRunner()
        created_dsl_bp_name = "Test_Overlay_Subnet_DSL_BP_{}".format(int(time.time()))
        LOG.info("Creating Bp {}".format(created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(BP_FILE_PATH),
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

        if "DRAFT" not in result.output:
            assert '"state": "ACTIVE"' in result.output

        LOG.info("Success")

    def test_compile(self):

        runner = CliRunner()
        LOG.info("Compiling bp at {}".format(BP_FILE_PATH))
        result = runner.invoke(
            cli, ["-vv", "compile", "bp", "--file={}".format(BP_FILE_PATH)]
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
        generated_json = generated_json["spec"]
        generated_json["resources"].pop("client_attrs", None)

        # Assert whether account_uuid is present in generated_json
        sub_account_uuid = generated_json["resources"]["substrate_definition_list"][0][
            "create_spec"
        ]["resources"]["account_uuid"]
        assert sub_account_uuid != ""

        # Replace correct account uuid in known_json
        known_json = json.loads(open(BP_OUT_PATH).read())
        known_json = known_json["spec"]
        known_json["resources"]["substrate_definition_list"][0]["create_spec"][
            "resources"
        ]["account_uuid"] = sub_account_uuid
        known_json["resources"].pop("client_attrs", None)

        known_json["resources"]["substrate_definition_list"][0]["create_spec"][
            "cluster_reference"
        ] = generated_json["resources"]["substrate_definition_list"][0]["create_spec"][
            "cluster_reference"
        ]
        known_json["resources"]["substrate_definition_list"][0]["create_spec"][
            "resources"
        ]["nic_list"][0]["subnet_reference"]["uuid"] = generated_json["resources"][
            "substrate_definition_list"
        ][
            0
        ][
            "create_spec"
        ][
            "resources"
        ][
            "nic_list"
        ][
            0
        ][
            "subnet_reference"
        ][
            "uuid"
        ]
        known_json["resources"]["substrate_definition_list"][0]["create_spec"][
            "resources"
        ]["nic_list"][0]["vpc_reference"]["uuid"] = generated_json["resources"][
            "substrate_definition_list"
        ][
            0
        ][
            "create_spec"
        ][
            "resources"
        ][
            "nic_list"
        ][
            0
        ][
            "vpc_reference"
        ][
            "uuid"
        ]

        if LV(CALM_VERSION) < LV("3.9.0"):
            remove_status_map_from_bp(known_json)

        # remove vtpm config for version less than 4.2.0
        if LV(CALM_VERSION) < LV("4.2.0"):
            remove_vtpm_config_from_bp_resources(known_json)

        if LV(CALM_VERSION) < LV("4.3.0"):
            remove_global_variables_from_spec(known_json)

        remove_output_variables_from_bp(known_json)
        remove_output_variables_from_bp(generated_json)

        assert sorted(known_json.items()) == sorted(generated_json.items())
