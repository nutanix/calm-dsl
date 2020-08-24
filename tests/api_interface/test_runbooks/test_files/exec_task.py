"""
Calm Runbook Sample for running http tasks
"""
from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import CalmAccount as Account
from calm.dsl.runbooks import ENDPOINT_FILTER, ENDPOINT_PROVIDER

linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
AHV_LINUX_ID = read_local_file(".tests/runbook_tests/ahv_linux_id")
AHV_LINUX_VM_NAME = read_local_file(".tests/runbook_tests/ahv_linux_vm_name")
AHV_LINUX_VM_NAME_PREFIX = read_local_file(".tests/runbook_tests/ahv_linux_vm_name_prefix")
AHV_WINDOWS_ID = read_local_file(".tests/runbook_tests/ahv_windows_id")
VMWARE_LINUX_ID = read_local_file(".tests/runbook_tests/vmware_linux_id")
VMWARE_WINDOWS_ID = read_local_file(".tests/runbook_tests/vmware_windows_id")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

HTTP_AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
HTTP_AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
HTTP_URL = read_local_file(".tests/runbook_tests/url")

http_endpoint = Endpoint.HTTP(
    HTTP_URL, verify=False, auth=Endpoint.Auth(HTTP_AUTH_USERNAME, HTTP_AUTH_PASSWORD),
)

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="endpoint_cred")

linux_endpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)

# Linux AHV VM Endpoint with static VM ID values
linux_ahv_static_vm_endpoint = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    values=[AHV_LINUX_ID],
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)

# Linux AHV VM Endpoint with Dynamic filter name equals filter
linux_ahv_dynamic_vm_endpoint1 = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="name==" + AHV_LINUX_VM_NAME,
    cred=LinuxCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)

# Linux AHV VM Endpoint with Dynamic filter name starts with filter
linux_ahv_dynamic_vm_endpoint2 = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="name==" + AHV_LINUX_VM_NAME_PREFIX + ".*",
    cred=LinuxCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)

# Linux AHV VM Endpoint with Dynamic filter power state is on filter
linux_ahv_dynamic_vm_endpoint3 = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="power_state==on",
    cred=LinuxCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)

# Linux AHV VM Endpoint with Dynamic filter UUID in filter
linux_ahv_dynamic_vm_endpoint4 = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="uuid=in=(" + AHV_LINUX_ID + ")",
    cred=LinuxCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)

# Linux AHV VM Endpoint with Dynamic filter category equal filter
linux_ahv_dynamic_vm_endpoint5 = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="categories==cat1:value1",
    cred=LinuxCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)

linux_vmware_static_vm_endpoint = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    values=[VMWARE_LINUX_ID],
    cred=LinuxCred,
    account=Account.VMWare("vmware"),
    provider_type=ENDPOINT_PROVIDER.VMWARE,
)
linux_vmware_dynamic_vm_endpoint1 = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="tags==urn:vmomi:InventoryServiceTag:16edada7-2ed8-4953-b8b2-74f3093559af:GLOBAL",
    cred=LinuxCred,
    account=Account.VMWare("vmware"),
    provider_type=ENDPOINT_PROVIDER.VMWARE,
)
linux_vmware_dynamic_vm_endpoint2 = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="name==vm*",
    cred=LinuxCred,
    account=Account.VMWare("vmware"),
    provider_type=ENDPOINT_PROVIDER.VMWARE,
)

windows_ahv_static_vm_endpoint = Endpoint.Windows.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    value=[AHV_WINDOWS_ID],
    cred=WindowsCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)
windows_ahv_dynamic_vm_endpoint1 = Endpoint.Windows.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="category==cat1:value2",
    cred=WindowsCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)
windows_ahv_dynamic_vm_endpoint2 = Endpoint.Windows.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="category==name==windows.*",
    cred=WindowsCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)

windows_vmware_static_vm_endpoint = Endpoint.Windows.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    value=[VMWARE_WINDOWS_ID],
    cred=WindowsCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)
windows_vmware_dynamic_vm_endpoint1 = Endpoint.Windows.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="tags==urn:vmomi:InventoryServiceTag:16edada7-2ed8-4953-b8b2-74f3093559af:GLOBAL",
    cred=WindowsCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
)
windows_vmware_dynamic_vm_endpoint2 = Endpoint.Windows.vm(
    filter_type=ENDPOINT_FILTER.DYNAMIC,
    filter="name==vm*",
    cred=WindowsCred,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
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
        name="ExecTask", script='''print "Task is Successful"''', target=endpoints[0],
    )


@runbook
def PowershellTask(endpoints=[windows_endpoint]):
    Task.Exec.powershell(
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0],
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
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0],
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
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVStaticEndpoint(endpoints=[linux_ahv_static_vm_endpoint]):
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVDynamicEndpoint1(endpoints=[linux_ahv_dynamic_vm_endpoint1]):
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVDynamicEndpoint2(endpoints=[linux_ahv_dynamic_vm_endpoint2]):
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVDynamicEndpoint3(endpoints=[linux_ahv_dynamic_vm_endpoint3]):
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMAHVDynamicEndpoint4(endpoints=[linux_ahv_dynamic_vm_endpoint4]):
    Task.Exec.ssh(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMVMWareStaticEndpoint(endpoints=[linux_vmware_static_vm_endpoint]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnLinuxVMVMWareDynamicEndpoint1(endpoints=[linux_vmware_dynamic_vm_endpoint1]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )

@runbook
def ShellTaskOnLinuxVMVMWareDynamicEndpoint2(endpoints=[linux_vmware_dynamic_vm_endpoint2]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0],
    )


@runbook
def ShellTaskOnWindowsVMAHVStaticEndpoint(endpoints=[windows_ahv_static_vm_endpoint]):
    Task.Exec.powershell(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0]
    )


@runbook
def ShellTaskOnWindowsVMAHVDynamicEndpoint1(
    endpoints=[windows_ahv_dynamic_vm_endpoint1],
):
    Task.Exec.powershell(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0]
    )


@runbook
def ShellTaskOnWindowsVMAHVDynamicEndpoint2(
    endpoints=[windows_ahv_dynamic_vm_endpoint2],
):
    Task.Exec.powershell(
        name="ExecTask", script='''echo "Task is successful"''', target=endpoints[0]
    )


@runbook
def ShellTaskOnWindowsVMVMWareStaticEndpoint(endpoints=[windows_vmware_static_vm_endpoint]):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0]
    )

@runbook
def ShellTaskOnWindowsVMVMWareDynamicEndpoint1(endpoints=[windows_vmware_dynamic_vm_endpoint1]):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0]
    )

@runbook
def ShellTaskOnWindowsVMVMWareDynamicEndpoint2(endpoints=[windows_vmware_dynamic_vm_endpoint2]):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is successful"''',
        target=endpoints[0]
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
        name="ExecTask", script='''echo "Task is Successful"''', target=endpoints[0],
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
