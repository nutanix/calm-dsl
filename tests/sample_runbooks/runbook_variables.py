"""
Calm DSL Sample Runbook with runbook variable usecase

"""

from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask, CalmVariable


code = '''print "Hello @@{firstname}@@ @@{lastname}@@"
'''


class DslRunbookWithVariables(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        firstname = CalmVariable.Simple("FIRSTNAME", runtime=True)  # noqa
        lastname = CalmVariable.Simple("LASTNAME")  # noqa
        CalmTask.Exec.escript(name="Exec_Task", script=code)

    endpoints = []
    credentials = []


def main():
    print(DslRunbookWithVariables.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
