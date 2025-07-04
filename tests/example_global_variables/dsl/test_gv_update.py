import os
from calm.dsl.builtins import *
from calm.dsl.builtins import (
    GlobalVariable,
    CalmVariable,
    Ref,
    ref,
    Metadata,
    CalmTask as CalmVarTask,
)
from calm.dsl.runbooks import RunbookTask as CalmTask


HttpGlobalVar1 = GlobalVariable(
    definition=CalmVariable.WithOptions.FromTask(
        CalmVarTask.HTTP.get(
            "https://jsonplaceholder.typicode.com/todos/1",
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
            response_paths={"HttpGlobalVar1": "$.title"},
            name="",
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    ),
    projects=[],
)


class GlobalVariableMetadata(Metadata):
    project = Ref.Project("default")
