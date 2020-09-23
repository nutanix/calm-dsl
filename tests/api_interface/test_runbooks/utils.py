import os
import time
import uuid
import pytest
import json


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
