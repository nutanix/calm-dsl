"""
Calm DSL Entity Stats Runbook

"""
import json

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable
from calm.dsl.runbooks import CalmEndpoint as Endpoint

PCEndpoint = Endpoint.HTTP("https://localhost:9440/api/nutanix/v3")

script = """
print "Calm Entity Stats are as follows -"
print "Endpoint Count   - @@{endpoints_count}@@"
print "Blueprint Count  - @@{blueprints_count}@@"
print "Runbook Count    - @@{runbooks_count}@@"
print "Apps Count       - @@{apps_count}@@"
"""


@runbook
def DslEntityStatsRunbook(endpoints=[PCEndpoint]):

    "Example runbook for getting count of calm entities on PC"
    endpoints_count  = Variable.Simple.int("0")  # noqa
    blueprints_count = Variable.Simple.int("0")  # noqa
    runbooks_count   = Variable.Simple.int("0")  # noqa
    apps_count       = Variable.Simple.int("0")  # noqa

    Task.HTTP.post(
        name="EndpointCount",
        relative_url="/endpoints/list",
        body=json.dumps({}),
        headers={"Authorization": "Bearer @@{calm_jwt}@@"},
        content_type="application/json",
        response_paths={"endpoints_count": "$.metadata.total_matches"},
        status_mapping={200: True},
    )
    Task.HTTP.post(
        name="BlueprintCount",
        relative_url="/blueprints/list",
        body=json.dumps({}),
        headers={"Authorization": "Bearer @@{calm_jwt}@@"},
        content_type="application/json",
        response_paths={"blueprints_count": "$.metadata.total_matches"},
        status_mapping={200: True},
    )
    Task.HTTP.post(
        name="RunbookCount",
        relative_url="/runbooks/list",
        body=json.dumps({}),
        headers={"Authorization": "Bearer @@{calm_jwt}@@"},
        content_type="application/json",
        response_paths={"runbooks_count": "$.metadata.total_matches"},
        status_mapping={200: True},
    )
    Task.HTTP.post(
        name="AppCount",
        relative_url="/apps/list",
        body=json.dumps({}),
        headers={"Authorization": "Bearer @@{calm_jwt}@@"},
        content_type="application/json",
        response_paths={"apps_count": "$.metadata.total_matches"},
        status_mapping={200: True},
    )
    Task.Exec.escript(name="EntityStats", script=script)


def main():
    print(runbook_json(DslEntityStatsRunbook))


if __name__ == "__main__":
    main()
