import os
import uuid
import json
import shutil
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.builtins import read_local_file, get_valid_identifier
from calm.dsl.decompile.file_handler import get_bp_dir
from calm.dsl.decompile import init_decompile_context
from calm.dsl.log import get_logging_handle

from calm.dsl.cli.bps import (
    get_blueprint_module_from_file,
    get_blueprint_class_from_module,
)

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
        LOG.info("Compiling Blueprint file at {}".format(bp_file_location))
        result = runner.invoke(cli, ["-vv", "compile", "bp", "-f", bp_file_location])
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
        LOG.info(
            "Creating Blueprint '{}' from file at {}".format(bp_name, bp_file_location)
        )
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
        # Decompiling the created bp and storing secrets in file
        LOG.info("Decompiling Blueprint {}".format(bp_name))
        cli_inputs = [CRED_PASSWORD, CRED_PASSWORD, CRED_PASSWORD]
        result = runner.invoke(
            cli,
            ["decompile", "bp", bp_name, "--with_secrets"],
            input="\n".join(cli_inputs),
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
        LOG.info(
            "Compiling decompiled blueprint file at {}".format(
                decompiled_bp_file_location
            )
        )
        result = runner.invoke(
            cli, ["-vv", "compile", "bp", "-f", decompiled_bp_file_location]
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

        LOG.info("Comparing original and decompiled blueprint json")
        assert bp_json == decompiled_bp_json
        LOG.info("Success")

        # Deleting old bp directory
        shutil.rmtree(self.bp_dir_list.pop())

        # Resetting context for decompiling
        init_decompile_context()

        self._test_decompile_with_prefix(bp_name)

    def _test_decompile_with_prefix(self, bp_name):

        runner = CliRunner()

        # Decompiling the created bp and storing secrets in file with prefix
        prefix = get_valid_identifier("_{}".format(str(uuid.uuid4())[:10]))
        LOG.info(
            "Decompiling Blueprint {} with prefix flag set to '{}'".format(
                bp_name, prefix
            )
        )

        cli_inputs = [CRED_PASSWORD, CRED_PASSWORD, CRED_PASSWORD]
        result = runner.invoke(
            cli,
            ["decompile", "bp", bp_name, "--with_secrets", "-p", prefix],
            input="\n".join(cli_inputs),
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
        decompiled_bp_file_location = os.path.join(get_bp_dir(), "blueprint.py")

        user_bp_module = get_blueprint_module_from_file(decompiled_bp_file_location)
        UserBlueprint = get_blueprint_class_from_module(user_bp_module)

        LOG.info("Asserting prefix in the entity names")
        for svc in UserBlueprint.services:
            assert svc.__name__.startswith(prefix)

        for pkg in UserBlueprint.packages:
            assert pkg.__name__.startswith(prefix)

        for sub in UserBlueprint.substrates:
            assert sub.__name__.startswith(prefix)
            assert sub.provider_spec.__name__.startswith(prefix)
            assert sub.provider_spec.resources.__name__.startswith(prefix)

        for pfl in UserBlueprint.profiles:
            assert pfl.__name__.startswith(prefix)

            for dep in pfl.deployments:
                assert dep.__name__.startswith(prefix)

        LOG.info("Success")

        # Resetting context for decompiling
        init_decompile_context

        # On applying prefix, name of dsl classes will be changed but UI name will be preserved
        # So compiled payload should be same

        bp_file_location = os.path.join(os.getcwd(), BP_FILE)
        LOG.info("Compiling original blueprint file at {}".format(bp_file_location))
        result = runner.invoke(cli, ["-vv", "compile", "bp", "-f", bp_file_location])
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

        LOG.info(
            "Compiling decompiled blueprint file having entity names with prefix at {}".format(
                decompiled_bp_file_location
            )
        )
        result = runner.invoke(
            cli, ["-vv", "compile", "bp", "-f", decompiled_bp_file_location]
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

        # POP out the client attrs, as they will be changed due to prefix
        bp_json["spec"]["resources"].pop("client_attrs", {})
        decompiled_bp_json["spec"]["resources"].pop("client_attrs", {})

        LOG.info("Comparing original and decompiled blueprint json")
        assert bp_json == decompiled_bp_json
        LOG.info("Success")
