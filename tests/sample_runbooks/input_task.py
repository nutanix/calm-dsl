"""
Calm DSL Runbook Sample for input task

"""

from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask, TaskInput


inputs = [
    TaskInput("name"),
    TaskInput("password", input_type="password"),
    TaskInput("date", input_type="date"),
    TaskInput("time", input_type="time"),
    TaskInput("user", input_type="select", options=["user1", "user2", "user3"]),
]


code = '''print "Hello @@{name}@@"
print "Your Password is @@{password}@@"
print "Date you selected is @@{date}@@"
print "Time selected is @@{time}@@"
print "User selected is @@{user}@@"
'''


class DslInputRunbook(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.Input(name="Input_Task", inputs=inputs)
        CalmTask.Exec.escript(name="Exec_Task", script=code)

    endpoints = []
    credentials = []


def main():
    print(DslInputRunbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
