import os
import time
import uuid
from importlib_metadata import metadata
import pytest

import json
from calm.dsl.cli.constants import MARKETPLACE_ITEM
from calm.dsl.config import get_context
from calm.dsl.api import get_api_client


def change_uuids(bp, context):
    """
    Helper function to change uuids
    Args:
        bp (dict): BP dict
        context (dict) : context to recursively change uuid references
    """
    if isinstance(bp, dict):

        new_name = "Test_" + str(uuid.uuid4())[-10:]
        if bp.get("spec", None) and bp.get("metadata", None):
            bp["spec"]["name"] = new_name
            bp["metadata"]["name"] = new_name
        for key, val in bp.items():
            if key == "uuid":
                old_uuid = val
                if old_uuid in context.keys():
                    bp[key] = context[old_uuid]
                else:
                    new_uuid = str(uuid.uuid4())
                    context[old_uuid] = new_uuid
                    bp[key] = new_uuid
            else:
                change_uuids(val, context)
    elif isinstance(bp, list):
        for item in bp:
            if isinstance(item, str):
                try:
                    uuid.UUID(hex=str(item), version=4)
                except Exception:
                    change_uuids(item, context)
                    continue
                old_uuid = item
                if old_uuid in context.keys():
                    new_uuid = context[old_uuid]
                    bp[bp.index(item)] = new_uuid
                else:
                    new_uuid = str(uuid.uuid4())
                    context[old_uuid] = new_uuid
                    bp[bp.index(item)] = new_uuid
            else:
                change_uuids(item, context)
    return bp


def update_endpoints_name(rb, context):
    """
    Helper function to change uuids
    Args:
        rb (dict): Runbook dict
        context (dict) : context to recursively change endpoint's name reference
    """
    if isinstance(rb, dict):

        if rb.get("endpoint_definition_list", []):

            for endpoint in rb["endpoint_definition_list"]:
                old_name = endpoint["name"]
                endpoint["name"] = old_name + str(uuid.uuid4())[-10:]
                context[old_name] = endpoint["name"]

        for key, val in rb.items():
            if key == "name":
                if val in context.keys():
                    rb[key] = context[val]
            else:
                update_endpoints_name(val, context)
    elif isinstance(rb, list):
        for item in rb:
            update_endpoints_name(item, context)
    return rb


def upload_runbook(client, rb_name, Runbook):
    """
    This routine uploads the given runbook
    Args:
        client (obj): client object
        rb_name (str): runbook name
        Runbook (obj): runbook object
    Returns:
        dict: returns upload API call response
    """
    params = {"filter": "name=={};deleted==FALSE".format(rb_name)}
    res, err = client.runbook.list(params=params)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    entities = res.get("entities", None)
    print("\nSearching and deleting existing runbook having same name")
    if entities:
        if len(entities) != 1:
            pytest.fail("More than one runbook found - {}".format(entities))

        print(">> {} found >>".format(Runbook))
        rb_uuid = entities[0]["metadata"]["uuid"]

        res, err = client.runbook.delete(rb_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        print(">> {} deleted >>".format(Runbook))

    else:
        print(">> {} not found >>".format(Runbook))

    # uploading the runbook
    print("\n>>Creating the runbook {}".format(rb_name))
    rb_desc = "Runbook DSL Test automation"
    rb_resources = json.loads(Runbook.runbook.json_dumps())

    # update endpoint names for testing purporse as endpoints with duplicate names are not allowed
    rb_resources = update_endpoints_name(rb_resources, {})
    res, err = client.runbook.upload_with_secrets(rb_name, rb_desc, rb_resources)

    if not err:
        print(">> {} uploaded with creds >>".format(Runbook))
        assert res.ok is True
    else:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def poll_runlog_status(
    client, runlog_uuid, expected_states, poll_interval=10, maxWait=300
):
    """
    This routine polls for 5mins till the runlog gets into the expected state
    Args:
        client (obj): client object
        runlog_uuid (str): runlog id
        expected_states (list): list of expected states
    Returns:
        (str, list): returns final state of the runlog and reasons list
    """
    count = 0
    while count < maxWait:
        res, err = client.runbook.poll_action_run(runlog_uuid)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        state = response["status"]["state"]
        reasons = response["status"]["reason_list"]
        if state in expected_states:
            break
        count += poll_interval
        time.sleep(poll_interval)

    return state, reasons or []


def read_test_config(file_name="test_config.json"):
    """
    This routine returns dict for the json file
    Args:
        file_name(str): Name of the json file
    Returns:
        dict: json file in python dict format
    """

    current_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.dirname(current_path) + "/test_runbooks/test_files/%s" % (
        file_name
    )
    json_file = open(file_path)
    data = json.load(json_file)
    return data


def update_runbook(client, rb_name, Runbook):
    """
    This routine updates the given runbook
    Args:
        client (obj): client object
        rb_name (str): runbook name
        Runbook (obj): runbook object
    Returns:
        dict: returns updates API call response
    """
    params = {"filter": "name=={};deleted==FALSE".format(rb_name)}
    res, err = client.runbook.list(params=params)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    entities = res.get("entities", None)
    print("\nSearching and deleting existing runbook having same name")
    if entities:
        if len(entities) != 1:
            pytest.fail("More than one runbook found - {}".format(entities))

        print(">> {} found >>".format(Runbook))
        rb_uuid = entities[0]["metadata"]["uuid"]
        rb_spec_version = entities[0]["metadata"]["spec_version"]

    else:
        pytest.fail(">> {} not found >>".format(Runbook))

    # updating the runbook
    print("\n>>Updating the runbook {}".format(rb_name))
    rb_desc = "Runbook DSL Test automation"
    rb_resources = json.loads(Runbook.runbook.json_dumps())
    res, err = client.runbook.update_with_secrets(
        rb_uuid, rb_name, rb_desc, rb_resources, rb_spec_version
    )

    if not err:
        print(">> {} uploaded with creds >>".format(Runbook))
        assert res.ok is True
    else:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def poll_run_script_output(
    client,
    runbook_uuid,
    trl_id,
    request_id,
    expected_states,
    poll_interval=10,
    maxWait=150,
):
    """
    This routine polls for 5mins till the run script gets into the expected state
    Args:
        client (obj): client object
        runbook_uuid (str): runbook id
        trl_id (str): trl id
        rquest_id (str): request id
        expected_states (list): list of expected states
    Returns:
        (str, list): returns final state of the runlog and reasons list
    """
    count = 0
    while count < maxWait:
        res, err = client.runbook.run_script_output(runbook_uuid, trl_id, request_id)
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))
        response = res.json()
        state = response["state"]
        if state in expected_states:
            break
        count += poll_interval
        time.sleep(poll_interval)

    return state


