"""
AHV Blueprint — Macro Support in Substrate Fields
==================================================
A worked, runnable reference for every AHV substrate field that accepts a Calm
macro expression (``@@{variable_name}@@``) as a runtime input, per the
DSL-Changes-for-Custom-Forms spec (section 3.2).

Requires: Calm >= 4.4.0  (numeric / JSON substrate-field macros are gated on this).

------------------------------------------------------------------------------
How to run
------------------------------------------------------------------------------
1. Put guest-OS creds in ``.local/.tests/`` next to this file::

       echo -n 'root'        > .local/.tests/username
       echo -n 'nutanix/4u'  > .local/.tests/password

2. Replace every ``<replace-with-...>`` token below with a real value from your
   setup: image name/uuid, subnet name/uuid, cluster name/uuid. (Look them up with
   ``calm get images`` / ``calm get subnets``, or your local DSL cache.)
3. Compile, create, then launch a chosen profile (``-i`` uses the variable
   defaults; drop it to be prompted)::

       calm compile bp -f ahv_macro_blueprint.py
       calm create  bp -f ahv_macro_blueprint.py --name ahv_macro_bp
       calm launch  bp ahv_macro_bp -a my_app -p NormalMacroProfile -i -w

------------------------------------------------------------------------------
Macro-capable AHV fields
(single source of truth: ``calm.dsl.constants.AHV_MACRO_FIELDS``)
------------------------------------------------------------------------------
  Entity          Field                  Kind           How to macro it
  --------------  ---------------------  -------------  ------------------------------------------
  AhvVm           name                   string         name = "@@{vm_name}@@"
  AhvVm           cluster_reference      json           cluster = "@@{cluster_json}@@"      (dict var)
  AhvVmResources  num_sockets (vCPUs)    int            vCPUs = "@@{vcpus}@@"
  AhvVmResources  num_vcpus_per_socket   int            cores_per_vCPU = "@@{cores}@@"
  AhvVmResources  memory_size_mib        int            memory = "@@{memory_mib}@@"
  AhvVmResources  power_state            string         power_state = "@@{power_state}@@"
  AhvVmResources  nic_list               json-per-item  a NIC OBJECT, or a whole-NIC dict-macro entry
  AhvDisk         data_source_reference  json           cloneFromImageService("@@{disk_image_ref}@@") (dict var)
  AhvDisk         disk_size_mib          int            disk_size_mib = "@@{disk_size_mib}@@"
  AhvNic          subnet_reference       json           NormalNic.ingress("@@{subnet_uuid}@@")

------------------------------------------------------------------------------
Validation rules (spec section 3.2)
------------------------------------------------------------------------------
* String field : a bare macro ``@@{...}@@`` or a literal string.
* INT field    : a bare macro ``@@{...}@@`` or a non-negative integer.
* JSON field   : a full object dict, OR a bare macro that resolves to one (fed by
                 a ``CalmVariable.Simple.dictionary`` runtime variable).
* Arbitrary non-macro strings in a numeric field are rejected by the server.

------------------------------------------------------------------------------
Example JSON object values (what each dict variable should resolve to)
Replace the ids/names with your own (``calm get clusters`` / ``images`` / ``subnets``).
------------------------------------------------------------------------------
* cluster_reference (AhvVm.cluster):
    {"kind": "cluster", "name": "auto_cluster_nested_6a479f4192fce9e853a8ab2f",
     "uuid": "000655c3-f365-f042-7e7b-5254009f04f1"}
* data_source_reference (disk image):
    {"kind": "image", "uuid": "e57c4b80-b695-4afe-b45b-08695eb697c2",
     "name": "Centos7HadoopMaster.qcow2"}
* nic_list item (whole NIC / subnet_reference):
    {"subnet_reference": {"type": "", "kind": "subnet", "name": "vlan.0",
     "uuid": "7b8b48fe-59c4-4e62-8366-a78f25a99a03"}}

------------------------------------------------------------------------------
Three gotchas that trip people up (and why)
------------------------------------------------------------------------------
* INT field + macro  -> the server resolves the value at runtime and SKIPS the
  GiB->MiB conversion the DSL normally applies. So put the final unit (MiB for
  memory/disk size) in the variable's default value.
* DISK image macro   -> macro the disk's ``data_source_reference`` (a dict
  ``{"kind":"image","uuid":...}``), NOT an image-NAME string. A name string
  resolves to a bare value the server can't turn into a reference, so the disk is
  created with no image (no OS).                                    [ENG-949632]
* WHOLE-disk macro   -> ``disks = ["@@{disk}@@"]`` is NOT supported: the server
  costs disks per item (it reads ``disk_size_mib`` on each disk), which fails on a
  bare macro string and returns HTTP 500 at create. Use the per-item
  ``data_source_reference`` form instead. NICs / cluster ARE fine as whole-object
  macros — only disks are cost-iterated.                            [ENG-949615]

------------------------------------------------------------------------------
Profiles in this blueprint
------------------------------------------------------------------------------
1. NormalProfile       — all literal values; no macros (baseline).
2. NormalMacroProfile  — scalar INT/string macros + the disk image as a dict macro.
3. JsonMacroProfile    — JSON-object macros: disk image ref, whole NIC, cluster.
4. AllMacroProfile     — union of 2 + 3: every macro-capable field at once.
"""

