"""
Calm DSL Sample Runbook with global variable usecase

"""

from calm.dsl.runbooks import *
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable


code = """
print("@@{var1}@@")
print("@@{global.GlobalVar}@@")
"""


@runbook
def DslRunbookWithGlobalVariables():
    "Runbook example with global variables"

    var1 = Variable.Simple.Secret("test")  # noqa
    Task.Exec.escript.py3(name="Exec_Task", script=code)

    global_variables = [Ref.GlobalVariable("GlobalVar")]


def main():
    print(runbook_json(DslRunbookWithGlobalVariables))


if __name__ == "__main__":
    main()
