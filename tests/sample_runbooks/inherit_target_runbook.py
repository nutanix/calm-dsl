"""
Calm DSL Decision Task with child tasks inheriting target Example

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref


@runbook
def DslInheritTargetRunbook():
    """
    Runbook example with decision task with child tasks inheriting target
    """

    with Task.Decision.ssh(
        name="DecisionTask",
        script="cat hell",
        target=ref(Endpoint.use_existing("DslEndpoint")),
    ) as d:

        if d.ok:
            Task.Exec.escript(
                name="Task1",
                script="print 'Decision Task is Successful'",
                inherit_target=True,
            )

        else:
            Task.Exec.ssh(
                name="Task2", script="print 'Decision Task Failed'", inherit_target=True
            )


def main():
    print(runbook_json(DslInheritTargetRunbook))


if __name__ == "__main__":
    main()
