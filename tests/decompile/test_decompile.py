from calm.dsl.builtins import ref, basic_cred, CalmVariable, CalmTask, action, parallel
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_local_file, vm_disk_package
from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmResources, AhvVm
from calm.dsl.builtins import readiness_probe

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")


Era_Disk = vm_disk_package(
    name="era_disk",
    config={
        # By default image type is set to DISK_IMAGE
        "image": {
            "source": "http://download.nutanix.com/era/1.1.1/ERA-Server-build-1.1.1-340d9db1118eac81219bec98507d4982045d8799.qcow2"
        }
    },
)


class MySQLService(Service):
    """Sample mysql service"""

    name = "my sql service"
    ENV = CalmVariable.Simple("DEV")

    @action
    def __create__():
        "System action for creating an application"

        CalmTask.Exec.ssh(name="Task1", script="echo 'Service create in ENV=@@{ENV}@@'")


class MySQLPackage(Package):
    """Example package with variables, install tasks and link to service"""

    name = "my sql package"
    foo = CalmVariable.Simple("bar")
    services = [ref(MySQLService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")


class MyAhvVm1Resources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService("Centos7", bootable=True),
        AhvVmDisk.CdRom.Sata.cloneFromImageService(
            "SQLServer2014SP2-FullSlipstream-x64"
        ),
        AhvVmDisk.CdRom.Ide.cloneFromImageService(
            "SQLServer2014SP2-FullSlipstream-x64"
        ),
        AhvVmDisk.Disk.Scsi.cloneFromImageService("AHV_CENTOS_76"),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(12),
        AhvVmDisk.CdRom.Sata.emptyCdRom(),
        AhvVmDisk.CdRom.Ide.emptyCdRom(),
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(Era_Disk),
    ]
    nics = [AhvVmNic.DirectNic.ingress("vlan.0")]


class MyAhvVm1(AhvVm):

    name = "@@{calm_application_name}@@-@@{calm_array_index}@@"
    resources = MyAhvVm1Resources
    categories = {"AppFamily": "Backup", "AppType": "Default"}


class AHVVMforMySQL(Substrate):
    """AHV VM config given by reading a spec file"""

    name = "ahv vm for sql"
    provider_spec = MyAhvVm1

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=False,
        retries="5",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="0",
    )


class MySQLDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    name = "my sql deployment"
    packages = [ref(MySQLPackage)]
    substrate = ref(AHVVMforMySQL)


class PHPService(Service):
    """Sample PHP service with a custom action"""

    name = "php service"
    # Dependency to indicate PHP service is dependent on SQL service being up
    dependencies = [ref(MySQLService)]

    @action
    def test_action(name="php service test_action"):

        blah = CalmVariable.Simple("2")  # noqa
        CalmTask.Exec.ssh(name="Task2", script='echo "Hello"')
        CalmTask.Exec.ssh(name="Task3", script='echo "Hello again"')


class PHPPackage(Package):
    """Example PHP package with custom install task"""

    name = "php package"

    foo = CalmVariable.Simple("baz")
    services = [ref(PHPService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task4", script="echo @@{foo}@@")


class MyAhvVm2Resources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService("Centos7", bootable=True),
        AhvVmDisk.CdRom.Sata.cloneFromImageService(
            "SQLServer2014SP2-FullSlipstream-x64"
        ),
        AhvVmDisk.CdRom.Ide.cloneFromImageService(
            "SQLServer2014SP2-FullSlipstream-x64"
        ),
        AhvVmDisk.Disk.Scsi.cloneFromImageService("AHV_CENTOS_76"),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(12),
        AhvVmDisk.CdRom.Sata.emptyCdRom(),
        AhvVmDisk.CdRom.Ide.emptyCdRom(),
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(Era_Disk),
    ]
    nics = [AhvVmNic.DirectNic.ingress("vlan.0")]


class MyAhvVm2(AhvVm):

    name = "@@{calm_application_name}@@-@@{calm_array_index}@@"
    resources = MyAhvVm2Resources
    categories = {"AppFamily": "Backup", "AppType": "Default"}


class AHVVMforPHP(Substrate):
    """AHV VM config given by reading a spec file"""

    name = "ahv vm for php substrate"
    provider_spec = MyAhvVm2

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=False,
        retries="5",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="0",
    )


class PHPDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    name = "php deplyment"

    packages = [ref(PHPPackage)]
    substrate = ref(AHVVMforPHP)


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    name = "default profile"

    nameserver = CalmVariable.Simple(DNS_SERVER, label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [MySQLDeployment, PHPDeployment]

    @action
    def test_profile_action(name="test profile action"):
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(MySQLService))
        PHPService.test_action(name="Call Runbook Task")
        with parallel:
            CalmTask.Exec.escript(
                "print 'Hello World!'", name="Test Escript", target=ref(MySQLService)
            )
            CalmTask.SetVariable.escript(
                script="print 'var1=test'",
                name="Test Setvar Escript",
                variables=["var1"],
                target=ref(MySQLService),
            )


class TestDecompile(Blueprint):
    """Calm DSL .NEXT demo"""

    credentials = [basic_cred(CRED_USERNAME, CRED_PASSWORD, default=True)]
    services = [MySQLService, PHPService]
    packages = [MySQLPackage, PHPPackage, Era_Disk]
    substrates = [AHVVMforMySQL, AHVVMforPHP]
    profiles = [DefaultProfile]
