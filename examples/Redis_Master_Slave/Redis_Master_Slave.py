from calm.dsl.builtins import ref, basic_cred, CalmTask
from calm.dsl.builtins import CalmVariable, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec
from calm.dsl.builtins import read_ahv_spec, read_vmw_spec
from calm.dsl.builtins import vm_disk_package
from calm.dsl.builtins import read_local_file

CENTOS_KEY = read_local_file("secrets/private_key")

DefaultCred = basic_cred("centos", CENTOS_KEY, name="CENTOS", type="KEY", default=True)


class RedisMaster(Service):
    """Redis Master Service"""


class AHVMasterPackage(Package):
    """AHV Redis MasterPackage"""

    services = [ref(RedisMaster)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Master_Package.sh",
            cred=ref(DefaultCred),
        )


class AWSMasterPackage(Package):
    """AWS Redis MasterPackage"""

    services = [ref(RedisMaster)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Master_Package.sh",
            cred=ref(DefaultCred),
        )


class VMwareMasterPackage(Package):
    """VMware Redis MasterPackage"""

    services = [ref(RedisMaster)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Master_Package.sh",
            cred=ref(DefaultCred),
        )


class AzureMasterPackage(Package):
    """"Azure Redis MasterPackage"""

    services = [ref(RedisMaster)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Master_Package.sh",
            cred=ref(DefaultCred),
        )


class GCPMasterPackage(Package):
    """GCP Redis MasterPackage"""

    services = [ref(RedisMaster)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Master_Package.sh",
            cred=ref(DefaultCred),
        )


# Downloadable images for AHV and VMware
AHV_CENTOS_76 = vm_disk_package(
    name="AHV_CENTOS_76", config_file="specs/image_config/ahv_centos.yaml"
)
ESX_CENTOS_76 = vm_disk_package(
    name="ESX_CENTOS_76", config_file="specs/image_config/vmware_centos.yaml"
)


class AHVRedisMasterSubstrate(Substrate):
    provider_spec = read_ahv_spec(
        "specs/substrate/ahv_spec_centos.yaml", disk_packages={1: AHV_CENTOS_76}
    )
    provider_spec.spec["name"] = "Redis_Master-@@{calm_array_index}@@-@@{calm_random}@@"
    os_type = "Linux"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }
    editables = {
        "create_spec": {
            "resources": {
                "nic_list": {},
                "disk_list": True,
                "num_vcpus_per_socket": True,
                "num_sockets": True,
                "memory_size_mib": True,
                "serial_port_list": {},
            }
        }
    }


class AWSRedisMasterSubstrate(Substrate):
    provider_spec = read_provider_spec("specs/substrate/aws_spec_centos.yaml")
    provider_spec.spec["name"] = "Redis_Master-@@{calm_array_index}@@-@@{calm_random}@@"
    provider_type = "AWS_VM"
    os_type = "Linux"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class VMwareRedisMasterSubstrate(Substrate):
    provider_spec = read_vmw_spec(
        "specs/substrate/vmware_spec_centos.yaml", vm_template=ESX_CENTOS_76
    )
    provider_spec.spec["name"] = "Redis_Master-@@{calm_array_index}@@-@@{calm_random}@@"
    provider_type = "VMWARE_VM"
    os_type = "Linux"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class AzureRedisMasterSubstrate(Substrate):
    provider_spec = read_provider_spec("specs/substrate/azure_spec_centos.yaml")
    provider_spec.spec["name"] = "Redis_Master-@@{calm_array_index}@@-@@{calm_random}@@"
    provider_type = "AZURE_VM"
    os_type = "Linux"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class GCPRedisMasterSubstrate(Substrate):
    provider_spec = read_provider_spec("specs/substrate/gcp_spec_centos.yaml")
    provider_spec.spec["resources"]["sshKeys"] = [read_local_file("secrets/public_key")]
    os_type = "Linux"
    provider_type = "GCP_VM"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "address": "@@{platform.networkInterfaces[0].accessConfigs[0].natIP}@@",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class AHVRedisMasterDeployment(Deployment):
    packages = [ref(AHVMasterPackage)]
    substrate = ref(AHVRedisMasterSubstrate)
    min_replicas = "1"
    max_replicas = "1"


class AWSRedisMasterDeployment(Deployment):
    packages = [ref(AWSMasterPackage)]
    substrate = ref(AWSRedisMasterSubstrate)
    min_replicas = "1"
    max_replicas = "1"


class VMwareRedisMasterDeployment(Deployment):
    packages = [ref(VMwareMasterPackage)]
    substrate = ref(VMwareRedisMasterSubstrate)
    min_replicas = "1"
    max_replicas = "1"


class AzureRedisMasterDeployment(Deployment):
    packages = [ref(AzureMasterPackage)]
    substrate = ref(AzureRedisMasterSubstrate)
    min_replicas = "1"
    max_replicas = "1"