import os  # noqa

from calm.dsl.builtins import *  # noqa

# Credentials
CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")

DefaultCred = basic_cred(
    CRED_USERNAME,
    CRED_PASSWORD,
    name="default_cred",
    type="PASSWORD",
    default=True,
)

# One shared service, but a separate package per profile deployment.
# A Service can be reused across packages; each deployment must reference its own
# Package (same pattern as examples/Redis_Master_Slave).


class AhvMacroService(Service):
    """Minimal service shared across all profiles."""

    pass


class NormalPackage(Package):
    services = [ref(AhvMacroService)]


class NormalMacroPackage(Package):
    services = [ref(AhvMacroService)]


class JsonMacroPackage(Package):
    services = [ref(AhvMacroService)]


class AllMacroPackage(Package):
    services = [ref(AhvMacroService)]


# Profile 1 – NormalProfile: baseline, all literal values (no macros).


class NormalVmResources(AhvVmResources):
    memory = 4  # GiB → compiled to 4096 MiB
    vCPUs = 2
    cores_per_vCPU = 1
    power_state = "ON"
    boot_type = "LEGACY"

    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(
            "Centos7HadoopMaster.qcow2",  # literal image by NAME (resolved at compile)
            bootable=True,
        )
    ]
    nics = [
        AhvVmNic.NormalNic.ingress("vlan.0")
    ]  # literal NIC: subnet by NAME (resolved at compile)


class NormalAhvVm(AhvVm):
    name = "vm-@@{calm_array_index}@@-@@{calm_time}@@"
    resources = NormalVmResources


class NormalSubstrate(Substrate):
    account = Ref.Account("NTNX_LOCAL_AZ")
    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = NormalAhvVm

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=False,
        retries="3",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="10",
        credential=ref(DefaultCred),
    )


class NormalDeployment(Deployment):
    packages = [ref(NormalPackage)]
    substrate = ref(NormalSubstrate)


class NormalProfile(Profile):
    """
    Baseline profile: all AHV substrate fields are literal values.
    No runtime macros; launch asks for no substrate-level inputs.
    """

    deployments = [NormalDeployment]


# Profile 2 – NormalMacroProfile: INT/string macros + disk image as a dict macro.


class NormalMacroVmResources(AhvVmResources):
    memory = "@@{memory_mib}@@"
    vCPUs = "@@{vcpus}@@"
    cores_per_vCPU = "@@{cores}@@"
    power_state = "@@{power_state}@@"
    boot_type = "LEGACY"

    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(
            "@@{disk_image_ref}@@",  # dict var -> data_source_reference (not a name)
            disk_size_mib="@@{disk_size_mib}@@",
            bootable=True,
        )
    ]

    nics = [AhvVmNic.NormalNic.ingress("@@{subnet_uuid}@@")]


class NormalMacroAhvVm(AhvVm):
    # VM name has always accepted macros
    name = "@@{vm_name}@@"
    resources = NormalMacroVmResources


class NormalMacroSubstrate(Substrate):
    account = Ref.Account("NTNX_LOCAL_AZ")
    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = NormalMacroAhvVm

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=False,
        retries="3",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="10",
        credential=ref(DefaultCred),
    )


class NormalMacroDeployment(Deployment):
    packages = [ref(NormalMacroPackage)]
    substrate = ref(NormalMacroSubstrate)


