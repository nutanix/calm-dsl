"""
Calm DSL Runbook Sample for input task

"""

from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable


code = """print "Hello @@{user_name}@@"
print "Your Password is @@{password}@@"
print "Date you selected is @@{date}@@"
print "Time selected is @@{time}@@"
print "User selected is @@{user}@@"
"""


@runbook
def DslInputRunbook():
    "Runbook Service example"
    Task.Input(
        name="Input_Task",
        inputs=[
            Variable.TaskInput("user_name"),
            Variable.TaskInput("password", input_type="password"),
            Variable.TaskInput("date", input_type="date"),
            Variable.TaskInput("time", input_type="time"),
            Variable.TaskInput(
                "user", input_type="select", options=["user1", "user2", "user3"]
            ),
        ],
    )
    Task.Exec.escript(name="Exec_Task", script=code)


def main():
    print(runbook_json(DslInputRunbook))


if __name__ == "__main__":
    main()
