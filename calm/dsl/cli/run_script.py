import uuid
import sys
import time
import click
import os

from .utils import highlight_text
from calm.dsl.api import get_api_client
from calm.dsl.builtins import Ref
from calm.dsl.builtins.models.helper import common as common_helper
from calm.dsl.cli.constants import TEST_SCRIPTS
from calm.dsl.log import get_logging_handle
from calm.dsl.cli.endpoints import compile_endpoint
from calm.dsl.cli.tunnels import get_tunnel
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)


def test_scripts_type():
    """Provides the list of scripts that can be run in playground"""
    return TEST_SCRIPTS.TYPE


def _display_script_run_status(state, response):
    """Displays the script run status on the console.

    Args:
        -> state (str): state of the script run
        -> response (dict): response of the script run

    """
    if not (state or response):
        LOG.error("Unable to fetch proper api response")
        sys.exit(-1)

    LOG.info("Script execution reached state: {}".format(state))

    status_code = str(response.get("code", ""))

    if state == TEST_SCRIPTS.STATUS.ERROR:
        response = response.get("error", response)

    message_list = response.get("message_list", [])
    message = response.get("message", "")
    reason = ""
    final_output = ""

    if message_list:
        if message_list[0].get("details", {}):
            final_output = message_list[0]["details"].get("final_output", "")
        message = message_list[0].get("message", "")
        reason = message_list[0].get("reason", "")
        LOG.debug(
            "Script execution failed. Status code: {} reason: {}".format(
                status_code, message_list
            )
        )
    else:
        final_output = response.get("output", "")

    click.echo("\n----Script Run Summary----\n")
    click.echo("Status: " + highlight_text(state))
    if final_output:
        click.echo("Final Output: " + final_output)
    if status_code:
        click.echo("Status Code: " + status_code)
    if message:
        click.echo("Message: " + message)
    if reason:
        click.echo("Reason: " + reason)


def _poll_test_scripts(bp_uuid, trl_id, request_id, poll_interval=5, maxWait=500):
    """Polls the test script status for every poll_interval seconds until maxWait seconds.

    Args:
        -> bp_uuid (str): blueprint uuid
        -> trl_id (str): trl id
        -> request_id (str): request id
        -> poll_interval (int): interval in seconds to poll the status
        -> maxWait (int): maximum time to wait for the script to complete
    """
    client = get_api_client()
    count = 0
    status = None
    response = {}

    while count < maxWait:
        LOG.info("Polling to get script run status")
        res, err = client.blueprint.test_scripts(bp_uuid, trl_id, request_id)
        if err:
            return err["error"].get("state", TEST_SCRIPTS.STATUS.ERROR), err

        response = res.json()
        status = response.get("state", None)

        if status and status in TEST_SCRIPTS.TERMINAL_STATES:
            return status, response

        count += poll_interval
        time.sleep(poll_interval)

    return status, response


def _run_script(bp_uuid, payload):
    """Fetches trl_id and request_id required to run script on target machine and then runs it on target machine.
    Args:
        -> bp_uuid (str): blueprint uuid
        -> payload (dict): payload to run the script

    Returns:
        -> status and response of script run
    """
    client = get_api_client()
    res, err = client.blueprint.run_scripts(bp_uuid, payload)

    if err:
        LOG.error(
            "Script run failed due to: [{}] - {}".format(err["code"], err["error"])
        )
        sys.exit("Script run failed")

    response = res.json()
    trl_id = None
    request_id = None

    if response.get("status", {}):
        trl_id = response["status"].get("trl_id", None)
        request_id = response["status"].get("request_id", None)

    return _poll_test_scripts(bp_uuid, trl_id, request_id)


