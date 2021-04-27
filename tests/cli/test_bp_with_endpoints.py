import pytest
import time
import os
import json
import traceback
from distutils.version import LooseVersion as LV
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.api import get_api_client
from calm.dsl.store import Version
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


DSL_BP_FILEPATH = "tests/existing_vm_example_with_target_endpoint/test_existing_vm_bp_with_endpoint_target_task.py"
JSON_BP_FILEPATH = (
    "tests/existing_vm_example_with_target_endpoint/test_existing_vm_bp.json"
)
DSL_EP_PATH = "tests/cli/endpoints/linux_endpoint.py"
CALM_ENDPOINT_NAME = "DND-Endpoint"

# calm_version
CALM_VERSION = Version.get_version("Calm")


@pytest.mark.slow
@pytest.mark.skipif(
    LV(CALM_VERSION) < LV("3.0.0"), reason="Endpoints in bp is supported from 3.0.0"
)
class TestBpCommands:
    def setup_method(self):
        """Method to create endpoint"""

        client = get_api_client()
        self.endpoint = CALM_ENDPOINT_NAME

        # Check if there is existing endpoint with this name
        payload = {"filter": "name=={}".format(self.endpoint)}
        res, _ = client.endpoint.list(payload)
        res = res.json()

        if res["metadata"]["total_matches"] > 0:
            return

        # If there is no endpoint, create one
        LOG.info("Creating Endpoint {}".format(self.endpoint))
        runner = CliRunner()
        result = runner.invoke(
            cli, ["create", "endpoint", "-f", DSL_EP_PATH, "-n", self.endpoint]
        )
        assert result.exit_code == 0
        LOG.info("Success")

    def teardown_method(self):
        """Method to delete endpoint"""

        LOG.info("Deleting Endpoint {}".format(self.endpoint))
        runner = CliRunner()
        result = runner.invoke(cli, ["delete", "endpoint", self.endpoint])
        assert result.exit_code == 0
        LOG.info("Success")

    def test_compile_bp(self):
        runner = CliRunner()
        LOG.info("Compiling Bp file at {}".format(DSL_BP_FILEPATH))
        result = runner.invoke(
            cli, ["compile", "bp", "--file={}".format(DSL_BP_FILEPATH)]
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
        LOG.info("Success")

    def test_dsl_bp_create(self):
        runner = CliRunner()
        self.created_dsl_bp_name = "Test_Existing_VM_ENDPOINT_DSL_{}".format(
            int(time.time())
        )
        LOG.info("Creating Bp {}".format(self.created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(DSL_BP_FILEPATH),
                "--name={}".format(self.created_dsl_bp_name),
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
        LOG.info("Success")
        self._test_dsl_bp_delete()

    def test_json_bp_create(self):
        runner = CliRunner()
        self.created_json_bp_name = "Test_Exisisting_VM_JSON_{}".format(
            int(time.time())
        )

        # Getting the data stored in provider spec file
        with open(JSON_BP_FILEPATH, "r") as f:
            old_spec_data = f.read()

        try:
            # Compile the BP and to a json file, for using to test json upload
            os.system(
                "calm -vvvvv compile bp --file={} > {}".format(
                    DSL_BP_FILEPATH, JSON_BP_FILEPATH
                )
            )
            LOG.info("Creating Bp {}".format(self.created_json_bp_name))
            result = runner.invoke(
                cli,
                [
                    "create",
                    "bp",
                    "--file={}".format(JSON_BP_FILEPATH),
                    "--name={}".format(self.created_json_bp_name),
                    "--description='Test JSON Blueprint; to delete'",
                ],
                catch_exceptions=True,
            )
            if result.exit_code:
                cli_res_dict = {
                    "Output": result.output,
                    "Exception": str(result.exception),
                }
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

        finally:
            # Rewriting old data
            with open(JSON_BP_FILEPATH, "w") as f:
                f.write(old_spec_data)

        self._test_json_bp_delete()

    def _test_dsl_bp_delete(self):
        runner = CliRunner()
        LOG.info("Deleting DSL Bp {} ".format(self.created_dsl_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_dsl_bp_name])
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

    def _test_json_bp_delete(self):
        runner = CliRunner()
        LOG.info("Deleting JSON Bp {} ".format(self.created_json_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_json_bp_name])
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


if __name__ == "__main__":
    tester = TestBpCommands()
