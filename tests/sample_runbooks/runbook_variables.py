"""
Calm DSL Sample Runbook with runbook variable usecase

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable


code = """
print("@@{var1}@@")
if "@@{var1}@@" == "test":
    print("yes")
else:
    print("no")
print("@@{var2}@@")
if "@@{var2}@@" == "test":
    print("yes")
else:
    print("no")
print("Hello @@{firstname}@@ @@{lastname}@@")
"""


@runbook
def DslRunbookWithVariables():
    "Runbook example with variables"

    var1 = Variable.Simple.Secret("test")  # noqa
    var2 = Variable.Simple.Secret("test", runtime=True)  # noqa
    firstname = Variable.Simple("FIRSTNAME", runtime=True)  # noqa
    lastname = Variable.Simple("LASTNAME")  # noqa
    Task.Exec.escript.py3(name="Exec_Task", script=code)


def main():
    print(runbook_json(DslRunbookWithVariables))


if __name__ == "__main__":
    main()
