"""
Calm Runbook Sample for running task on already existing endpoint
"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmEndpoint, ref


@runbook
def DslEndpointReference():
    "Runbook Service example"
    CalmTask.Exec.ssh(name="Task1", script='echo "hello"', target=ref(CalmEndpoint('DslEndpoint')))


def main():
    print(DslEndpointReference.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
