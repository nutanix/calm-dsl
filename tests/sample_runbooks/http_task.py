"""
Calm Runbook Sample for running http tasks
"""
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmEndpoint, Auth

AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
URL = read_local_file(".tests/runbook_tests/url")

endpoint = CalmEndpoint.HTTP(
    URL, verify=True, auth=Auth.Basic(AUTH_USERNAME, AUTH_PASSWORD)
)


@runbook
def DslHTTPTask(endpoints=[endpoint], default=False):
    "Runbook Service example"
    Task.HTTP.endpoint(
        "GET",
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True},
        response_paths={"ep_type": "$.spec.resources.type"},
        target=endpoints[0],
    )


def main():
    print(DslHTTPTask.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
