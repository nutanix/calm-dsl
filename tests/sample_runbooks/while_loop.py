"""
Calm DSL Sample Runbook with while loop task

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, Status


@runbook
def DslWhileLoopRunbook():
    "Runbook example with while loop"

    with Task.Loop(
        iterations=2,
        name="WhileTask",
        exit_condition=Status.SUCCESS,
        loop_variable="loop_var",
    ):
        Task.Exec.escript(name="Task1", script="print 'Inside loop1 @@{loop_var}@@'")

    with Task.Loop(iterations=2, name="WhileTask2"):
        Task.Exec.escript(name="Task2", script="print 'Inside loop2 @@{iteration}@@'")


def main():
    print(runbook_json(DslWhileLoopRunbook))


if __name__ == "__main__":
    main()
