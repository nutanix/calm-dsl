"""
 Calm Runbooks with VM endpoints
"""
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import CalmAccount as Account, VM
from calm.dsl.runbooks import ENDPOINT_FILTER, ENDPOINT_PROVIDER

AHV_POWER_ON = read_local_file(".tests/runbook_tests/vm_actions_ahv_on")
AHV_POWER_OFF = read_local_file(".tests/runbook_tests/vm_actions_ahv_off")

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")

PoweredOnVM = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    vms=[VM(uuid=AHV_POWER_ON)],
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)

PoweredOffVM = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    vms=[VM(uuid=AHV_POWER_OFF)],
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)


@runbook
def AHVPowerOnAction(endpoints=[PoweredOffVM]):
    Task.VMPowerOn(name="PowerOnTask", target=endpoints[0])
    Task.Exec.ssh(
        name="ShellTask1",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )
    Task.VMRestart(name="RestartTask", target=endpoints[0])
    Task.Exec.ssh(
        name="ShellTask2",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )


@runbook
def AHVPowerOffAction(endpoints=[PoweredOnVM]):
    Task.VMPowerOff(name="PowerOffTask", target=endpoints[0])
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )
