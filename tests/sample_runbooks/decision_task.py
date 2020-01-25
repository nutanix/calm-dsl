"""
Calm DSL Decision Task Example

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmEndpoint, ref


@runbook
def DslDecisionRunbook():
    "Runbook Service example"
    with CalmTask.Decision.ssh(name="DecisionTask", script="cat hell", target=ref(CalmEndpoint("DslEndpoint"))):
        def success():
            CalmTask.Exec.escript(name="Task1", script="print 'Decision Task is Successful'")

        def failure():
            CalmTask.Exec.escript(name="Task2", script="print 'Decision Task Failed'")


def main():
    print(DslDecisionRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
