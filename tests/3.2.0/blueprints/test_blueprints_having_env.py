import pytest
import json
import uuid
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.cli.bps import get_blueprint
from calm.dsl.builtins import read_local_file
from calm.dsl.config import get_context
from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

SIMPLE_BLUEPRINT = "tests/3.2.0/blueprints/simple_blueprint_example/blueprint.py"
AHV_HELPER_BLUEPRINT = (
    "tests/3.2.0/blueprints/test_blueprint_having_ahv_helper/blueprint.py"
)
STATIC_PROVIDER_SPEC_BLUEPRINT = (
    "tests/3.2.0/blueprints/test_blueprint_with_static_provider_spec/blueprint.py"
)
VM_BLUEPRINT = "tests/3.2.0/blueprints/vm_blueprints/blueprint.py"

# projects
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
ENV_UUID = PROJECT["ENVIRONMENTS"][0]["UUID"]


class TestBlueprint:
    def setup_method(self):
        """Method to instantiate to created_bp_list and reset context"""

        # Resetting context
        ContextObj = get_context()
        ContextObj.reset_configuration()

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
        [
            SIMPLE_BLUEPRINT,
            AHV_HELPER_BLUEPRINT,
            STATIC_PROVIDER_SPEC_BLUEPRINT,
            VM_BLUEPRINT,
        ],
    )
    def test_env_presence_in_compiled_bp(self, bp_file_path):
        """tests env presence in compiled bp"""

        runner = CliRunner()

        LOG.info("Compiling bp file at {}".format(bp_file_path))
        result = runner.invoke(
            cli, ["-vvvv", "compile", "bp", "--file={}".format(bp_file_path)]
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

        assert ENV_UUID in result.output

    @pytest.mark.parametrize(
        "bp_file_path",
        [
            SIMPLE_BLUEPRINT,
            AHV_HELPER_BLUEPRINT,
            STATIC_PROVIDER_SPEC_BLUEPRINT,
            VM_BLUEPRINT,
        ],
    )
    def test_bp_create(self, bp_file_path):
        """tests creation of blueprint"""

        runner = CliRunner()
        client = get_api_client()
        created_dsl_bp_name = "Test_Single_VM_DSL_{}".format(str(uuid.uuid4())[-10:])

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

        self.created_bp_list.append(created_dsl_bp_name)

        # Get the blueprint
        bp_data = get_blueprint(client, name=created_dsl_bp_name)
        res, _ = client.blueprint.read(bp_data["metadata"]["uuid"])
        bp_data = res.json()

        LOG.info("Asserting env data in blueprint")
        for _profile in bp_data["status"]["resources"].get("app_profile_list", []):
            _envs = _profile.get("environment_reference_list", [])
            assert len(_envs) == 1
            for _e in _envs:
                assert _e["uuid"] == ENV_UUID

        LOG.info("Success")
