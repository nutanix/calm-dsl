"""
Calm DSL Runbook Sample for input task

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask, CalmVariable


code = """print "Hello @@{user_name}@@"
print "Your Password is @@{password}@@"
print "Date you selected is @@{date}@@"
print "Time selected is @@{time}@@"
print "User selected is @@{user}@@"
"""


@runbook
def DslInputRunbook():
    "Runbook Service example"
    CalmTask.Input(
        name="Input_Task",
        inputs=[
            CalmVariable.TaskInput("user_name"),
            CalmVariable.TaskInput("password", input_type="password"),
            CalmVariable.TaskInput("date", input_type="date"),
            CalmVariable.TaskInput("time", input_type="time"),
            CalmVariable.TaskInput(
                "user", input_type="select", options=["user1", "user2", "user3"]
            ),
        ],
    )
    CalmTask.Exec.escript(name="Exec_Task", script=code)


def main():
    print(DslInputRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
