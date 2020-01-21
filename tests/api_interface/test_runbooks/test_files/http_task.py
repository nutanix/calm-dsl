"""
Calm Runbook Sample for running http tasks
"""
import json

from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmEndpoint, Auth, ref
from utils import read_test_config, change_uuids

AUTH_USERNAME = read_local_file("/.tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file("/.tests/runbook_tests/auth_password")
URL = read_local_file("/.tests/runbook_tests/url")
TEST_URL = read_local_file("/.tests/runbook_tests/url1")

endpoint = CalmEndpoint.HTTP(URL, verify=False, auth=Auth.Basic(AUTH_USERNAME, AUTH_PASSWORD))
endpoint_without_auth = CalmEndpoint.HTTP(TEST_URL)
endpoint_payload = change_uuids(read_test_config(file_name="endpoint_payload.json"), {})


class HTTPTask(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():

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

    endpoints = [endpoint]
    credentials = []


class HTTPTaskWithValidations(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():

        # Creating an endpoint with POST call
        CalmTask.HTTP.endpoint(
            "POST",
            relative_url="/list",
            body=json.dumps({}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            response_paths={"ep_uuid": "$.metdata.uuid"},
        )

    endpoints = []
    credentials = []


class HTTPTaskWithoutAuth(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():

        # Creating an endpoint with POST call
        CalmTask.HTTP.endpoint(
            "GET",
            content_type="text/html",
            status_mapping={200: True}
        )

    endpoints = [endpoint_without_auth]
    credentials = []
    default_target = ref(endpoint_without_auth)