def publish_runbook_to_marketplace_manager(
    client,
    runbook_uuid,
    marketplace_item_name,
    version,
    description="",
    with_secrets=False,
    with_endpoints=False,
    app_group_uuid=None,
    app_icon_uuid=None,
    icon_file=None,
):
    """
    This routine publish the runbook to the marketplace
    Args:
        client (obj): client object
        runbook_uuid (str): runbook id
        marketplace_item_name (str): name of marketplace item
        version (str): version for marketplace item
        description (str): description of marketplace item
        with_secrets (str): publish with secrets
        with_endpoints (str): publish with endpoints
        app_group_uuid (str): group uuid in case publishing new verion
        icon_file (str): icon file details
    Returns:
        response (obj): returns response of the publish api
        err (dict): error of operation
    """
    context = get_context()
    server_config = context.get_server_config()

    mpi_spec = {
        "spec": {
            "name": marketplace_item_name,
            "description": description,
            "resources": {
                "app_attribute_list": ["FEATURED"],
                "icon_reference_list": [],
                "author": server_config["pc_username"],
                "version": version,
                "type": MARKETPLACE_ITEM.TYPES.RUNBOOK,
                "app_group_uuid": app_group_uuid or str(uuid.uuid4()),
                "runbook_template_info": {
                    "is_published_with_secrets": with_secrets,
                    "is_published_with_endpoints": with_endpoints,
                    "source_runbook_reference": {
                        "uuid": runbook_uuid,
                        "kind": "runbook",
                    },
                },
            },
        },
        "api_version": "3.0",
        "metadata": {"kind": "marketplace_item"},
    }

    if app_icon_uuid:
        mpi_spec["spec"]["resources"]["icon_reference_list"] = [
            {
                "icon_type": "ICON",
                "icon_reference": {"kind": "file_item", "uuid": app_icon_uuid},
            }
        ]

    return client.market_place.create(mpi_spec)


def change_marketplace_state(client, mpi_uuid, new_state, project_list=None):
    """
    Change state of MPI and list of project it is shared it
    Args:
        client (obj): client object
        mpi_uuid (str): UUID of MPI
        new_state (str): New state of mpi
        project_list (list): list of project names
    Returns:
        response (obj): returns response of the update API
    """

    res, err = client.market_place.read(mpi_uuid)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    mpi_data = res.json()
    mpi_data.pop("status", None)
    mpi_data["spec"]["resources"]["app_state"] = new_state
    if project_list is not None:
        project_reference_list = []
        for project in project_list:
            project_params = {"filter": "name=={}".format(project)}
            res, err = client.project.list(params=project_params)
            if err:
                pytest.fail("[{}] - {}".format(err["code"], err["error"]))

            response = res.json()
            entities = response.get("entities", None)
            if not entities:
                raise Exception("No project with name {} exists".format(project))

            project_id = entities[0]["metadata"]["uuid"]
            project_reference_list.append(
                {"name": project, "uuid": project_id, "kind": "project"}
            )

        mpi_data["spec"]["resources"]["project_reference_list"] = project_reference_list

    res, err = client.market_place.update(uuid=mpi_uuid, payload=mpi_data)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    return res.json()


