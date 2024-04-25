"""
Calm DSL Confirm Task Example

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task


code = """print("Hello")
print("Bye")"""


@runbook
def DslConfirmRunbook():
    "Runbook Service example"
    Task.Confirm(name="Confirm_Task")
    Task.Exec.escript.py3(name="Exec_Task", script=code)


def main():
    print(runbook_json(DslConfirmRunbook))


if __name__ == "__main__":
    main()
