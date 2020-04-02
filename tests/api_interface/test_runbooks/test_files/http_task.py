"""
Calm Runbook Sample for running http tasks
"""
import json

from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmEndpoint, Auth, ref
from calm.dsl.config import get_config
from utils import read_test_config, change_uuids

AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
URL = read_local_file(".tests/runbook_tests/url")

config = get_config()
TEST_URL = "https://{}:9440/".format(config["SERVER"]["pc_ip"])

endpoint = CalmEndpoint.HTTP(URL, verify=False, auth=Auth.Basic(AUTH_USERNAME, AUTH_PASSWORD))
endpoint_with_tls_verify = CalmEndpoint.HTTP(URL, verify=True, auth=Auth.Basic(AUTH_USERNAME, AUTH_PASSWORD))
endpoint_with_incorrect_auth = CalmEndpoint.HTTP(URL, verify=False)
endpoint_without_auth = CalmEndpoint.HTTP(TEST_URL)
endpoint_payload = change_uuids(read_test_config(file_name="http_endpoint_payload.json"), {})


@runbook
def HTTPTask(endpoints=[endpoint]):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "POST",
        body=json.dumps(endpoint_payload),
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        response_paths={"ep_uuid": "$.metadata.uuid"},
        status_mapping={200: True},
        target=ref(endpoint),
    )

    # Check the type of the created endpoint
    CalmTask.HTTP.endpoint(
        "GET",
        relative_url="/" + endpoint_payload['metadata']['uuid'],
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        response_paths={"ep_type": "$.spec.resources.type"},
        status_mapping={200: True},
        target=ref(endpoint),
    )

    # Delete the created endpoint
    CalmTask.HTTP.endpoint(
        "DELETE",
        relative_url="/" + endpoint_payload['metadata']['uuid'],
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True},
        target=ref(endpoint),
    )

    CalmTask.Exec.escript(name="ExecTask", script='''print "@@{ep_type}@@"''')


@runbook
def HTTPTaskWithValidations():

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "POST",
        relative_url="/list",
        body=json.dumps({}),
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        response_paths={"ep_uuid": "$.metdata.uuid"},
    )


@runbook
def HTTPTaskWithoutAuth(endpoints=[endpoint_without_auth], default_target=ref(endpoint_without_auth)):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "GET",
        content_type="text/html",
        status_mapping={200: True}
    )


@runbook
def HTTPTaskWithIncorrectCode(endpoints=[endpoint_without_auth], default_target=ref(endpoint_without_auth)):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "GET",
        name="HTTPTask",
        content_type="text/html",
        status_mapping={300: True}
    )


@runbook
def HTTPTaskWithFailureState(endpoints=[endpoint_without_auth], default_target=ref(endpoint_without_auth)):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "GET",
        name="HTTPTask",
        content_type="text/html",
        status_mapping={200: False}
    )


@runbook
def HTTPTaskWithUnsupportedURL(endpoints=[endpoint], default_target=ref(endpoint)):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "GET",
        name="HTTPTask",
        relative_url="unsupported url",
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True}
    )


@runbook
def HTTPTaskWithUnsupportedPayload(endpoints=[endpoint]):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "POST",
        name="HTTPTask",
        relative_url="/list",
        body=json.dumps({"payload": "unsupported"}),
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True},
        target=ref(endpoint)
    )


@runbook
def HTTPTaskWithIncorrectAuth(endpoints=[endpoint_with_incorrect_auth]):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "POST",
        name="HTTPTask",
        relative_url="/list",
        body=json.dumps({}),
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True},
        target=ref(endpoint_with_incorrect_auth)
    )


@runbook
def HTTPTaskWithTLSVerify(endpoints=[endpoint_with_tls_verify]):

    # Creating an endpoint with POST call
    CalmTask.HTTP.endpoint(
        "POST",
        name="HTTPTask",
        relative_url="/list",
        body=json.dumps({}),
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True},
        target=ref(endpoint_with_tls_verify)
    )
