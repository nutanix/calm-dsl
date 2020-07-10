"""
Calm DSL Sample Runbook used for testing runbook pause and play

"""

from calm.dsl.runbooks import parallel, branch
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task


code = '''print "Start"
sleep(20)
print "End"'''


@runbook
def DslParallelRunbook():
    "Runbook example for running tasks in parallel"

    Task.Exec.escript(name="root", script=code)
    with parallel() as p:

        with branch(p):
            Task.Exec.escript(name="Task1", script=code)

        with branch(p):
            Task.Exec.escript(name="Task2", script=code)
            Task.Exec.escript(name="Task3", script=code)

        with branch(p):
            Task.Exec.escript(name="Task4", script=code)
            Task.Exec.escript(name="Task5", script=code)


def main():
    print(runbook_json(DslParallelRunbook))


if __name__ == "__main__":
    main()
