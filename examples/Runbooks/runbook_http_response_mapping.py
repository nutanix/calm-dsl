"""
Calm DSL HTTP Runbook
"""
import os
import json
from calm.dsl.runbooks import *
from calm.dsl.runbooks import (
    CalmEndpoint as Endpoint,
    RunbookTask as CalmTask,
    RunbookVariable as CalmVariable,
)
from calm.dsl.builtins import CalmTask as CalmVarTask, Metadata

PCEndpoint = Endpoint.HTTP("https://localhost:9440/api/nutanix/v3")


# Runbook
@runbook
def DslHTTPTaskResponseCodeRange(endpoints=[PCEndpoint]):
    CalmTask.HTTP.post(
        name="Task 1",
        relative_url="/endpoints/list",
        headers={"Authorization": "Bearer @@{calm_jwt}@@"},
        content_type="application/json",
        verify=False,
        body=json.dumps({}),
        response_code_status_map=[
            HTTPResponseHandle.ResponseCode(
                code=200,
                code_ranges=[{"start_code": 200, "end_code": 200}],
                status=HTTPResponseHandle.TASK_STATUS.Success,
            )
        ],
        target=ref(endpoints[0]),
    )


def main():
    print(runbook_json(DslHTTPTaskResponseCodeRange))


if __name__ == "__main__":
    main()