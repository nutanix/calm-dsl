"""
Calm DSL Sample Runbook for parallel task

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import RunbookTask as Task


@runbook
def ParallelTask():
    "Runbook Service example"
    with Task.Parallel():
        Task.Delay(60, name="Delay1")
        Task.Delay(60, name="Delay2")
        Task.Delay(60, name="Delay3")
