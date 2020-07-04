"""
Calm DSL Sample Runbook with runbook variable usecase

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import RunbookTask as Task, RunbookVariable as Variable


code = """print "Hello @@{firstname}@@ @@{lastname}@@"
"""


@runbook
def DslRunbookWithVariables():
    "Runbook Service example"
    firstname = Variable.Simple("FIRSTNAME", runtime=True)  # noqa
    lastname = Variable.Simple("LASTNAME")  # noqa
    Task.Exec.escript(name="Exec_Task", script=code)


def main():
    print(DslRunbookWithVariables.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
