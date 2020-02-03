"""
Calm DSL Runbook Sample for input task

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask, TaskInput


inputs = [
    TaskInput("my_name"),
    TaskInput("password", input_type="password"),
    TaskInput("date", input_type="date"),
    TaskInput("time", input_type="time"),
    TaskInput("user", input_type="select", options=["user1", "user2", "user3"]),
]


code = '''print "Hello @@{my_name}@@"
print "Your Password is @@{password}@@"
print "Date you selected is @@{date}@@"
print "Time selected is @@{time}@@"
print "User selected is @@{user}@@"
'''


@runbook
def DslInputRunbook():
    "Runbook Service example"
    CalmTask.Input(name="Input_Task", inputs=inputs)
    CalmTask.Exec.escript(name="Exec_Task", script=code)


def main():
    print(DslInputRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
