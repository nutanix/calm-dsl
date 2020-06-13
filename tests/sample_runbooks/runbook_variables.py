"""
Calm DSL Sample Runbook with runbook variable usecase

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask, CalmVariable


code = """print "Hello @@{firstname}@@ @@{lastname}@@"
"""


@runbook
def DslRunbookWithVariables():
    "Runbook Service example"
    firstname = CalmVariable.Simple("FIRSTNAME", runtime=True)  # noqa
    lastname = CalmVariable.Simple("LASTNAME")  # noqa
    CalmTask.Exec.escript(name="Exec_Task", script=code)


def main():
    print(DslRunbookWithVariables.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