class NormalMacroProfile(Profile):
    """
    INT and string substrate fields driven by macros.

    Each macro maps to a runtime variable below.  At launch Calm substitutes
    the runtime-variable value into the substrate spec before provisioning.

    Macro-capable scalar fields demonstrated:
        vCPUs            (INT)
        cores_per_vCPU   (INT)
        memory           (INT, in MiB)
        disk_size_mib    (INT)
        disk image ref   (JSON dict {kind,uuid} — data_source_reference)
        subnet UUID      (string, inside NIC)
        power_state      (string)
        VM name          (string — always supported)
    """

    deployments = [NormalMacroDeployment]

    # --- Runtime variables (filled by operator at launch) ---

    vm_name = CalmVariable.Simple(
        "vm-@@{calm_array_index}@@-@@{calm_time}@@",
        label="VM Name",
        is_mandatory=True,
        runtime=True,
        description="Name for the provisioned VM.",
    )

    vcpus = CalmVariable.Simple.int(
        "2",
        label="vCPUs",
        is_mandatory=True,
        runtime=True,
        description="Number of virtual CPUs.",
    )

    cores = CalmVariable.Simple.int(
        "1",
        label="Cores per vCPU",
        is_mandatory=True,
        runtime=True,
        description="CPU cores per socket.",
    )

    memory_mib = CalmVariable.Simple.int(
        "4096",
        label="Memory (MiB)",
        is_mandatory=True,
        runtime=True,
        description="Memory in MiB (e.g. 4096 = 4 GiB).",
    )

    disk_size_mib = CalmVariable.Simple.int(
        "51200",
        label="Disk Size (MiB)",
        is_mandatory=False,
        runtime=True,
        description="Primary disk size in MiB (e.g. 51200 = 50 GiB).",
    )

    disk_image_ref = CalmVariable.Simple.dictionary(
        {"kind": "image", "uuid": "<replace-with-image-uuid>"},
        label="Disk Image Reference (JSON)",
        is_mandatory=True,
        runtime=True,
        description="Image data_source_reference {kind, uuid} for the primary disk.",
    )

    subnet_uuid = CalmVariable.Simple(
        "<replace-with-subnet-uuid>",
        label="Subnet UUID",
        is_mandatory=True,
        runtime=True,
        description="UUID of the subnet to attach to the VM NIC.",
    )

    power_state = CalmVariable.WithOptions(
        ["ON", "OFF"],
        default="ON",
        label="Power State",
        is_mandatory=False,
        runtime=True,
        description="Initial power state after VM creation.",
    )


# Profile 3 – JsonMacroProfile: JSON-object macros (disk image ref, whole NIC, cluster).


class JsonMacroVmResources(AhvVmResources):
    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    power_state = "ON"
    boot_type = "LEGACY"

    # Macro the disk image ref (JSON object), not the whole disk. disk_size_mib is
    # required when the image ref is a macro.
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(
            "@@{disk_image_ref}@@",
            disk_size_mib=51200,
            bootable=True,
        )
    ]

    nics = [
        "@@{nic_json}@@"
    ]  # whole-NIC macro is supported (NICs aren't cost-iterated)


class JsonMacroAhvVm(AhvVm):
    name = "vm-@@{calm_array_index}@@-@@{calm_time}@@"
    resources = JsonMacroVmResources
    cluster = "@@{cluster_json}@@"  # whole cluster reference as a JSON macro


class JsonMacroSubstrate(Substrate):
    account = Ref.Account("NTNX_LOCAL_AZ")
    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = JsonMacroAhvVm

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=False,
        retries="3",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="10",
        credential=ref(DefaultCred),
    )


class JsonMacroDeployment(Deployment):
    packages = [ref(JsonMacroPackage)]
    substrate = ref(JsonMacroSubstrate)


class JsonMacroProfile(Profile):
    """JSON-object macros: disk image ref, whole NIC, and cluster reference."""

    deployments = [JsonMacroDeployment]

    disk_image_ref = CalmVariable.Simple.dictionary(
        {"kind": "image", "uuid": "<replace-with-image-uuid>"},
        label="Disk Image Reference (JSON)",
        is_mandatory=True,
        runtime=True,
        description="Image data_source_reference {kind, uuid} for the disk.",
    )

    nic_json = CalmVariable.Simple.dictionary(
        {
            "type": "",
            "nic_type": "NORMAL_NIC",
            "subnet_reference": {
                "type": "",
                "kind": "subnet",
                "name": "<replace-with-subnet-name>",
                "uuid": "<replace-with-subnet-uuid>",
            },
            "network_function_nic_type": "INGRESS",
            "mac_address": "",
            "ip_endpoint_list": [],
            "network_function_chain_reference": None,
            "vpc_reference": None,
        },
        label="NIC (JSON)",
        is_mandatory=True,
        runtime=True,
        description="Full AHV NIC spec as a JSON object.",
    )

    cluster_json = CalmVariable.Simple.dictionary(
        {
            "type": "",
            "kind": "cluster",
            "name": "<replace-with-cluster-name>",
            "uuid": "<replace-with-cluster-uuid>",
        },
        label="Cluster (JSON)",
        is_mandatory=True,
        runtime=True,
        description="Cluster reference as a JSON object.",
    )


# Profile 4 – AllMacroProfile: union of NormalMacroProfile + JsonMacroProfile.


class AllMacroVmResources(AhvVmResources):
    memory = "@@{memory_mib}@@"
    vCPUs = "@@{vcpus}@@"
    cores_per_vCPU = "@@{cores}@@"
    power_state = "@@{power_state}@@"
    boot_type = "LEGACY"

    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(
            "@@{disk_image_ref}@@",
            disk_size_mib=51200,
            bootable=True,
        )
    ]

    nics = ["@@{nic}@@"]


