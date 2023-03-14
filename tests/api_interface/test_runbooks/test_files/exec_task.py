"""
Calm Runbook Sample for running http tasks
"""
import json
from calm.dsl.runbooks import read_local_file, read_file
from calm.dsl.runbooks import runbook, Ref
from calm.dsl.runbooks import RunbookTask as Task, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref
from calm.dsl.builtins.models.helper.common import get_vmware_account_from_datacenter
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
AHV_LINUX_ID = read_local_file(".tests/runbook_tests/ahv_linux_id")
AHV_LINUX_VM_NAME = read_local_file(".tests/runbook_tests/ahv_linux_vm_name")
AHV_LINUX_VM_NAME_PREFIX = read_local_file(
    ".tests/runbook_tests/ahv_linux_vm_name_prefix"
)
# AHV_WINDOWS_ID = read_local_file(".tests/runbook_tests/ahv_windows_id")

VMWARE_LINUX_ID = read_local_file(".tests/runbook_tests/vmware_linux_id")
VMWARE_LINUX_VM_NAME = read_local_file(".tests/runbook_tests/vmware_linux_vm_name")
VMWARE_LINUX_VM_NAME_PREFIX = read_local_file(
    ".tests/runbook_tests/vmware_linux_vm_name_prefix"
)

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

HTTP_AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
HTTP_AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
HTTP_URL = read_local_file(".tests/runbook_tests/url")

LOCAL_LINUX_ENDPOINT_VPC = read_local_file(".tests/endpoint_linux_vpc")
LOCAL_WINDOWS_ENDPOINT_VPC = read_local_file(".tests/endpoint_windows_vpc")

VMWARE_ACCOUNT_NAME = get_vmware_account_from_datacenter()

http_endpoint = Endpoint.HTTP(
    HTTP_URL,
    verify=False,
    auth=Endpoint.Auth(HTTP_AUTH_USERNAME, HTTP_AUTH_PASSWORD),
)

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="endpoint_cred")

linux_endpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)

# Linux AHV VM Endpoint with static VM ID values
linux_ahv_static_vm_endpoint = Endpoint.Linux.vm(
    vms=[Ref.Vm(uuid=AHV_LINUX_ID)],
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)

# Linux AHV VM Endpoint with Dynamic filter name equals filter
linux_ahv_dynamic_vm_endpoint1 = Endpoint.Linux.vm(
    filter="name==" + AHV_LINUX_VM_NAME,
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)

# Linux AHV VM Endpoint with Dynamic filter name starts with filter
linux_ahv_dynamic_vm_endpoint2 = Endpoint.Linux.vm(
    filter="name==" + AHV_LINUX_VM_NAME_PREFIX + ".*",
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)

# Linux AHV VM Endpoint with Dynamic filter power state is on filter
linux_ahv_dynamic_vm_endpoint3 = Endpoint.Linux.vm(
    filter="power_state==on;name==" + AHV_LINUX_VM_NAME_PREFIX + ".*",
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)

linux_vmware_static_vm_endpoint = Endpoint.Linux.vm(
    vms=[Ref.Vm(uuid=VMWARE_LINUX_ID)],
    cred=LinuxCred,
    account=Ref.Account(VMWARE_ACCOUNT_NAME),
)

linux_vmware_dynamic_vm_endpoint1 = Endpoint.Linux.vm(
    filter="name==" + VMWARE_LINUX_VM_NAME,
    cred=LinuxCred,
    account=Ref.Account(VMWARE_ACCOUNT_NAME),
)

linux_vmware_dynamic_vm_endpoint2 = Endpoint.Linux.vm(
    filter="name==" + VMWARE_LINUX_VM_NAME_PREFIX + ".*",
    cred=LinuxCred,
    account=Ref.Account(VMWARE_ACCOUNT_NAME),
)

linux_vmware_dynamic_vm_endpoint3 = Endpoint.Linux.vm(
    filter="power_state==poweredOn;name==" + VMWARE_LINUX_VM_NAME_PREFIX + ".*",
    cred=LinuxCred,
    account=Ref.Account(VMWARE_ACCOUNT_NAME),
)

linux_endpoint_with_wrong_cred = Endpoint.Linux.ip([linux_ip], cred=WindowsCred)
multiple_linux_endpoint = Endpoint.Linux.ip([linux_ip, linux_ip], cred=LinuxCred)

windows_endpoint = Endpoint.Windows.ip([windows_ip], cred=WindowsCred)
windows_endpoint_with_wrong_cred = Endpoint.Windows.ip([windows_ip], cred=LinuxCred)
multiple_windows_endpoint = Endpoint.Windows.ip(
    [windows_ip, windows_ip], cred=WindowsCred
)


@runbook
def EscriptTask():
    Task.Exec.escript(name="ExecTask", script='''print "Task is Successful"''')


@runbook
def EscriptMacroTask():
    Task.Exec.escript(name="EscriptMacroTask", filename="macro_escript.py")


@runbook
def SetVariableOnEscript():
    Task.SetVariable.escript(
        name="SetVariableTask",
        script='''print "task_state=Successful"''',
        variables=["task_state"],
    )
    Task.Exec.escript(name="ExecTask", script='''print "Task is @@{task_state}@@"''')


@runbook
def EscriptOnEndpoint(endpoints=[multiple_linux_endpoint]):
    Task.Exec.escript(
        name="ExecTask", script='''print "Task is Successful"''', target=endpoints[0]
    )


@runbook
def PowershellTask(endpoints=[windows_endpoint]):
    Task.Exec.powershell(
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0]
    )


@runbook
def PowershellTaskinVpc():
    LOG.info(LOCAL_WINDOWS_ENDPOINT_VPC)
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(Endpoint.use_existing(LOCAL_WINDOWS_ENDPOINT_VPC)),
    )


