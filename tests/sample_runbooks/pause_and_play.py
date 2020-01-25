"""
Calm DSL Sample Runbook used for testing runbook pause and play

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask


code = '''print "Start"
sleep(20)
print "End"'''


@runbook
def DslPausePlayRunbook():
    "Runbook Service example"
    CalmTask.Exec.escript(name="Task1", script=code)
    CalmTask.Exec.escript(name="Task2", script=code)
    CalmTask.Exec.escript(name="Task3", script=code)
    CalmTask.Exec.escript(name="Task4", script=code)
    CalmTask.Exec.escript(name="Task5", script=code)


def main():
    print(DslPausePlayRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
