"""
Calm DSL Sample Runbook with while loop task

"""

from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask


class DslWhileLoopRunbook(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        while(CalmTask.While(10, name="WhileTask", parallel_factor=2)):
            CalmTask.Exec.escript(name="Task1", script="print 'Inside loop1 @@{loop_counter}@@'")

        while(5):
            CalmTask.Exec.escript(name="Task2", script="print 'Inside loop2 @@{loop_counter}@@'")

    endpoints = []
    credentials = []


def main():
    print(DslWhileLoopRunbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