class AllMacroAhvVm(AhvVm):
    # VM name macro (always supported)
    name = "@@{vm_name}@@"
    resources = AllMacroVmResources
    cluster = "@@{cluster}@@"


class AllMacroSubstrate(Substrate):
    account = Ref.Account("NTNX_LOCAL_AZ")
    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = AllMacroAhvVm

    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=False,
        retries="3",
        connection_port=22,
        address="@@{platform.status.resources.nic_list[0].ip_endpoint_list[0].ip}@@",
        delay_secs="10",
        credential=ref(DefaultCred),
    )


class AllMacroDeployment(Deployment):
    packages = [ref(AllMacroPackage)]
    substrate = ref(AllMacroSubstrate)


class AllMacroProfile(Profile):
    """Every macro-capable substrate field at once (union of profiles 2 + 3)."""

    deployments = [AllMacroDeployment]

    # --- Scalar runtime variables ---

    vm_name = CalmVariable.Simple(
        "vm-@@{calm_array_index}@@-@@{calm_time}@@",
        label="VM Name",
        is_mandatory=True,
        runtime=True,
        description="Name for the provisioned VM.",
    )

    vcpus = CalmVariable.Simple.int(
        "2",
        label="vCPUs",
        is_mandatory=True,
        runtime=True,
        description="Number of virtual CPUs.",
    )

    cores = CalmVariable.Simple.int(
        "1",
        label="Cores per vCPU",
        is_mandatory=True,
        runtime=True,
        description="CPU cores per socket.",
    )

    memory_mib = CalmVariable.Simple.int(
        "4096",
        label="Memory (MiB)",
        is_mandatory=True,
        runtime=True,
        description="Memory in MiB (e.g. 4096 = 4 GiB).",
    )

    power_state = CalmVariable.WithOptions(
        ["ON", "OFF"],
        default="ON",
        label="Power State",
        is_mandatory=False,
        runtime=True,
        description="Initial power state after VM creation.",
    )

    # --- JSON runtime variables (full object replacements) ---

    cluster = CalmVariable.Simple.dictionary(
        {
            "type": "",
            "kind": "cluster",
            "name": "<replace-with-cluster-name>",
            "uuid": "<replace-with-cluster-uuid>",
        },
        label="Cluster (JSON)",
        is_mandatory=True,
        runtime=True,
        description=(
            "Cluster reference as a JSON object. "
            "Resolved into cluster_reference on the AHV VM at launch."
        ),
    )

    disk_image_ref = CalmVariable.Simple.dictionary(
        {"kind": "image", "uuid": "<replace-with-image-uuid>"},
        label="Disk Image Reference (JSON)",
        is_mandatory=True,
        runtime=True,
        description=(
            "Image data_source_reference {kind, uuid} as a JSON object. "
            "Resolved into the bootable disk data_source_reference at launch."
        ),
    )

    nic = CalmVariable.Simple.dictionary(
        {
            "type": "",
            "nic_type": "NORMAL_NIC",
            "subnet_reference": {
                "type": "",
                "kind": "subnet",
                "name": "<replace-with-subnet-name>",
                "uuid": "<replace-with-subnet-uuid>",
            },
            "network_function_nic_type": "INGRESS",
            "mac_address": "",
            "ip_endpoint_list": [],
            "network_function_chain_reference": None,
            "vpc_reference": None,
        },
        label="NIC (JSON)",
        is_mandatory=True,
        runtime=True,
        description=(
            "Full AHV NIC spec as a JSON object. "
            "Replaces the single entry in the nic_list."
        ),
    )


# ===========================================================================
# Blueprint
# ===========================================================================


class AhvMacroBlueprint(Blueprint):
    """
    AHV Blueprint demonstrating macro support in substrate fields.

    Profiles
    --------
    NormalProfile      — baseline; all literal values.
    NormalMacroProfile — scalar INT / string fields driven by macros.
    JsonMacroProfile   — JSON-object fields (disk, NIC, cluster) as macros.
    AllMacroProfile    — every macro-capable field from spec section 3.2.

    Requires Calm >= 4.4.0 for macro support in numeric substrate fields.
    """

    services = [AhvMacroService]
    packages = [
        NormalPackage,
        NormalMacroPackage,
        JsonMacroPackage,
        AllMacroPackage,
    ]
    substrates = [
        NormalSubstrate,
        NormalMacroSubstrate,
        JsonMacroSubstrate,
        AllMacroSubstrate,
    ]
    profiles = [
        NormalProfile,
        NormalMacroProfile,
        JsonMacroProfile,
        AllMacroProfile,
    ]
    credentials = [DefaultCred]
