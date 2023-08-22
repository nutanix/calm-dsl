from calm.dsl.runbooks import runbook, parallel, branch
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.builtins import Ref, Metadata, read_local_file

PROJECT_NAME = read_local_file("project_name")


@runbook
def ParallelTask():
    "Runbook Service example"
    with parallel() as p:
        with branch(p):
            Task.Delay(2, name="Delay1")
        with branch(p):
            Task.Delay(2, name="Delay2")


class RunbookMetadata(Metadata):
    project = Ref.Project(PROJECT_NAME)
