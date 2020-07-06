"""
Calm Runbook Sample for running task on already existing endpoint
"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref


@runbook
def DslExistingEndpoint():
    "Runbook Service example for using exisiting endpoint"
    Task.Exec.ssh(
        name="Task1",
        script='echo "hello"',
        target=ref(Endpoint.use_existing("DslEndpoint")),
    )


def main():
    print(runbook_json(DslExistingEndpoint))


if __name__ == "__main__":
    main()