def _test_script(script_type, script_file, endpoint_file, project_name):
    """Constructs payload required to test script run and displays it on console
    Args:
        -> script_type (str): type of script to run
        -> script_file (str): path to script file
        -> endpoint_file (str): path to endpoint file
        -> project_name (optional) (str): name of the reference project
    """
    EndpointPayload = compile_endpoint(endpoint_file)

    endpoint_attrs = EndpointPayload["spec"]["resources"].get("attrs", {})

    if not endpoint_attrs:
        LOG.error("Endpoint attributes not found in the endpoint file")
        sys.exit(-1)

    machine = None
    cred_name = None
    username = None
    password = None
    secret = {}
    protocol = endpoint_attrs.get("connection_protocol", None)
    port = endpoint_attrs.get("port", None)

    if endpoint_attrs.get("values", []):
        machine = endpoint_attrs["values"][0]
    else:
        LOG.error("Target VM IP not found in the endpoint file")
        sys.exit(-1)

    if endpoint_attrs.get("credential_definition_list", []):
        username = endpoint_attrs["credential_definition_list"][0].get("username", None)
        cred_type = endpoint_attrs["credential_definition_list"][0].get("type", "")
        if cred_type == "KEY":
            secret = endpoint_attrs["credential_definition_list"][0].get("secret", {})
            cred_name = endpoint_attrs["credential_definition_list"][0].get("name", "")
        else:
            password = (
                endpoint_attrs["credential_definition_list"][0]
                .get("secret", {})
                .get("value", None)
            )

    with open(os.path.abspath(script_file), "r") as scriptf:
        script_data = scriptf.read().strip()
        if script_data.startswith('"') and script_data.endswith('"'):
            script_data = script_data[1:-1]

    # attach project from current context if no project is supplied
    if not project_name:
        project_cache_data = common_helper.get_cur_context_project()
        project_name = project_cache_data.get("name")

    project_ref = Ref.Project(project_name)
    bp_uuid = str(uuid.uuid4())

    payload = {
        "metadata": {
            "kind": "blueprint",
            "project_reference": project_ref,
            "uuid": bp_uuid,
        },
        "spec": {
            "targetDetails": {
                "from_blueprint": False,
                "port": port,
                "machine": machine,
                "loginDetails": {},
            },
            "attrs": {
                "script_type": script_type,
                "script": script_data,
            },
        },
    }

    # Connection Protocol are only present in windows endpoints. Two valid protocols are HTTP and HTTPS.
    if protocol:
        payload["spec"]["targetDetails"]["protocol"] = protocol

    if secret:
        payload["spec"]["targetDetails"]["from_blueprint"] = True
        payload["spec"]["targetDetails"]["creds"] = {
            "username": username,
            "secret": secret,
            "cred_class": "static",
            "type": cred_type,
            "name": cred_name,
            "uuid": str(uuid.uuid4()),
        }
    else:
        payload["spec"]["targetDetails"]["loginDetails"] = {
            "username": username,
            "password": password,
        }

    state, response = _run_script(bp_uuid, payload)
    _display_script_run_status(state, response)


def test_escript(script_file, project_name, tunnel_name=""):
    """Tests the execution of escript file
    Args:
        -> script_file (str): path to escript file
        -> project_name (optional) (str): name of the reference project
        -> tunnel_name (optional) (str): name of the tunnel to use for script execution
    """
    with open(os.path.abspath(script_file), "r") as scriptf:
        script_data = scriptf.read()

    # Retrieving tunnel information if a tunnel is specified.
    tunnel_ref = None
    if tunnel_name:
        client = get_api_client()
        tunnel = get_tunnel(client, tunnel_name)
        kind = tunnel.get("metadata", {}).get("kind", None)
        if kind == CACHE.ENTITY.TUNNEL:
            tunnel_ref = Ref.Tunnel.Account(name=tunnel_name)
        else:
            tunnel_ref = Ref.Tunnel.VPC(name=tunnel_name)

    # attach project from current context if no project is supplied
    if not project_name:
        project_cache_data = common_helper.get_cur_context_project()
        project_name = project_cache_data.get("name")

    project_ref = Ref.Project(project_name)
    bp_uuid = str(uuid.uuid4())

    payload = {
        "metadata": {
            "kind": "blueprint",
            "project_reference": project_ref,
            "uuid": bp_uuid,
        },
        "spec": {
            "targetDetails": {"from_blueprint": False},
            "attrs": {
                "script_type": "static_py3",
                "script": script_data,
            },
        },
    }
    if tunnel_ref:
        payload["spec"]["targetDetails"]["tunnel_reference"] = tunnel_ref.get_dict()

    state, response = _run_script(bp_uuid, payload)
    _display_script_run_status(state, response)


def test_python_script(script_file, endpoint_file, project_name):
    """Tests the execution of python remote scripts on linux machine
    Args:
        -> script_file (str): path to script file
        _> endpoint_file (str): path to endpoint file
        -> project_name (optional) (str): name of the reference project
    """
    _test_script("python_remote", script_file, endpoint_file, project_name)


def test_shell_script(script_file, endpoint_file, project_name):
    """Tests the execution of shell scripts on linux machine
    Args:
        -> script_file (str): path to script file
        _> endpoint_file (str): path to endpoint file
        -> project_name (optional) (str): name of the reference project
    """
    _test_script("sh", script_file, endpoint_file, project_name)


def test_powershell_script(script_file, endpoint_file, project_name):
    """Tests the execution of powershell scripts on windows machine
    Args:
        -> script_file (str): path to script file
        _> endpoint_file (str): path to endpoint file
        -> project_name (optional) (str): name of the reference project
    """
    _test_script("npsscript", script_file, endpoint_file, project_name)
