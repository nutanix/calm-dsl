"""
Calm DSL Sample Runbook with while loop task

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, Status, StatusHandle


@runbook
def DslWhileLoopRunbook():
    "Runbook example with while loop"

    with Task.Loop(
        iterations=2,
        name="WhileTask",
        exit_condition=Status.SUCCESS,
        loop_variable="loop_var",
    ):
        Task.Exec.escript.py3(
            name="Task1", script="print('Inside loop1 @@{loop_var}@@')"
        )

    with Task.Loop(iterations=2, name="WhileTask2"):
        Task.Exec.escript.py3(
            name="Task2", script="print('Inside loop2 @@{iteration}@@')"
        )

    with Task.Loop(
        iterations=2,
        name="WhileTask",
        exit_condition=Status.SUCCESS,
        loop_variable="loop_var",
        status_map_list=[
            StatusHandle.Mapping.task_status(
                values=[
                    StatusHandle.Status.Failure
                ],
                result=StatusHandle.Result.Warning,
            )
        ],
    ):
        Task.Exec.escript.py3(
            name="Task1", script="print('Inside loop1 @@{loop_var}@@')"
        )


def main():
    print(runbook_json(DslWhileLoopRunbook))


if __name__ == "__main__":
    main()
