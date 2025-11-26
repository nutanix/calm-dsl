"""
Calm DSL Sample Runbook used for testing execution name

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task


code = """print("Start")
sleep(2)
print("End")"""


@runbook
def DslExecutionRunbook(execution_name="@@{calm_runbook_name}@@_custom_name"):
    "Runbook with execution name example"

    Task.Exec.escript.py3(name="Task1", script=code)


def main():
    print(runbook_json(DslExecutionRunbook))


if __name__ == "__main__":
    main()
