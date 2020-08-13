"""
 Calm Runbooks with VM endpoints
"""
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import CalmAccount as Account
from calm.dsl.runbooks import ENDPOINT_FILTER, ENDPOINT_PROVIDER

AHV_LINUX_ID = read_local_file(".tests/runbook_tests/ahv_linux_id")
AHV_VM_WITHOUT_IP = read_local_file(".tests/runbook_tests/ahv_linux_id_with_no_ip")
AHV_VM_OFF = read_local_file(".tests/runbook_tests/ahv_linux_id_with_powered_off")
AHV_VM_INCORRECT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")

EndpointWithIncorrectId = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    values=[AHV_VM_INCORRECT],
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)


EndpointWithNoIP = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    values=[AHV_VM_WITHOUT_IP],
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)


EndpointWithOffState = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    values=[AHV_VM_OFF],
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)


EndpointWithIPOutsideSubnet = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    values=[AHV_LINUX_ID],
    subnet="0.0.0.0",
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)


@runbook
def VMEndpointWithIncorrectID(endpoints=[EndpointWithIncorrectId]):
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )
    Task.Exec.escript(
        name="EscriptTask",
        script='''echo "Escript Task is Successful"''',
        target=endpoints[0],
    )


@runbook
def VMEndpointWithNoIP(endpoints=[EndpointWithNoIP]):
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )
    Task.Exec.escript(
        name="EscriptTask",
        script='''echo "Escript Task is Successful"''',
        target=endpoints[0],
    )


@runbook
def VMEndpointWithIPOutsideSubnet(endpoints=[EndpointWithIPOutsideSubnet]):
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )
    Task.Exec.escript(
        name="EscriptTask",
        script='''echo "Escript Task is Successful"''',
        target=endpoints[0],
    )


@runbook
def VMEndpointWithOffState(endpoints=[EndpointWithOffState]):
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )
    Task.Exec.escript(
        name="EscriptTask",
        script='''echo "Escript Task is Successful"''',
        target=endpoints[0],
    )
