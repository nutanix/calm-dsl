import json  # no_qa
import os  # no_qa

from calm.dsl.builtins import *  # no_qa


# Secret Variables
BP_CRED_root_PASSWORD = read_local_file(".tests/password")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
SUBNET_NAME = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]["SUBNETS"][1]["NAME"]
CLUSTER = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]["SUBNETS"][1]["CLUSTER"]

# Credentials
BP_CRED_root = basic_cred(
    "root",
    BP_CRED_root_PASSWORD,
    name="root",
    type="PASSWORD",
    default=True,
)


class Service1(Service):

    pass


class vmcalm_timeResources(AhvVmResources):

    memory = 1
    vCPUs = 1
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService("CentOS-7-cloudinit", bootable=True)
    ]
    nics = [AhvVmNic.NormalNic.ingress(SUBNET_NAME, cluster=CLUSTER)]


class vmcalm_time(AhvVm):

    name = "vm-@@{calm_time}@@"
    resources = vmcalm_timeResources
    cluster = Ref.Cluster(name=CLUSTER)


class VM1(Substrate):

    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = vmcalm_time

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=True,
        retries="5",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="60",
    )


class Package1(Package):

    services = [ref(Service1)]

    @action
    def __uninstall__():

        with parallel() as p0:

            with branch(p0):
                CalmTask.Exec.escript(
                    name="Task1",
                    script="print 'Task1'",
                    target=ref(Service1),
                )

                with parallel() as p1:

                    with branch(p1):
                        CalmTask.Exec.escript(
                            name="Task1_1",
                            script="print 'Task1_1'",
                            target=ref(Service1),
                        )

                    with branch(p1):
                        CalmTask.Exec.escript(
                            name="Task1_2",
                            script="print 'Task1_2'",
                            target=ref(Service1),
                        )

            with branch(p0):
                CalmTask.Exec.escript(
                    name="Task2",
                    script="print 'Task2'",
                    target=ref(Service1),
                )

                CalmTask.Exec.escript(
                    name="Task2_1",
                    script="print 'Task2_1'",
                    target=ref(Service1),
                )


class _7edbded5_deployment(Deployment):

    name = "7edbded5_deployment"
    min_replicas = "1"
    max_replicas = "1"
    default_replicas = "1"

    packages = [ref(Package1)]
    substrate = ref(VM1)


class Default(Profile):

    deployments = [_7edbded5_deployment]


class test_sbp_789987(Blueprint):

    services = [Service1]
    packages = [Package1]
    substrates = [VM1]
    profiles = [Default]
    credentials = [BP_CRED_root]


class BpMetadata(Metadata):

    categories = {"TemplateType": "Vm"}
