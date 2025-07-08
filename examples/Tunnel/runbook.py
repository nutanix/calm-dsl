import os
import json
from calm.dsl.runbooks import *
from calm.dsl.runbooks import (
    CalmEndpoint as Endpoint,
    RunbookTask as CalmTask,
    RunbookVariable as CalmVariable,
    read_local_file
)
from calm.dsl.builtins import CalmTask as CalmVarTask, Metadata

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]
TUNNEL_2 = DSL_CONFIG["TUNNELS"]["TUNNEL_2"]["NAME"]

# Runbook
@runbook
def TestRunbook():

    HttpDeleteVariable = CalmVariable.WithOptions.FromTask(
        CalmVarTask.HTTP.delete(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"HttpDeleteVariable": "$.api_version"},
            name="",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
            body="{}",
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    )  # noqa
    HttpPutVariable = CalmVariable.WithOptions.FromTask(
        CalmVarTask.HTTP.put(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"HttpPutVariable": "$.api_version"},
            name="",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            body="{}",
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    )  # noqa
    HttpPostVariable = CalmVariable.WithOptions.FromTask(
        CalmVarTask.HTTP.post(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"HttpPostVariable": "$.api_version"},
            name="",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
            body="{}",
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    )  # noqa
    HttpGetVariable = CalmVariable.WithOptions.FromTask(
        CalmVarTask.HTTP.get(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"HttpGetVariable": "$.api_version"},
            name="",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    )  # noqa
    EscriptVariable = CalmVariable.WithOptions.FromTask(
        CalmVarTask.Exec.escript.py3(
            name="",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    )  # noqa

    CalmTask.Exec.escript.py3(
        name="Execute Escript",
        script="print('Hello World')",
        tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
    )

    CalmTask.SetVariable.escript.py3(
        name="Set_Variable Escript",
        script="print('Hello World')",
        tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
        variables=["var1"],
    )

    with CalmTask.Decision.escript.py3(
        name="Decision Escript",
        script="print('Hello World')",
        tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
    ) as d0:

        if d0.ok:
            CalmTask.Exec.escript.py3(
                name="Task 3_2",
                script="print('Hello World')",
            )

        else:
            CalmTask.Exec.escript.py3(
                name="Task 3_1",
                script="print('Hello World')",
            )


class RunbookMetadata(Metadata):
    project = Ref.Project("default")
