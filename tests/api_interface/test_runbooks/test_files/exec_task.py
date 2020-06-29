"""
Calm Runbook Sample for running http tasks
"""
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask as Task, basic_cred
from calm.dsl.builtins import CalmEndpoint, ref

linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="endpoint_cred")

linux_endpoint = CalmEndpoint.Linux.ip([linux_ip], cred=LinuxCred)
linux_endpoint_with_wrong_cred = CalmEndpoint.Linux.ip([linux_ip], cred=WindowsCred)
multiple_linux_endpoint = CalmEndpoint.Linux.ip([linux_ip, linux_ip], cred=LinuxCred)

windows_endpoint = CalmEndpoint.Windows.ip([windows_ip], cred=WindowsCred)
windows_endpoint_with_wrong_cred = CalmEndpoint.Windows.ip([windows_ip], cred=LinuxCred)
multiple_windows_endpoint = CalmEndpoint.Windows.ip(
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
        name="ExecTask",
        script='''print "Task is Successful"''',
        target=ref(multiple_linux_endpoint),
    )


@runbook
def PowershellTask(endpoints=[windows_endpoint]):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(windows_endpoint),
    )


@runbook
def SetVariableOnPowershell(
    endpoints=[windows_endpoint], default_target=ref(windows_endpoint)
):
    Task.SetVariable.powershell(
        name="SetVariableTask",
        script='''echo "task_state=Successful"''',
        variables=["task_state"],
    )
    Task.Exec.powershell(name="ExecTask", script='''echo "Task is @@{task_state}@@"''')


@runbook
def PowershellOnMultipleIPs(endpoints=[multiple_windows_endpoint]):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(multiple_windows_endpoint),
    )


@runbook
def PowershellWithCredOverwrite(
    endpoints=[windows_endpoint_with_wrong_cred], credentials=[WindowsCred]
):
    Task.Exec.powershell(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(windows_endpoint_with_wrong_cred),
        cred=WindowsCred,
    )


@runbook
def ShellTask(endpoints=[linux_endpoint]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(linux_endpoint),
    )


@runbook
def SetVariableOnShell(endpoints=[linux_endpoint], default_target=ref(linux_endpoint)):
    Task.SetVariable.ssh(
        name="SetVariableTask",
        script='''echo "task_state=Successful"''',
        variables=["task_state"],
    )
    Task.Exec.ssh(name="ExecTask", script='''echo "Task is @@{task_state}@@"''')


@runbook
def ShellOnMultipleIPs(endpoints=[multiple_linux_endpoint]):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(multiple_linux_endpoint),
    )


@runbook
def ShellWithCredOverwrite(
    endpoints=[linux_endpoint_with_wrong_cred], credentials=[LinuxCred]
):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "Task is Successful"''',
        target=ref(linux_endpoint_with_wrong_cred),
        cred=LinuxCred,
    )


@runbook
def PowershellTaskWithoutTarget():
    Task.Exec.powershell(name="ExecTask", script='''echo "Task is Successful"''')


@runbook
def ShellTaskWithoutTarget():
    Task.Exec.ssh(name="ExecTask", script='''echo "Task is Successful"''')


@runbook
def MacroOnShell(endpoints=[linux_endpoint], default_target=ref(linux_endpoint)):
    Task.Exec.ssh(
        name="ExecTask",
        script='''echo "@@{calm_runbook_name}@@, @@{calm_runbook_uuid}@@ @@{calm_project_name}@@ @@{calm_jwt}@@ @@{calm_date}@@"''',
    )


@runbook
def MacroOnPowershell(
    endpoints=[windows_endpoint], default_target=ref(windows_endpoint)
):
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