class GCPRedisMasterDeployment(Deployment):
    packages = [ref(GCPMasterPackage)]
    substrate = ref(GCPRedisMasterSubstrate)
    min_replicas = "1"
    max_replicas = "1"


class RedisSlave(Service):
    """Redis Slave Service"""

    dependencies = [
        ref(AHVRedisMasterDeployment),
        ref(AWSRedisMasterDeployment),
        ref(VMwareRedisMasterDeployment),
        ref(AzureRedisMasterSubstrate),
        ref(GCPRedisMasterSubstrate),
    ]


class AHVSlavePackage(Package):
    """AHV Redis SlavePackage"""

    services = [ref(RedisSlave)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Slave_Package.sh",
            cred=ref(DefaultCred),
        )


class AWSSlavePackage(Package):
    """AWS Redis SlavePackage"""

    services = [ref(RedisSlave)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Slave_Package.sh",
            cred=ref(DefaultCred),
        )


class VMwareSlavePackage(Package):
    """VMware Redis SlavePackage"""

    services = [ref(RedisSlave)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Slave_Package.sh",
            cred=ref(DefaultCred),
        )


class AzureSlavePackage(Package):
    """Azure Redis SlavePackage"""

    services = [ref(RedisSlave)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Slave_Package.sh",
            cred=ref(DefaultCred),
        )


class GCPSlavePackage(Package):
    """GCP Redis SlavePackage"""

    services = [ref(RedisSlave)]

    @action
    def __install__():
        CalmTask.Exec.ssh(
            name="PackageInstallTask",
            filename="scripts/Slave_Package.sh",
            cred=ref(DefaultCred),
        )


class AHVRedisSlaveSubstrate(Substrate):
    os_type = "Linux"
    provider_spec = read_ahv_spec(
        "specs/substrate/ahv_spec_centos.yaml", disk_packages={1: AHV_CENTOS_76}
    )
    provider_spec.spec["name"] = "Redis_Slave-@@{calm_array_index}@@-@@{calm_random}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class AWSRedisSlaveSubstrate(Substrate):
    os_type = "Linux"
    provider_type = "AWS_VM"
    provider_spec = read_provider_spec("specs/substrate/aws_spec_centos.yaml")
    provider_spec.spec["name"] = "Redis_Slave-@@{calm_array_index}@@-@@{calm_random}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class VMwareRedisSlaveSubstrate(Substrate):
    os_type = "Linux"
    provider_type = "VMWARE_VM"
    provider_spec = read_vmw_spec(
        "specs/substrate/vmware_spec_centos.yaml", vm_template=ESX_CENTOS_76
    )
    provider_spec.spec["name"] = "Redis_Slave-@@{calm_array_index}@@-@@{calm_random}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class AzureRedisSlaveSubstrate(Substrate):
    os_type = "Linux"
    provider_type = "AZURE_VM"
    provider_spec = read_provider_spec("specs/substrate/azure_spec_centos.yaml")
    provider_spec.spec["name"] = "Redis_Slave-@@{calm_array_index}@@-@@{calm_random}@@"
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class GCPRedisSlaveSubstrate(Substrate):
    os_type = "Linux"
    provider_type = "GCP_VM"
    provider_spec = read_provider_spec("specs/substrate/gcp_spec_centos.yaml")
    provider_spec.spec["resources"]["sshKeys"] = [read_local_file("secrets/public_key")]
    readiness_probe = {
        "disabled": False,
        "delay_secs": "60",
        "connection_type": "SSH",
        "address": "@@{platform.networkInterfaces[0].accessConfigs[0].natIP}@@",
        "connection_port": 22,
        "credential": ref(DefaultCred),
    }


class AHVRedisSlaveDeployment(Deployment):
    packages = [ref(AHVSlavePackage)]
    substrate = ref(AHVRedisSlaveSubstrate)
    min_replicas = "2"
    max_replicas = "4"


class AWSRedisSlaveDeployment(Deployment):
    packages = [ref(AWSSlavePackage)]
    substrate = ref(AWSRedisSlaveSubstrate)
    min_replicas = "2"
    max_replicas = "4"


class VMwareRedisSlaveDeployment(Deployment):
    packages = [ref(VMwareSlavePackage)]
    substrate = ref(VMwareRedisSlaveSubstrate)
    min_replicas = "2"
    max_replicas = "4"


class AzureRedisSlaveDeployment(Deployment):
    packages = [ref(AzureSlavePackage)]
    substrate = ref(AzureRedisSlaveSubstrate)
    min_replicas = "2"
    max_replicas = "4"


class GCPRedisSlaveDeployment(Deployment):
    packages = [ref(GCPSlavePackage)]
    substrate = ref(GCPRedisSlaveSubstrate)
    min_replicas = "2"
    max_replicas = "4"


