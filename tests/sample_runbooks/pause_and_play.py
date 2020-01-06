"""
Calm DSL Sample Runbook used for testing runbook pause and play

"""

from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask


code = '''print "Start"
sleep(20)
print "End"'''


class DslPausePlayRunbook(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.Exec.escript(name="Task1", script=code)
        CalmTask.Exec.escript(name="Task2", script=code)
        CalmTask.Exec.escript(name="Task3", script=code)
        CalmTask.Exec.escript(name="Task4", script=code)
        CalmTask.Exec.escript(name="Task5", script=code)

    endpoints = []
    credentials = []


def main():
    print(DslPausePlayRunbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
