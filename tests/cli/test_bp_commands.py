import pytest
import time
import os
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


DSL_BP_FILEPATH = "tests/existing_vm_example/test_existing_vm_bp.py"
JSON_BP_FILEPATH = "tests/existing_vm_example/test_existing_vm_bp.json"


@pytest.mark.slow
class TestBpCommands:
    def test_bps_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps"])
        assert result.exit_code == 0
        if result.exit_code:
            pytest.fail("BP Get failed")
        print(result.output)

    def test_bps_list_with_limit_offset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps", "--limit=15", "--offset=5"])
        assert result.exit_code == 0
        print(result.output)

    def test_bps_list_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get", "bps", "--name=MSSQL"])
        assert result.exit_code == 0
        print(result.output)

    def test_compile_bp(self):
        runner = CliRunner()
        LOG.info("Compiling Bp file at {}".format(DSL_BP_FILEPATH))
        result = runner.invoke(
            cli, ["compile", "bp", "--file={}".format(DSL_BP_FILEPATH)]
        )

        assert result.exit_code == 0

    def test_dsl_bp_create(self):
        runner = CliRunner()
        self.created_dsl_bp_name = "Test_Exisisting_VM_DSL_{}".format(int(time.time()))
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

        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response: {}".format(result.output))
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
                "calm -v CRITICAL compile bp --file={} > {}".format(
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
            )
            assert result.exit_code == 0
            LOG.info("Success")
            LOG.debug("Response: {}".format(result.output))

        finally:
            # Rewriting old data
            with open(JSON_BP_FILEPATH, "w") as f:
                f.write(old_spec_data)

        self._test_json_bp_delete()

    def _test_bp_describe(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["describe", "bp", self.created_dsl_bp_name])
        assert result.exit_code == 0
        self._test_dsl_bp_delete()

    def test_random_bp_describe(self):
        runner = CliRunner()
        LOG.info("Running 'calm describe bp' command")
        result = runner.invoke(cli, ["describe", "bp", "MySQL"])
        if result.exit_code != 0:
            assert (
                result.exception.args[0]
                == "No blueprint found with name MySQL found >>"
            )
        else:
            assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Command output : {}".format(result.output))

    def _test_dsl_bp_delete(self):
        runner = CliRunner()
        LOG.info("Deleting DSL Bp {} ".format(self.created_dsl_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_dsl_bp_name])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response : {}".format(result.output))

    def _test_json_bp_delete(self):
        runner = CliRunner()
        LOG.info("Deleting JSON Bp {} ".format(self.created_json_bp_name))
        result = runner.invoke(cli, ["delete", "bp", self.created_json_bp_name])
        assert result.exit_code == 0
        LOG.info("Success")
        LOG.debug("Response : {}".format(result.output))


if __name__ == "__main__":
    tester = TestBpCommands()
