"""
Calm DSL Sample Runbook with runbook variable usecase

"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref, basic_cred

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
endpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)

code = """
print "@@{var1}@@"
if "@@{var1}@@" == "test":
    print "yes"
else:
    print "no"
print "@@{var2}@@"
if "@@{var2}@@" == "test":
    print "yes"
else:
    print "no"
print "Hello @@{firstname}@@ @@{lastname}@@"
"""


@runbook
def DslRunbookWithVariables(endpoints=[endpoint]):
    "Runbook example with variables"

    var1 = Variable.Simple.Secret("test")  # noqa
    var2 = Variable.Simple.Secret("test")  # noqa
    firstname = Variable.Simple("FIRSTNAME")  # noqa
    lastname = Variable.Simple("LASTNAME")  # noqa
    Task.Exec.escript(name="Exec_Task", script=code, target=endpoints[0])