class Nutanix(Profile):
    """Redis master slave deployment in Nutanix provider"""

    REDIS_CONFIG_PASSWORD = CalmVariable.Simple.Secret(
        "nutanix/4u",
        label="Redis Configuration Password",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [AHVRedisMasterDeployment, AHVRedisSlaveDeployment]

    @action
    def ScaleOut():
        """This action will scale out Redis slaves by given scale out count"""
        Scaleout = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_out(
            "@@{Scaleout}@@",
            target=ref(AHVRedisSlaveDeployment),
            name="Scale out Slave",
        )

    @action
    def ScaleIn():
        """This action will scale in Redis slaves by given scale in count"""
        ScaleIn = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_in(
            "@@{ScaleIn}@@", target=ref(AHVRedisSlaveDeployment), name="Scale in Slave"
        )


class AWS(Profile):
    """Redis master slave deployment in AWS provider"""

    REDIS_CONFIG_PASSWORD = CalmVariable.Simple.Secret(
        "nutanix/4u",
        label="Redis Configuration Password",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [AWSRedisMasterDeployment, AWSRedisSlaveDeployment]

    @action
    def ScaleOut():
        """This action will scale out Redis slaves by given scale out count"""
        Scaleout = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_out(
            "@@{Scaleout}@@",
            target=ref(AWSRedisSlaveDeployment),
            name="Scale out Slave",
        )

    @action
    def ScaleIn():
        """This action will scale in Redis slaves by given scale in count"""
        ScaleIn = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_in(
            "@@{ScaleIn}@@", target=ref(AWSRedisSlaveDeployment), name="Scale in Slave"
        )


class VMware(Profile):
    """Redis master slave deployment in VMware provider"""

    REDIS_CONFIG_PASSWORD = CalmVariable.Simple.Secret(
        "nutanix/4u",
        label="Redis Configuration Password",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [VMwareRedisMasterDeployment, VMwareRedisSlaveDeployment]

    @action
    def ScaleOut():
        """This action will scale out Redis slaves by given scale out count"""
        Scaleout = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_out(
            "@@{Scaleout}@@",
            target=ref(VMwareRedisSlaveDeployment),
            name="Scale out Slave",
        )

    @action
    def ScaleIn():
        """This action will scale in Redis slaves by given scale in count"""
        ScaleIn = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_in(
            "@@{ScaleIn}@@",
            target=ref(VMwareRedisSlaveDeployment),
            name="Scale in Slave",
        )


class Azure(Profile):
    """Redis master slave deployment in Azure provider"""

    REDIS_CONFIG_PASSWORD = CalmVariable.Simple.Secret(
        "nutanix/4u",
        label="Redis Configuration Password",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [AzureRedisMasterDeployment, AzureRedisSlaveDeployment]

    @action
    def ScaleOut():
        """This action will scale out Redis slaves by given scale out count"""
        Scaleout = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_out(
            "@@{Scaleout}@@",
            target=ref(AzureRedisSlaveDeployment),
            name="Scale out Slave",
        )

    @action
    def ScaleIn():
        """This action will scale in Redis slaves by given scale in count"""
        ScaleIn = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_in(
            "@@{ScaleIn}@@",
            target=ref(AzureRedisSlaveDeployment),
            name="Scale in Slave",
        )


class GCP(Profile):
    """Redis master slave deployment in Azure provider"""

    REDIS_CONFIG_PASSWORD = CalmVariable.Simple.Secret(
        "nutanix/4u",
        label="Redis Configuration Password",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [GCPRedisMasterDeployment, GCPRedisSlaveDeployment]

    @action
    def ScaleOut():
        """This action will scale out Redis slaves by given scale out count"""
        Scaleout = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_out(
            "@@{Scaleout}@@",
            target=ref(GCPRedisSlaveDeployment),
            name="Scale out Slave",
        )

    @action
    def ScaleIn():
        """This action will scale in Redis slaves by given scale in count"""
        ScaleIn = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)
        CalmTask.Scaling.scale_in(
            "@@{ScaleIn}@@", target=ref(GCPRedisSlaveDeployment), name="Scale in Slave"
        )


class RedisBlueprint(Blueprint):
    """Accessibility:
    * redis-cli from master host"""

    profiles = [Nutanix, AWS, VMware, Azure, GCP]
    services = [RedisMaster, RedisSlave]
    substrates = [
        AHVRedisMasterSubstrate,
        AHVRedisSlaveSubstrate,
        AWSRedisMasterSubstrate,
        AWSRedisSlaveSubstrate,
        VMwareRedisMasterSubstrate,
        VMwareRedisSlaveSubstrate,
        AzureRedisMasterSubstrate,
        AzureRedisSlaveSubstrate,
        GCPRedisMasterSubstrate,
        GCPRedisSlaveSubstrate,
    ]
    packages = [
        AHVMasterPackage,
        AHVSlavePackage,
        AHV_CENTOS_76,
        ESX_CENTOS_76,
        AWSMasterPackage,
        AWSSlavePackage,
        VMwareMasterPackage,
        VMwareSlavePackage,
        AzureMasterPackage,
        AzureSlavePackage,
        GCPMasterPackage,
        GCPSlavePackage,
    ]
    credentials = [DefaultCred]


def main():
    print(RedisBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
