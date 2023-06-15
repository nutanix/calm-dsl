import os
import uuid
import json
import shutil
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.builtins import read_local_file
from calm.dsl.decompile.file_handler import get_bp_dir
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.decompile import init_decompile_context


LOG = get_logging_handle(__name__)

BP_FILE = "tests/decompile/test_task_tree_bp.py"
CRED_PASSWORD = read_local_file(".tests/password")


class TestDecompile:
    def setup_method(self):
        self.created_bp_list = []
        self.bp_dir_list = []
        init_decompile_context()

    def teardown_method(self):
        for bp_name in self.created_bp_list:
            LOG.info("Deleting Blueprint {}".format(bp_name))
            runner = CliRunner()
            result = runner.invoke(cli, ["delete", "bp", bp_name])
            assert result.exit_code == 0

        for dir_location in self.bp_dir_list:
            shutil.rmtree(dir_location)

    def test_task_tree_bp(self):
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

        # Fetch project used for compilation
        project_name = bp_json["metadata"]["project_reference"].get("name")

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

        # Update project in context to be used for decompilation
        ContextObj = get_context()
        ContextObj.update_project_context(project_name=project_name)

        self.created_bp_list.append(bp_name)
        # Decompiling the created bp and storing secrets in file
        LOG.info("Decompiling Blueprint {}".format(bp_name))
        cli_inputs = [CRED_PASSWORD]
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

        bp_json_edge_list = (
            bp_json.get("spec", {})
            .get("resources", {})
            .get("package_definition_list", [{}])[0]
            .get("options", {})
            .get("uninstall_runbook", {})
            .get("task_definition_list", [{}])[0]
            .get("attrs", {})
            .get("edges", [])
        )

        decompiled_bp_json_edge_list = (
            decompiled_bp_json.get("spec", {})
            .get("resources", {})
            .get("package_definition_list", [{}])[0]
            .get("options", {})
            .get("uninstall_runbook", {})
            .get("task_definition_list", [{}])[0]
            .get("attrs", {})
            .get("edges", [])
        )

        sorted_bp_json_edge_list = sorted(
            bp_json_edge_list,
            key=lambda edge: (
                edge["from_task_reference"]["name"],
                edge["to_task_reference"]["name"],
            ),
        )
        sorted_decompiled_bp_json_edge_list = sorted(
            decompiled_bp_json_edge_list,
            key=lambda edge: (
                edge["from_task_reference"]["name"],
                edge["to_task_reference"]["name"],
            ),
        )

        LOG.info("Comparing original and decompiled edge list")
        assert sorted_bp_json_edge_list == sorted_decompiled_bp_json_edge_list
        LOG.info("Success")

        # Deleting old bp directory
        shutil.rmtree(self.bp_dir_list.pop())
