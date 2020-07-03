"""
Calm DSL Sample Runbook with while loop task

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import RunbookTask as Task, Status


@runbook
def DslWhileLoopRunbook():
    "Runbook Service example"
    with Task.Loop(iterations=2, name="WhileTask", exit_condition=Status.SUCCESS):
        Task.Exec.escript(name="Task1", script="print 'Inside loop1 @@{iteration}@@'")

    with Task.Loop(iterations=2):
        Task.Exec.escript(name="Task2", script="print 'Inside loop2 @@{iteration}@@'")


def main():
    print(DslWhileLoopRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
