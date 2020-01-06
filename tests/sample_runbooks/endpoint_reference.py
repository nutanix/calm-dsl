"""
Calm Runbook Sample for running task on already existing endpoint
"""

from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmEndpoint, ref


class DslEndpointReference(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.Exec.ssh(name="Task1", script='echo "hello"', target=ref(CalmEndpoint('DslEndpoint')))

    endpoints = []
    credentials = []


def main():
    print(DslEndpointReference.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
