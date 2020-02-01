"""
Calm DSL Sample Runbook for parallel task

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask


@runbook
def ParallelTask():
    "Runbook Service example"
    with CalmTask.Parallel():
        CalmTask.Delay(60, name="Delay1")
        CalmTask.Delay(60, name="Delay2")
        CalmTask.Delay(60, name="Delay3")
