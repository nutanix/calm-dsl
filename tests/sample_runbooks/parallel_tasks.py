"""
Calm DSL Sample Runbook for parallel task

"""

from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask


code = '''print "hello"'''


class DslParallelRunbook(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.Exec.escript(name="Task1", script=code)
        with CalmTask.Parallel(name="ParallelTask"):
            CalmTask.Exec.escript(name="Task2", script="print 'Inside Task2'")

            def path():
                CalmTask.Exec.escript(name="Task3_1", script="print 'Inside Task3.1'")
                CalmTask.Exec.escript(name="Task3_2", script="sleep(30)")
                CalmTask.Exec.escript(name="Task3_3", script="print 'Inside Task3.3'")
        CalmTask.Exec.escript(name="Task4", script=code)

    endpoints = []
    credentials = []


def main():
    print(DslParallelRunbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
