import json
import os
import traceback
import pytest
import uuid
from click.testing import CliRunner

from calm.dsl.cli import main as cli
from calm.dsl.builtins import read_local_file
from tests.utils import Application as ApplicationHelper
from calm.dsl.cli.main import get_api_client
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_AZ = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]

LINUX_ENDPOINT_BASIC_CRED_FILE = os.path.abspath(
    "tests/unit/run_script/endpoints/linux_endpoint_with_basic_cred.py"
)
LINUX_ENDPOINT_SSH_CRED_FILE = os.path.abspath(
    "tests/unit/run_script/endpoints/linux_endpoint_with_ssh_cred.py"
)
WINDOWS_ENDPOINT_BASIC_CRED_FILE = os.path.abspath(
    "tests/unit/run_script/endpoints/windows_endpoint_with_basic_cred.py"
)

ESCRIPT_FILE = os.path.abspath("tests/unit/run_script/scripts/escript.py")
SHELL_SCRIPT_FILE = os.path.abspath("tests/unit/run_script/scripts/shell_script.sh")
POWERSHELL_SCRIPT_FILE = os.path.abspath(
    "tests/unit/run_script/scripts/powershell_script.ps1"
)

BP_FILE_PATH = os.path.abspath("tests/unit/run_script/blueprint.py")


class TestRunScriptCommands:
    app_helper = ApplicationHelper()

    @classmethod
    def setup_class(cls):
        runner = CliRunner()
        cls.app_name = "Test_DSL_App_Run_Script_" + str(uuid.uuid4())[-10:]
        LOG.info("Creating app {} for ssh target machine".format(cls.app_name))
        result = runner.invoke(
            cli,
            [
                "create",
                "app",
                "--file={}".format(BP_FILE_PATH),
                "--name={}".format(cls.app_name),
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

        cls.app_helper._wait_for_non_busy_state(cls.app_name)
        params = {"filter": "name=={}".format(cls.app_name)}
        client = get_api_client()
        res, err = client.application.list(params=params)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        response = res.json()
        entities = response.get("entities", None)
        app = None
        if entities:
            app = entities[0]
        else:
            pytest.fail("Application {} not found".format(cls.app_name))

        app_uuid = app["metadata"]["uuid"]
        res, err = client.application.read(app_uuid)
        if err:
            pytest.fail(err)
        response = res.json()
        # Reading ip address of app created
        cls.ip_address = response["status"]["resources"]["deployment_list"][0][
            "substrate_configuration"
        ]["element_list"][0].get("address", "")
        if not cls.ip_address:
            pytest.fail(
                "Unable to find ip address of application {}".format(cls.app_name)
            )

        LOG.info(
            "Setting linux machine ip address {} in endpoint file: {}".format(
                cls.ip_address, LINUX_ENDPOINT_SSH_CRED_FILE
            )
        )
        with open(LINUX_ENDPOINT_SSH_CRED_FILE, "r") as fd:
            data = fd.read()
            data = data.replace(
                'linux_ip = ""', "linux_ip = '{}'".format(cls.ip_address)
            )

        with open(LINUX_ENDPOINT_SSH_CRED_FILE, "w+") as fd:
            fd.write(data)

    @classmethod
    def teardown_class(cls):
        runner = CliRunner()

        LOG.info("Restoring endpoint file: {}".format(LINUX_ENDPOINT_SSH_CRED_FILE))
        with open(LINUX_ENDPOINT_SSH_CRED_FILE, "r") as fd:
            data = fd.read()
            data = data.replace(
                "linux_ip = '{}'".format(cls.ip_address), 'linux_ip = ""'
            )

        with open(LINUX_ENDPOINT_SSH_CRED_FILE, "w+") as fd:
            fd.write(data)

        cls.app_helper._wait_for_non_busy_state(cls.app_name)
        LOG.info("Deleting App {} ".format(cls.app_name))
        result = runner.invoke(cli, ["delete", "app", cls.app_name])
        assert result.exit_code == 0
        LOG.info("App {} deleted successfully".format(cls.app_name))

    @pytest.mark.parametrize(
        "SCRIPT_TYPE, " "SCRIPT_FILE, ENDPOINT_FILE",
        [
            pytest.param("escript", ESCRIPT_FILE, None),
            pytest.param("shell", SHELL_SCRIPT_FILE, LINUX_ENDPOINT_BASIC_CRED_FILE),
            pytest.param("shell", SHELL_SCRIPT_FILE, LINUX_ENDPOINT_SSH_CRED_FILE),
            pytest.param(
                "powershell", POWERSHELL_SCRIPT_FILE, WINDOWS_ENDPOINT_BASIC_CRED_FILE
            ),
            pytest.param("python", ESCRIPT_FILE, LINUX_ENDPOINT_BASIC_CRED_FILE),
        ],
    )
    def test_scripts(self, SCRIPT_TYPE, SCRIPT_FILE, ENDPOINT_FILE):
        """
        Tests `calm run-script` cli command for following cases:
        -> Successful run of escript file
        -> Successful run of shell script file with basic auth linux endpoint
        -> Successful run of shell script file with ssh key based linux endpoint
        -> Successful run of powershell script file with basic auth windows endpoint
        -> Successful run of python remote script file with basic auth linux endpoint

        Note:
        -> Python remote tasks don't run on windows endpoint.
        -> Windows endpoint only have basic auth and no ssh based authentication.
        """
        runner = CliRunner()
        LOG.info("Running 'calm run-script' command for {} script".format(SCRIPT_TYPE))
        if SCRIPT_TYPE == "escript":
            LOG.info("Running 'calm run-script' command for {}".format(SCRIPT_TYPE))
            LOG.info("Script file used: {}".format(SCRIPT_FILE))
            result = runner.invoke(
                cli,
                [
                    "run-script",
                    "--type={}".format(SCRIPT_TYPE),
                    "--file={}".format(SCRIPT_FILE),
                ],
            )
        else:
            LOG.info(
                "Running 'calm run-script' command for {} script".format(SCRIPT_TYPE)
            )
            LOG.info(
                "Script file used: {}, Endpoint file used: {}".format(
                    SCRIPT_FILE, ENDPOINT_FILE
                )
            )
            result = runner.invoke(
                cli,
                [
                    "run-script",
                    "--type={}".format(SCRIPT_TYPE),
                    "--file={}".format(SCRIPT_FILE),
                    "--endpoint={}".format(ENDPOINT_FILE),
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

        assert "Status: SUCCESS" in result.output, "failed to test shell script"
