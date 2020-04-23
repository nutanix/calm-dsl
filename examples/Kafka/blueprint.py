# Calm DSL for Kafka on AHV

import os

from calm.dsl.builtins import *  # no_qa

# SSH Credentials
CENTOS_USER = "centos"
CENTOS_KEY = read_local_file(os.path.join("keys", "centos"))
CENTOS_PUBLIC_KEY = read_local_file(os.path.join("keys", "centos_pub"))
CentosCred = basic_cred(
    CENTOS_USER, CENTOS_KEY, name="Centos", type="KEY", default=True,
)

# OS Image details for VM
CENTOS_IMAGE_SOURCE = "http://download.nutanix.com/calm/CentOS-7-x86_64-1810.qcow2"
CentosPackage = vm_disk_package(
    name="centos_disk", config={"image": {"source": CENTOS_IMAGE_SOURCE}},
)


class Kafka(Service):
    @action
    def __start__():
        """System action for starting an application"""

        CalmTask.Exec.ssh(
            name="Start kafka", filename="scripts/Startkafka.sh", target=ref(Kafka),
        )


class KafkaAhvVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(CentosPackage, bootable=True),
    ]
    nics = [AhvVmNic.DirectNic.ingress("vlan.0")]

    guest_customization = AhvVmGC.CloudInit(
        config={
            "users": [
                {
                    "name": CENTOS_USER,
                    "ssh-authorized-keys": [CENTOS_PUBLIC_KEY],
                    "sudo": ["ALL=(ALL) NOPASSWD:ALL"],
                }
            ]
        }
    )


class KafkaAhvVm(AhvVm):

    resources = KafkaAhvVmResources


class KafkaAhvSubstrate(Substrate):

    provider_spec = KafkaAhvVm


class KafkaPackage(Package):

    services = [ref(Kafka)]

    @action
    def __install__():

        CalmTask.Exec.ssh(
            name="Install Java", filename="scripts/InstallJava.sh",
        )
        CalmTask.Exec.ssh(
            name="Install Kafka", filename="scripts/InstallKafka.sh",
        )
        CalmTask.Exec.ssh(
            name="Configure Kafka", filename="scripts/ConfigureKafka.sh",
        )


class KafkaAhvDeployment(Deployment):
    """_15f245d6_deployment Deployment description"""

    min_replicas = "3"
    max_replicas = "6"

    packages = [ref(KafkaPackage)]
    substrate = ref(KafkaAhvSubstrate)


class Ahv(Profile):
    """Nutanix Profile description"""

    deployments = [KafkaAhvDeployment]

    KAFKA_URL = CalmVariable.Simple(
        "http://www-us.apache.org/dist/kafka/2.1.1/kafka_2.11-2.1.1.tgz",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
    )

    ZOOKEEPER_DATA_DIR = CalmVariable.Simple(
        "/home/centos/zookeepeer/data/",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
    )

    KAFKA_LOG_DIRS = CalmVariable.Simple(
        "/var/log/kafka-logs",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
    )

    NUMBER_OF_PARTITIONS = CalmVariable.Simple(
        "2", label="", is_mandatory=False, is_hidden=False, runtime=True
    )


class KafkaBlueprint(Blueprint):
    """Three node Kafka Cluster"""

    services = [Kafka]
    packages = [KafkaPackage, CentosPackage]
    substrates = [KafkaAhvSubstrate]
    profiles = [Ahv]
    credentials = [CentosCred]
