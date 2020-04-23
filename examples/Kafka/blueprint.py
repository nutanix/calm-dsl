# Calm DSL for Kafka (2.5.0) on AHV

import os

from calm.dsl.builtins import *  # no_qa


# Get env variables
# read_env() reads from .env file present in blueprint top-level
# directory and returns a dict of blueprint env variables and os env variables.
# If it does not exist, it returns a dict of os env present in os.environ.
# Custom env file location can also be given with relpath param.
# relpath will look for file relative to blueprint top-level directory.
# Examples:
#   read_env()
#   read_env(relpath=".env2")
#   read_env(relpath="env/dev")

ENV = read_env()

CENTOS_USER = ENV.get("CENTOS_USER", "centos")
CENTOS_IMAGE_SOURCE = ENV.get(
    "CENTOS_IMAGE_SOURCE", "http://download.nutanix.com/calm/CentOS-7-x86_64-1810.qcow2"
)
CENTOS_SSH_PRIVATE_KEY_NAME = ENV.get("CENTOS_SSH_PRIVATE_KEY_NAME", "centos")
CENTOS_SSH_PUBLIC_KEY_NAME = ENV.get("CENTOS_SSH_PUBLIC_KEY_NAME", "centos_pub")

AHV_NIC_NAME = ENV.get("AHV_NIC_NAME", "vlan.0")
AHV_MEM = ENV.get("AHV_MEM", "4")

KAFKA_URL = ENV.get(
    "KAFKA_URL", "http://www-us.apache.org/dist/kafka/2.5.0/kafka_2.12-2.5.0.tgz"
)
ZOOKEEPER_DATA_DIR = ENV.get("ZOOKEEPER_DATA_DIR", "/home/centos/zookeepeer/data/")
KAFKA_LOG_DIRS = ENV.get("KAFKA_LOG_DIRS", "/var/log/kafka-logs")
NUMBER_OF_PARTITION = ENV.get("NUMBER_OF_PARTITION", "2")
NUMBER_OF_NODES = ENV.get("NUMBER_OF_NODES", "3")


# SSH Credentials
# read_local_file() reads file from .local folder.
# If it does not exist, it reads from [LOCAL_DIR] location given in ~/.calm/init.ini.

CENTOS_KEY = read_local_file(CENTOS_SSH_PRIVATE_KEY_NAME)
CENTOS_PUBLIC_KEY = read_local_file(CENTOS_SSH_PUBLIC_KEY_NAME)
CENTOS_CRED = basic_cred(
    CENTOS_USER, CENTOS_KEY, name="Centos", type="KEY", default=True,
)

# OS Image details for VM
CENTOS_PACKAGE = vm_disk_package(
    name="centos_disk", config={"image": {"source": CENTOS_IMAGE_SOURCE}},
)


class Kafka(Service):
    @action
    def __start__():

        CalmTask.Exec.ssh(name="Start kafka", filename="scripts/Startkafka.sh")


class KafkaAhvVmResources(AhvVmResources):

    memory = int(AHV_MEM)
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(CENTOS_PACKAGE, bootable=True),
    ]
    nics = [AhvVmNic.DirectNic.ingress(AHV_NIC_NAME)]

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

        CalmTask.Exec.ssh(name="Install Java", filename="scripts/InstallJava.sh")
        CalmTask.Exec.ssh(name="Install Kafka", filename="scripts/InstallKafka.sh")
        CalmTask.Exec.ssh(name="Configure Kafka", filename="scripts/ConfigureKafka.sh")


class KafkaAhvDeployment(Deployment):

    min_replicas = NUMBER_OF_NODES
    max_replicas = NUMBER_OF_NODES

    packages = [ref(KafkaPackage)]
    substrate = ref(KafkaAhvSubstrate)


class Ahv(Profile):

    deployments = [KafkaAhvDeployment]

    KAFKA_URL = CalmVariable.Simple(KAFKA_URL)
    ZOOKEEPER_DATA_DIR = CalmVariable.Simple(ZOOKEEPER_DATA_DIR)
    KAFKA_LOG_DIRS = CalmVariable.Simple(KAFKA_LOG_DIRS)
    NUMBER_OF_PARTITIONS = CalmVariable.Simple(NUMBER_OF_PARTITION)


class KafkaBlueprint(Blueprint):
    """Three node Kafka Cluster"""

    services = [Kafka]
    packages = [KafkaPackage, CENTOS_PACKAGE]
    substrates = [KafkaAhvSubstrate]
    profiles = [Ahv]
    credentials = [CENTOS_CRED]
