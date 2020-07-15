import os
import uuid
import json
import shutil
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.builtins import read_local_file
from calm.dsl.decompile.file_handler import get_bp_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

BP_FILE = "tests/decompile/test_decompile.py"
CRED_PASSWORD = read_local_file(".tests/password")


class TestDecompile:
    def setup_method(self):
        self.created_bp_list = []
        self.bp_dir_list = []

    def teardown_method(self):
        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        for dir_location in self.bp_dir_list:
            shutil.rmtree(dir_location)

    def test_bp_payload_roundtrip(self):
        """Tests whether compiled payload of decompiled blueprint is same as normal blueprint"""

        runner = CliRunner()

        bp_file_location = os.path.join(os.getcwd(), BP_FILE)
        LOG.info("Creating Blueprint at {}".format(bp_file_location))
        result = runner.invoke(cli, ["-vvvvv", "compile", "bp", "-f", bp_file_location])
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
        bp_json = json.loads(result.output)

        # Creating BP
        bp_name = "Test_BP_{}".format(str(uuid.uuid4()))
        result = runner.invoke(
            cli, ["create", "bp", "-f", bp_file_location, "-n", bp_name]
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

        self.created_bp_list.append(bp_name)
        # Decompiling the cerated bp and storing secrets in file
        LOG.info("Decompiling Blueprint {}".format(bp_name))
        input = [CRED_PASSWORD]
        result = runner.invoke(
            cli, ["decompile", "bp", bp_name, "--with_secrets"], input="\n".join(input)
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

        self.bp_dir_list.append(get_bp_dir())
        # TODO add interface check tests
        decompiled_bp_file_location = os.path.join(get_bp_dir(), "blueprint.py")
        LOG.info("Compiling Blueprint at {}".format(decompiled_bp_file_location))
        result = runner.invoke(
            cli, ["-vvvvv", "compile", "bp", "-f", decompiled_bp_file_location]
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

        decompiled_bp_json = json.loads(result.output)
        # We don't have paramter to pass name of blueprint during compile right now
        # So compare everythin else other than blueprint name
        decompiled_bp_json["metadata"]["name"] = bp_json["metadata"]["name"]
        decompiled_bp_json["spec"]["name"] = bp_json["spec"]["name"]

        assert bp_json == decompiled_bp_json
