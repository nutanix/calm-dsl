"""
Calm Runbook Sample for running http tasks
"""
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint

AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
URL = read_local_file(".tests/runbook_tests/url")

endpoint = Endpoint.HTTP(
    URL, verify=True, auth=Endpoint.Auth(AUTH_USERNAME, AUTH_PASSWORD)
)


@runbook
def DslHTTPTask(endpoints=[endpoint], default=False):
    "Runbook example for HTTP Tasks"

    Task.HTTP.get(
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True},
        response_paths={"ep_type": "$.spec.resources.type"},
        target=endpoints[0],
    )


def main():
    print(runbook_json(DslHTTPTask))


if __name__ == "__main__":
    main()
