"""
 Calm Runbooks with VM endpoints
"""
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook, Ref
from calm.dsl.runbooks import RunbookTask as Task, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint

AHV_LINUX_ID = read_local_file(".tests/runbook_tests/ahv_linux_id")
AHV_VM_WITHOUT_IP = read_local_file(".tests/runbook_tests/ahv_linux_id_with_no_ip")
AHV_VM_OFF = read_local_file(".tests/runbook_tests/ahv_linux_id_with_powered_off")
AHV_VM_INCORRECT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")

EndpointWithIncorrectId = Endpoint.Linux.vm(
    vms=[Ref.Vm(uuid=AHV_VM_INCORRECT)],
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)


EndpointWithNoIP = Endpoint.Linux.vm(
    vms=[Ref.Vm(uuid=AHV_VM_WITHOUT_IP)],
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)


EndpointWithOffState = Endpoint.Linux.vm(
    vms=[Ref.Vm(uuid=AHV_VM_OFF)],
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)


EndpointWithIPOutsideSubnet = Endpoint.Linux.vm(
    vms=[Ref.Vm(uuid=AHV_LINUX_ID)],
    subnet="255.255.255.255/1",
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)


@runbook
def VMEndpointWithIncorrectID(endpoints=[EndpointWithIncorrectId]):
    Task.Exec.escript.py3(
        name="EscriptTask",
        script="""print("Escript Task is Successful")""",
        target=endpoints[0],
    )
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )


@runbook
def VMEndpointWithNoIP(endpoints=[EndpointWithNoIP]):
    Task.Exec.escript.py3(
        name="EscriptTask",
        script="""print("Escript Task is Successful")""",
        target=endpoints[0],
    )
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )


@runbook
def VMEndpointWithIPOutsideSubnet(endpoints=[EndpointWithIPOutsideSubnet]):
    Task.Exec.escript.py3(
        name="EscriptTask",
        script="""print("Escript Task is Successful")""",
        target=endpoints[0],
    )
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )


@runbook
def VMEndpointWithOffState(endpoints=[EndpointWithOffState]):
    Task.Exec.escript.py3(
        name="EscriptTask",
        script="""print("Escript Task is Successful")""",
        target=endpoints[0],
    )
    Task.Exec.ssh(
        name="ShellTask",
        script='''echo "Shell Task is Successful"''',
        target=endpoints[0],
    )
