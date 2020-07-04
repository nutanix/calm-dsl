"""
Calm DSL Decision Task Example

"""

from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref


@runbook
def DslDecisionRunbook():
    "Runbook Service example"
    with Task.Decision.ssh(
        name="DecisionTask", script="cat hell", target=ref(Endpoint.use_existing("DslEndpoint"))
    ) as d:

        if d.ok:
            Task.Exec.escript(
                name="Task1", script="print 'Decision Task is Successful'"
            )

        else:
            Task.Exec.escript(name="Task2", script="print 'Decision Task Failed'")


def main():
    print(DslDecisionRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