@runbook
def ShellTaskinVpc():
    LOG.info(LOCAL_LINUX_ENDPOINT_VPC)
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(Endpoint.use_existing(LOCAL_LINUX_ENDPOINT_VPC)),
    )


@runbook
def SetVariableOnPowershell(endpoints=[windows_endpoint]):
    Task.SetVariable.powershell(
        name="SetVariableTask",
        script='''echo "task_state=Successful"''',
        variables=["task_state"],
    )
    Task.Exec.powershell(name="ExecTask", script='''echo "Task is @@{task_state}@@"''')


@runbook
def PowershellOnMultipleIPs(endpoints=[multiple_windows_endpoint]):
    Task.Exec.powershell(
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0]
    )


@runbook
def PowershellWithCredOverwrite(
    endpoints=[windows_endpoint_with_wrong_cred], credentials=[WindowsCred]
):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=endpoints[0],
        cred=credentials[0],
    )


@runbook
def ShellTask(endpoints=[linux_endpoint]):
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0]
    )


@runbook
def ShellTaskOnLinuxVMAHVStaticEndpoint(endpoints=[linux_ahv_static_vm_endpoint]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVDynamicEndpoint1(endpoints=[linux_ahv_dynamic_vm_endpoint1]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVDynamicEndpoint2(endpoints=[linux_ahv_dynamic_vm_endpoint2]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVDynamicEndpoint3(endpoints=[linux_ahv_dynamic_vm_endpoint3]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMVMWareStaticEndpoint(endpoints=[linux_vmware_static_vm_endpoint]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMVMWareDynamicEndpoint1(
    endpoints=[linux_vmware_dynamic_vm_endpoint1],
):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMVMWareDynamicEndpoint2(
    endpoints=[linux_vmware_dynamic_vm_endpoint2],
):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMVMWareDynamicEndpoint3(
    endpoints=[linux_vmware_dynamic_vm_endpoint3],
):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def SetVariableOnShell(endpoints=[linux_endpoint]):
    Task.SetVariable.ssh(
        name="SetVariableTask",
        script='''echo "task_state=Successful"''',
        variables=["task_state"],
    )
    Task.Exec.ssh(name="ExecTask", script='''echo "Task is @@{task_state}@@"''')


@runbook
def ShellOnMultipleIPs(endpoints=[multiple_linux_endpoint]):
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0]
    )


@runbook
def ShellWithCredOverwrite(
    endpoints=[linux_endpoint_with_wrong_cred], credentials=[LinuxCred]
):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=endpoints[0],
        cred=credentials[0],
    )


@runbook
def PowershellTaskWithoutTarget():
    Task.Exec.powershell(name="ExecTask", script='''echo "Task is Successful"''')


@runbook
def ShellTaskWithoutTarget():
    Task.Exec.ssh(name="ExecTask", script='''echo "Task is Successful"''')


@runbook
def MacroOnShell(endpoints=[linux_endpoint]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "@@{calm_runbook_name}@@, @@{calm_runbook_uuid}@@ @@{calm_project_name}@@ @@{calm_jwt}@@ @@{calm_date}@@"''',
    )


@runbook
def MacroOnPowershell(endpoints=[windows_endpoint]):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "@@{calm_runbook_name}@@, @@{calm_runbook_uuid}@@ @@{calm_project_name}@@ @@{calm_jwt}@@ @@{calm_date}@@"''',
    )


@runbook
def MacroOnEscript():
    Task.Exec.escript(
        name="ExecTask",
        script='''print "@@{calm_runbook_name}@@, @@{calm_runbook_uuid}@@ @@{calm_project_name}@@ @@{calm_jwt}@@ @@{calm_date}@@"''',
    )


@runbook
def EndpointMacroOnShell(endpoints=[linux_endpoint]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "@@{endpoint.name}@@, @@{endpoint.type}@@, @@{endpoint.address}@@, @@{endpoint.port}@@, @@{endpoint.credential.username}@@"''',
    )


@runbook
def EndpointMacroOnPowershell(endpoints=[windows_endpoint]):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "@@{endpoint.name}@@, @@{endpoint.type}@@, @@{endpoint.address}@@, @@{endpoint.port}@@,\
        @@{endpoint.connection_protocol}@@, @@{endpoint.credential.username}@@"''',
    )


@runbook
def WindowsEndpointMacroOnEscript(endpoints=[windows_endpoint], default=False):
    Task.Exec.escript(
        name="ExecTask",
        target=endpoints[0],
        script='''print "@@{endpoint.name}@@, @@{endpoint.type}@@, @@{endpoint.address}@@, @@{endpoint.port}@@,\
        @@{endpoint.connection_protocol}@@, @@{endpoint.credential.username}@@"''',
    )


@runbook
def LinuxEndpointMacroOnEscript(endpoints=[linux_endpoint], default=False):
    Task.Exec.escript(
        name="ExecTask",
        target=endpoints[0],
        script='''print "@@{endpoint.name}@@, @@{endpoint.type}@@, @@{endpoint.address}@@, @@{endpoint.port}@@, @@{endpoint.credential.username}@@"''',
    )


@runbook
def HttpEndpointMacroOnEscript(endpoints=[http_endpoint], default=False):
    Task.Exec.escript(
        name="ExecTask",
        target=endpoints[0],
        script='''print "@@{endpoint.name}@@, @@{endpoint.type}@@, @@{endpoint.base_url}@@, @@{endpoint.retry_count}@@, \
        @@{endpoint.retry_interval}@@, @@{endpoint.tls_verify}@@, @@{endpoint.connection_timeout}@@"''',
    )
