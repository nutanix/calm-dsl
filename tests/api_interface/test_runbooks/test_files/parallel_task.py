"""
Calm DSL Sample Runbook for parallel task

"""

from calm.dsl.runbooks import runbook, parallel, branch
from calm.dsl.runbooks import RunbookTask as Task


@runbook
def ParallelTask():
    "Runbook Service example"
    with parallel() as p:
        with branch(p):
            Task.Delay(60, name="Delay1")
        with branch(p):
            Task.Delay(60, name="Delay2")
        with branch(p):
            Task.Delay(60, name="Delay3")
