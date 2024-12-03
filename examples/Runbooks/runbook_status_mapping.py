"""
Calm DSL VM Operation Runbook

"""
import os
import json

from calm.dsl.builtins import * 
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import (
    CalmEndpoint as Endpoint,
    RunbookTask as CalmTask,
    RunbookVariable as CalmVariable,
    StatusHandle,
)


CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
DslLinuxEndpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)

# Runbook
@runbook
def DslStatusMap(endpoints=[DslLinuxEndpoint]):
    CalmTask.Exec.ssh(
        name="Task 1",
        script="echo ('Hello')", 
        target=ref(endpoints[0]),
        status_map_list=[
            StatusHandle.Mapping.task_status(
                values=[
                    StatusHandle.Status.TaskFailure
                ],
                result=StatusHandle.Result.Warning,
            )
        ],
    )
    CalmTask.Exec.escript.py3(
        name="Task 2", 
        script="print ('Hello')", 
        status_map_list=[
            StatusHandle.Mapping.exit_code(
                values=[
                    {"start_code": 5, "end_code": 5},
                    {"start_code": 10, "end_code": 15},
                    {"start_code": 40, "end_code": 40},
                ],
                result=StatusHandle.Result.Warning,
            )
        ],
    )


def main():
    print(runbook_json(DslStatusMap))


if __name__ == "__main__":
    main()

