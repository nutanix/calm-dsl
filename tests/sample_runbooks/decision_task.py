"""
Calm DSL Decision Task Example

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmEndpoint, ref


@runbook
def DslDecisionRunbook():
    "Runbook Service example"
    with Task.Decision.ssh(
        name="DecisionTask", script="cat hell", target=ref(CalmEndpoint("DslEndpoint"))
    ) as val:

        if val.true:
            Task.Exec.escript(
                name="Task1", script="print 'Decision Task is Successful'"
            )

        if val.false:
            Task.Exec.escript(name="Task2", script="print 'Decision Task Failed'")


def main():
    print(DslDecisionRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