def clone_marketplace_runbook(client, mpi_uuid, runbook_name, project_name):
    """
    Clone MPI runbook in the given project
    Args:
        client (obj): client object
        mpi_uuid (str): UUID of MPI
        runbook_name (str): Nmme of runbook
        project_name (str): project name
    Returns:
        response (obj): returns response of the clone API
        err (dict): error of operation
    """
    payload = {
        "api_version": "3.0",
        "metadata": {"name": runbook_name, "kind": "runbook"},
        "spec": {
            "name": runbook_name,
            "resources": {
                "marketplace_reference": {"uuid": mpi_uuid, "kind": "marketplace_item"}
            },
        },
    }

    if project_name:
        project_id = get_project_id_from_name(client, project_name)
        if not project_id:
            raise Exception("No project with name {} exists".format(project_name))

        payload["metadata"]["project_reference"] = {
            "name": project_name,
            "uuid": project_id,
            "kind": "project",
        }

    return client.runbook.marketplace_clone(payload)


def execute_marketplace_runbook(
    client,
    mpi_uuid,
    project_name,
    default_endpoint_uuid=None,
    endpoints_mapping=None,
    args=None,
):
    """
    Execute MPI runbook in the given project
    Args:
        client (obj): client object
        mpi_uuid (str): UUID of MPI
        project_name (str): project name
        default_endpoint_uuid (str): default endpoint uuid that need to be used
        endpoints_mapping (dict): current endpoint and new endpoint mapping
        args (listt): list if runtime variables
    Returns:
        response (obj): returns response of the clone API
        err (dict): error of operation
    """

    project_id = get_project_id_from_name(client, project_name)
    if not project_id:
        raise Exception("No project with name {} exists".format(project_name))

    payload = {
        "api_version": "3.0",
        "metadata": {
            "project_reference": {
                "name": project_name,
                "uuid": project_id,
                "kind": "project",
            },
            "kind": "runbook",
        },
        "spec": {
            "resources": {
                "marketplace_reference": {"uuid": mpi_uuid, "kind": "marketplace_item"}
            }
        },
    }

    if args:
        payload["spec"]["resources"]["args"] = args

    if default_endpoint_uuid:
        payload["spec"]["resources"]["default_target_reference"] = {
            "uuid": default_endpoint_uuid,
            "kind": "app_endpoint",
        }

    if endpoints_mapping:
        payload["spec"]["resources"]["endpoints_mapping"] = endpoints_mapping

    return client.runbook.marketplace_execute(payload)


def get_project_id_from_name(client, project_name):
    """
    Helper function to get project if from name
    Args:
        client (obj): client object
        project_name (str): project name
    Returns:
        str: returns project name
    """

    project_params = {"filter": "name=={}".format(project_name)}
    res, err = client.project.list(params=project_params)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    response = res.json()
    project_entities = response.get("entities", None)
    project_id = None

    if project_entities:
        project_id = project_entities[0]["metadata"]["uuid"]

    return project_id


def validate_error_message(err, expected_message):
    """
    Helper function to validate error messages with expected error
    Args:
        error (dict): error
        expected_message (str): expected error message
    """
    message_list = err.get("message_list", [])
    found = False
    for message in message_list:
        if expected_message in message["message"].lower():
            found = True
            break

    if not found:
        pytest.fail(
            "Unable to found err {} in errors {}".format(expected_message, message_list)
        )


def get_runbook_dynamic_variable_values(runbook_uuid, var_uuid):
    """dynamic variable response"""

    client = get_api_client()

    # Get request and trl id
    res, err = client.market_place.variable_values(runbook_uuid, var_uuid=var_uuid)
    if err:
        pytest.fail("[{}] - {}".format(err["code"], err["error"]))

    res = res.json()
    var_payload = {"requestId": res["request_id"], "trlId": res["trl_id"]}
    count = 0
    while count < 10:
        res, err = client.market_place.variable_values(
            runbook_uuid, var_uuid=var_uuid, payload=var_payload
        )
        if err:
            pytest.fail("[{}] - {}".format(err["code"], err["error"]))

        res = res.json()
        var_state = res["state"]
        if var_state == "SUCCESS":
            return res["values"]
        count += 1
        print(">> Dynamic variable state: {}".format(var_state))
        time.sleep(10)

    return []


def update_tunnel_and_project(tunnel_reference, project, endpoint_payload):
    metadata = endpoint_payload["metadata"]
    if metadata.get("project_reference", {}):
        metadata["project_reference"]["name"] = project.get("name")
        metadata["project_reference"]["uuid"] = project.get("uuid")

    resources = endpoint_payload["spec"]["resources"]
    if resources.get("tunnel_reference", {}):
        resources["tunnel_reference"]["uuid"] = tunnel_reference.get("uuid")
        resources["tunnel_reference"]["name"] = tunnel_reference.get("name")
