"""
Calm Runbook Sample for set variable task
"""

from calm.dsl.runbooks import runbook, ref
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint


@runbook
def DslSetVariableRunbook():
    "Runbook example with Set Variable Tasks"

    Task.SetVariable.escript(name="Task1", script="print ('var1=test')", variables=["var1"])
    Task.Exec.escript(name="Task3", script="print ('@@{var1}@@ @@{var2}@@')")
