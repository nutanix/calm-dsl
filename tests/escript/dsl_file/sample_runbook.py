"""
Calm DSL Runbook

"""
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task


script = """print "hi"
"""


@runbook
def SampleRunbook():

    Task.Exec.escript(name="EScriptSample", script=script)


def main():
    print(runbook_json(SampleRunbook))


if __name__ == "__main__":
    main()
