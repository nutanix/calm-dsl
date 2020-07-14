"""
Calm DSL Sample Runbook with runbook variable usecase

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable


code = """print "Hello @@{firstname}@@ @@{lastname}@@"
"""


@runbook
def DslRunbookWithVariables():
    "Runbook example with variables"

    firstname = Variable.Simple("FIRSTNAME", runtime=True)  # noqa
    lastname = Variable.Simple("LASTNAME")  # noqa
    Task.Exec.escript(name="Exec_Task", script=code)


def main():
    print(runbook_json(DslRunbookWithVariables))


if __name__ == "__main__":
    main()
