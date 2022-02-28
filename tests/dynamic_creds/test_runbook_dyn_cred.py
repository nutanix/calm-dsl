"""
Calm DSL Sample Runbook used for testing runbook pause and play

"""

import json

from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task, basic_cred
from calm.dsl.builtins import dynamic_cred
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import CalmEndpoint as Endpoint, Ref

DNS_SERVER = read_local_file(".tests/dns_server")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
VM_IP = DSL_CONFIG["EXISTING_MACHINE"]["IP_1"]
CRED_USERNAME = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["LINUX"]["USERNAME"]
CRED_PASSWORD = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["LINUX"]["PASSWORD"]
WIN_CRED_USERNAME = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["WINDOWS"]["USERNAME"]
WIN_CRED_PASSWORD = DSL_CONFIG["EXISTING_MACHINE"]["CREDS"]["WINDOWS"]["PASSWORD"]
SECRET_PATH = "nutanix"

WindowsCred = basic_cred(WIN_CRED_USERNAME, WIN_CRED_PASSWORD, name="endpoint_cred")

CRED_PROVIDER = "HashiCorpVault_Cred_Provider"

Cred = dynamic_cred(
    CRED_USERNAME,
    Ref.Account(name=CRED_PROVIDER),
    variable_dict={"path": SECRET_PATH},
    name="cred",
)
endpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)
linux_endpoint_with_wrong_cred = Endpoint.Linux.ip([VM_IP], cred=WindowsCred)


@runbook
def DslDynCredEPRunbook(endpoints=[endpoint]):
    "Runbook example"
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0]
    )


@runbook
def DslDynCredRunbook(endpoints=[linux_endpoint_with_wrong_cred], credentials=[Cred]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=endpoints[0],
        cred=credentials[0],
    )
