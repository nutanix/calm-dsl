"""
Calm DSL Sample Runbook for parallel task

"""

from calm.dsl.builtins import runbook, serial
from calm.dsl.builtins import RunbookTask as Task


code = '''print "hello"'''


@runbook
def DslParallelRunbook():
    "Runbook Service example"
    Task.Exec.escript(name="Task1", script=code)
    with Task.Parallel(name="ParallelTask"):
        Task.Exec.escript(name="Task2", script="print 'Inside Task2'")

        with Task.Loop(iterations=1):
            Task.Exec.escript(name="Task3_1", script="print 'Inside Task3.1'")
            Task.Exec.escript(name="Task3_2", script="sleep(30)")
            Task.Exec.escript(name="Task3_3", script="print 'Inside Task3.3'")

        with serial():
            Task.Exec.escript(name="Task4_1", script="print 'Inside Task4.1'")
            Task.Exec.escript(name="Task4_2", script="print 'Inside Task4.2'")

    Task.Exec.escript(name="Task4", script=code)


def main():
    print(DslParallelRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
