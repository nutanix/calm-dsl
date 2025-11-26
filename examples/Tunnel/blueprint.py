"""
Generated blueprint DSL (.py)
"""

import json  # no_qa
import os  # no_qa

from calm.dsl.builtins import CalmTask as CalmVarTask
from calm.dsl.builtins import *  # no_qa
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import read_local_file

# Secret Variables
BP_CRED_cred_PASSWORD = "dummy_password"

# Credentials
BP_CRED_cred = basic_cred(
    "admin",
    BP_CRED_cred_PASSWORD,
    name="cred",
    type="PASSWORD",
    default=True,
)

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]
TUNNEL_2 = DSL_CONFIG["TUNNELS"]["TUNNEL_2"]["NAME"]

class Service1(Service):

    pass


class DNDvmcalm_timeResources(AhvVmResources):

    memory = 2
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService("CalmTunnelVM.qcow2", bootable=True)
    ]
    nics = [
        AhvVmNic.NormalNic.ingress(
            "vlan.0", cluster="auto_cluster_nested_6851daf8360236027177f736"
        )
    ]

    power_state = "ON"
    boot_type = "LEGACY"


class DNDvmcalm_time(AhvVm):

    name = "DND-vm-@@{calm_time}@@"
    resources = DNDvmcalm_timeResources
    cluster = Ref.Cluster(name="auto_cluster_nested_6851daf8360236027177f736")


class VM1(Substrate):

    account = Ref.Account("GPC2")
    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = DNDvmcalm_time

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=True,
        retries="5",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="60",
        credential=ref(BP_CRED_cred),
    )

    @action
    def __pre_create__(type="fragment"):

        CalmTask.Exec.escript.py3(
            name="Task1",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
            target=ref(VM1),
        )

    @action
    def __post_create__(type="fragment"):

        CalmTask.Exec.escript.py3(
            name="Task1",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            target=ref(VM1),
        )

    @action
    def __post_delete__(type="fragment"):

        CalmTask.Exec.escript.py3(
            name="Task1",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
            target=ref(VM1),
        )


class Config1_Update_ConfigAttrs97a14304(AhvUpdateConfigAttrs):

    disks = [
        PatchField.Ahv.Disks.modify(
            index=0, editable=False, operation="equal", value="8"
        )
    ]


class Package1(Package):

    services = [ref(Service1)]

    @action
    def __install__(type="system"):

        CalmTask.Exec.escript.py3(
            name="Task1",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            target=ref(Service1),
        )

    @action
    def __uninstall__(type="system"):

        CalmTask.Exec.escript.py3(
            name="Task1",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
            target=ref(Service1),
        )


class deployment_4ef45377(Deployment):

    min_replicas = "1"
    max_replicas = "1"
    default_replicas = "1"

    packages = [ref(Package1)]
    substrate = ref(VM1)


class Default(Profile):

    deployments = [deployment_4ef45377]
    patch_list = [
        AppEdit.UpdateConfig(
            name="Config1",
            target=ref(deployment_4ef45377),
            patch_attrs=Config1_Update_ConfigAttrs97a14304,
        )
    ]
    restore_configs = [
        AppProtection.RestoreConfig.Ahv(
            name="Restore_ConfigSnapshot config",
            target=ref(deployment_4ef45377),
            delete_vm_post_restore=False,
        )
    ]
    snapshot_configs = [
        AppProtection.SnapshotConfig.Ahv(
            name="Snapshot_ConfigSnapshot config",
            target=ref(deployment_4ef45377),
            num_of_replicas="ONE",
            restore_config=ref(restore_configs[0]),
            snapshot_location_type="LOCAL",
        )
    ]

    HTTPPostVariable = CalmVariable.WithOptions.FromTask(
        CalmVarTask.HTTP.post(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"http_post_variable": "$.api_version"},
            name="",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            body="{}",
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    )

    EscriptVariable = CalmVariable.WithOptions.FromTask(
        CalmVarTask.Exec.escript.py3(
            name="",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
        ),
        label="",
        is_mandatory=False,
        is_hidden=False,
        description="",
    )

    @action
    def Snapshot_Snapshotconfig(
        name="Snapshot_Snapshot config",
    ):

        EscriptVairbale = CalmVariable.WithOptions.FromTask(
            CalmVarTask.Exec.escript.py3(
                name="",
                script="print('Hello World')",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )
        HTTPVariable = CalmVariable.WithOptions.FromTask(
            CalmVarTask.HTTP.post(
                "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
                headers={},
                secret_headers={},
                content_type="application/json",
                verify=False,
                response_code_status_map=[
                    HTTPResponseHandle.ResponseCode(
                        status=HTTPResponseHandle.TASK_STATUS.Success,
                        code_ranges=[{"start_code": 200, "end_code": 200}],
                    ),
                ],
                response_paths={"HTTP_variable": "$.api_version"},
                name="",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
                body="{}",
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )

        CalmTask.ConfigExec(
            name="Snapshot_ConfigSnapshot config_Task",
            config=ref(Default.snapshot_configs[0]),
        )

        CalmTask.Exec.escript.py3(
            name="Task2",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
            target=ref(Service1),
        )

    @action
    def Restore_Snapshotconfig(
        name="Restore_Snapshot config",
    ):

        CalmTask.ConfigExec(
            name="Restore_ConfigSnapshot config_Task",
            config=ref(Default.restore_configs[0]),
        )

        CalmTask.Exec.escript.py3(
            name="Task2",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            target=ref(Service1),
        )

    @action
    def UntitledAction3(
        name="Untitled Action3",
    ):

        Escript_variable = CalmVariable.WithOptions.FromTask(
            CalmVarTask.Exec.escript.py3(
                name="",
                script="print('Hello World')",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )

        CalmTask.Exec.escript.py3(
            name="Task1",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            target=ref(Service1),
        )


class bp_with_tunnels(Blueprint):

    services = [Service1]
    packages = [Package1]
    substrates = [VM1]
    profiles = [Default]
    credentials = [BP_CRED_cred]


class BpMetadata(Metadata):

    categories = {"TemplateType": "Vm"}
    project = Ref.Project("default")
