"""
Calm Runbook Sample for set variable task
"""
import os

from calm.dsl.runbooks import runbook, ref
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint


@runbook
def DslSetVariableRunbook():
    "Runbook example with Set Variable Tasks"

    Task.SetVariable.escript(name="Task1", filename=os.path.join("scripts", "set_variable_task1_script.py"), variables=["var1"])
    Task.SetVariable.ssh(
        name="Task2", filename=os.path.join("scripts", "set_variable_task2_script.sh"), variables=["var2"], target=ref(Endpoint.use_existing("linux_bedag"))
    )
    Task.Exec.escript(name="Task3", script="print ('@@{var1}@@ @@{var2}@@')")
