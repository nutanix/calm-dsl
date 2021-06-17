import pytest
import time
import os
import json
import traceback
from click.testing import CliRunner
import uuid

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


DSL_BP_FILEPATH = "tests/existing_vm_example/test_existing_vm_bp.py"
JSON_BP_FILEPATH = "tests/existing_vm_example/test_existing_vm_bp.json"

BLUEPRINT_ERROR_MSG = {
    "AHV": {
        "DISK_NOT_ADDED": "Atleast one of the disk is required"
    },
    "VMW": {
        "NON_INTEGER_MEMORY": "memory_size_mib should be an integer (minimum 1)"
    }
}


@pytest.mark.slow
class TestBpCommands:
    def test_bps_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps"])
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
            pytest.fail("BP Get failed")
        LOG.info("Success")

    def test_bps_list_with_limit_offset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps", "--limit=15", "--offset=5"])
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
            pytest.fail("BP list with limit call failed")
        LOG.info("Success")

    def test_bps_list_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps", "--name=MSSQL"])
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
            pytest.fail("BP list with name call failed")
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
        self.created_dsl_bp_name = "Test_Existing_VM_DSL_{}".format(int(time.time()))
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
        self._test_bp_describe()

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

    def _test_bp_describe(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "bp", self.created_dsl_bp_name])
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
        self._test_dsl_bp_delete()

    def test_random_bp_describe(self):
        runner = CliRunner()
        LOG.info("Running 'calm describe bp' command")
        bp_name = "MySQL_ {}".format(int(time.time()))
        result = runner.invoke(cli, ["describe", "bp", bp_name])
        LOG.debug("Command output : {}".format(result.output))
        if result.exit_code != 0:
            assert result.exception.args[
                0
            ] == "No blueprint found with name {} found".format(bp_name)
        else:
            assert result.exit_code == 0
        LOG.info("Success")

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

    def test_blueprint_draft_reason_cli(self):
        """
        Metadata:
         Summary: This test verifies whether the draft state blueprint reason is shown on cli or not
         Priority: $P1
         Components: [BLUEPRINTS]
         Requirements: [CALM-14018]
         Steps:
           - 1) Create a bp using DSL.
           - 2) Add AHV service and don't add any boot disk
           - 3) Add vmware service and assign memory to zero
           - 4) Save the blueprint
           - 5) Validate the cli response
           - ExpectedResults
             - Api response for blueprint going to draft state must be shown on cli.
        """
        bp_dsl_file = "tests/cli/blueprints/bp_with_platform_validation_errors.py"
        dsl_bp_name = "blueprint_draft_state_{}".format(str(uuid.uuid4())[-10:])
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_dsl_file),
                "--name={}".format(dsl_bp_name)
            ],
            catch_exceptions=True
        )
        if not result.exit_code:
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
            pytest.fail("Blueprint got created with validation errors")

        assert BLUEPRINT_ERROR_MSG["AHV"]['DISK_NOT_ADDED'] in result.output and\
               BLUEPRINT_ERROR_MSG["VMW"]['NON_INTEGER_MEMORY'] in result.output, \
            "failed to get blueprint error reason on cli"


if __name__ == "__main__":
    tester = TestBpCommands()
