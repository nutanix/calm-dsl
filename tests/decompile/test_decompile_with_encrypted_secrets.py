import os
import uuid
import json
import shutil
import traceback
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.decompile.file_handler import get_bp_dir
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

ENCRYPTED_SECRETS_BP_DIRECTORY_PATH = os.path.join(
    os.getcwd(), "tests/decompile/example_bp_for_decompile_with_encrypted_secrets"
)
PASSPHRASE = "test_passphrase"
SECRETS_PATH_LIST = [
    ["credential_definition_list", 0],
    ["service_definition_list", 0, "variable_list", 0],
    ["service_definition_list", 0, "action_list", 6, "runbook", "variable_list", 0],
    [
        "service_definition_list",
        0,
        "action_list",
        7,
        "runbook",
        "task_definition_list",
        1,
        "attrs",
        "headers",
        0,
    ],
    ["service_definition_list", 1, "action_list", 6, "runbook", "variable_list", 0],
    [
        "service_definition_list",
        1,
        "action_list",
        6,
        "runbook",
        "task_definition_list",
        1,
        "attrs",
        "headers",
        0,
    ],
    ["app_profile_list", 0, "action_list", 0, "runbook", "variable_list", 0],
]


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

    def remove_secret_values(self, bp_payload):
        for path in SECRETS_PATH_LIST:
            secret = bp_payload
            for sub_path in path:
                secret = secret[sub_path]
            if path[0] == "credential_definition_list":
                secret = secret["secret"]
            secret["value"] = ""

    def test_bp_payload_with_encrypted_secrets(self):
        """Tests whether compiled payload of decompiled blueprint is same as normal blueprint"""

        runner = CliRunner()

        os.makedirs(ENCRYPTED_SECRETS_BP_DIRECTORY_PATH + "/.local")

        os.rename(
            ENCRYPTED_SECRETS_BP_DIRECTORY_PATH + "/decompiled_secrets.bin",
            ENCRYPTED_SECRETS_BP_DIRECTORY_PATH + "/.local/decompiled_secrets.bin",
        )

        bp_file_location = ENCRYPTED_SECRETS_BP_DIRECTORY_PATH + "/blueprint.py"
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
        bp_json = json.loads(json.dumps(bp_json, sort_keys=True))

        # Fetch project used for compilation
        project_name = bp_json["metadata"]["project_reference"].get("name")

        # Creating BP
        bp_name = "Test_BP_{}".format(str(uuid.uuid4()))
        LOG.info(
            "Creating Blueprint '{}' from file at {}".format(bp_name, bp_file_location)
        )
        result = runner.invoke(
            cli,
            [
                "create",
                "bp",
                "--file={}".format(bp_file_location),
                "--name={}".format(bp_name),
                "--passphrase={}".format(PASSPHRASE),
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

        # Update project in context to be used for decompilation
        ContextObj = get_context()
        ContextObj.update_project_context(project_name=project_name)

        self.created_bp_list.append(bp_name)
        # Decompiling the created bp and storing secrets in file
        LOG.info("Decompiling Blueprint {}".format(bp_name))
        result = runner.invoke(
            cli,
            ["decompile", "bp", bp_name, "--passphrase={}".format(PASSPHRASE)],
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

        decompiled_bp_json = json.loads(json.dumps(decompiled_bp_json, sort_keys=True))

        LOG.info("Comparing original and decompiled blueprint json")

        self.remove_secret_values(bp_json["spec"]["resources"])
        self.remove_secret_values(decompiled_bp_json["spec"]["resources"])

        assert bp_json == decompiled_bp_json
        LOG.info("Success")

        # Deleting old bp directory
        shutil.rmtree(self.bp_dir_list.pop())

        os.rename(
            ENCRYPTED_SECRETS_BP_DIRECTORY_PATH + "/.local/decompiled_secrets.bin",
            ENCRYPTED_SECRETS_BP_DIRECTORY_PATH + "/decompiled_secrets.bin",
        )

        os.rmdir(ENCRYPTED_SECRETS_BP_DIRECTORY_PATH + "/.local")
