import pytest
import sys
import json
import time
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.log import get_logging_handle

# Setting the recursion limit to max for
sys.setrecursionlimit(100000)

LOG = get_logging_handle(__name__)

SIMPLE_BP_FILE_PATH = "tests/simple_blueprint/test_simple_blueprint.py"
SIMPLE_BP_OUT_PATH = "tests/simple_blueprint/test_simple_blueprint.json"


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

    def test_create_bp(self):

        runner = CliRunner()
        created_dsl_bp_name = "Test_Simple_DSL_BP_{}".format(int(time.time()))
        LOG.info("Creating Bp {}".format(created_dsl_bp_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(SIMPLE_BP_FILE_PATH),
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

    def test_compile(self):

        runner = CliRunner()
        LOG.info("Compiling bp at {}".format(SIMPLE_BP_FILE_PATH))
        result = runner.invoke(
            cli, ["-vv", "compile", "bp", "--file={}".format(SIMPLE_BP_FILE_PATH)]
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
        known_json = json.loads(open(SIMPLE_BP_OUT_PATH).read())

        assert generated_json == known_json
