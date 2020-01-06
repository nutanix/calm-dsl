"""
Calm DSL Confirm Task Example

"""

from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask


code = '''print "Hello"
print "Bye"'''


class DslConfirmRunbook(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.Confirm(name="Confirm_Task")
        CalmTask.Exec.escript(name="Exec_Task", script=code)

    endpoints = []
    credentials = []


def main():
    print(DslConfirmRunbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
