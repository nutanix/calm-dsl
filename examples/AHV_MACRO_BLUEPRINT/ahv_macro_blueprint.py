"""
AHV Blueprint — Macro Support in Substrate Fields
==================================================
Demonstrates all AHV substrate fields that accept Calm macro expressions
(@@{variable_name}@@) as runtime inputs, as per the DSL-Changes-for-Custom-Forms
specification (section 3.2).

Requires: Calm >= 4.4.0

Profiles
--------
1. NormalProfile       — all literal values; no macros (baseline).
2. NormalMacroProfile  — macros in INT / string-typed substrate fields only:
                          vCPUs, cores_per_vCPU, memory, disk_size_mib,
                          disk image name (string in image field), subnet uuid,
                          power_state, VM name.
3. JsonMacroProfile    — macros that replace entire JSON objects:
                          disk (whole disk object), NIC (whole NIC object),
                          cluster (whole cluster reference).
4. AllMacroProfile     — every macro-capable field at once (union of 2 + 3),
                          including categories and disk_size_mib.

Macro validation rules (from spec section 3.2)
-----------------------------------------------
* String fields  : value must be a bare macro  @@{...}@@  or a literal string.
* INT fields     : value must be a bare macro   @@{...}@@  or a non-negative integer.
* JSON fields    : value is a full object dict  OR a bare macro that resolves to one.
* Arbitrary non-macro strings for numeric fields are rejected by the server.
"""

import os  # noqa

from calm.dsl.builtins import *  # noqa

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

CRED_USERNAME = read_local_file("cred_username")
CRED_PASSWORD = read_local_file("cred_password")

DefaultCred = basic_cred(
    CRED_USERNAME,
    CRED_PASSWORD,
    name="default_cred",
    type="PASSWORD",
    default=True,
)

# ---------------------------------------------------------------------------
# Shared service / package (reused by all profiles)
# ---------------------------------------------------------------------------


class AhvMacroService(Service):
    """Minimal service shared across all profiles."""

    pass


class AhvMacroPackage(Package):
    services = [ref(AhvMacroService)]


# ===========================================================================
# Profile 1 – NormalProfile
# All fields are literal values.  This is the baseline "no macro" case.
# ===========================================================================


class NormalVmResources(AhvVmResources):
    memory = 4  # GiB → compiled to 4096 MiB
    vCPUs = 2
    cores_per_vCPU = 1
    power_state = "ON"
    boot_type = "LEGACY"

    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(
            "<replace-with-image-name>",
            bootable=True,
        )
    ]
    nics = [AhvVmNic.NormalNic.ingress("<replace-with-subnet-uuid>")]


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
    packages = [ref(AhvMacroPackage)]
    substrate = ref(NormalSubstrate)


class NormalProfile(Profile):
    """
    Baseline profile: all AHV substrate fields are literal values.
    No runtime macros; launch asks for no substrate-level inputs.
    """

    deployments = [NormalDeployment]


# ===========================================================================
# Profile 2 – NormalMacroProfile
# INT and string substrate fields are driven by runtime macros.
# Supported macro-capable scalar fields (spec section 3.2):
#   vCPUs, cores_per_vCPU, memory (INT)
#   disk_size_mib (INT)
#   disk image name / subnet uuid (existing string-accepting fields)
#   power_state, VM name (string)
# ===========================================================================


class NormalMacroVmResources(AhvVmResources):
    # INT fields — accept macro string at runtime (resolved by server)
    memory = "@@{memory_mib}@@"      # server skips GiB→MiB when value is a macro
    vCPUs = "@@{vcpus}@@"
    cores_per_vCPU = "@@{cores}@@"

    # String field — ON/OFF/ACPI_SHUTDOWN
    power_state = "@@{power_state}@@"

    boot_type = "LEGACY"

    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(
            # image name field already accepts a macro string
            "@@{img_name}@@",
            # disk_size_mib is an INT field — also accepts a macro
            disk_size_mib="@@{disk_size_mib}@@",
            bootable=True,
        )
    ]

    # Subnet UUID inside a NIC is a string field — accepts a macro
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
    packages = [ref(AhvMacroPackage)]
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
        disk image name  (string)
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

    img_name = CalmVariable.Simple(
        "<replace-with-image-name>",
        label="Disk Image Name",
        is_mandatory=True,
        runtime=True,
        description="Name of the AHV image to clone for the primary disk.",
    )

    subnet_uuid = CalmVariable.Simple(
        "<replace-with-subnet-uuid>",
        label="Subnet UUID",
        is_mandatory=True,
        runtime=True,
        description="UUID of the subnet to attach to the VM NIC.",
    )

    power_state = CalmVariable.WithOptions(
        ["ON", "OFF", "ACPI_SHUTDOWN"],
        default="ON",
        label="Power State",
        is_mandatory=False,
        runtime=True,
        description="Initial power state after VM creation.",
    )


# ===========================================================================
# Profile 3 – JsonMacroProfile
# Entire JSON objects are replaced by a single macro string.
# Supported JSON-typed macro fields (spec section 3.2):
#   Disk (whole disk object)       → nics list entry is a macro string
#   NIC  (whole NIC object)        → disk list entry is a macro string
#   Cluster reference              → cluster field on AhvVm is a macro string
# ===========================================================================


class JsonMacroVmResources(AhvVmResources):
    memory = 4  # literal GiB — only the JSON-object fields are macros here
    vCPUs = 2
    cores_per_vCPU = 1
    power_state = "ON"
    boot_type = "LEGACY"

    # Whole disk object replaced by a JSON macro.
    # The server resolves @@{disk_json}@@ to a full disk spec dict at runtime.
    disks = ["@@{disk_json}@@"]

    # Whole NIC object replaced by a JSON macro.
    # The server resolves @@{nic_json}@@ to a full NIC spec dict at runtime.
    nics = ["@@{nic_json}@@"]


class JsonMacroAhvVm(AhvVm):
    name = "vm-@@{calm_array_index}@@-@@{calm_time}@@"
    resources = JsonMacroVmResources

    # Whole cluster reference replaced by a JSON macro.
    # The server resolves @@{cluster_json}@@ to {"kind": "cluster", "uuid": "..."} at runtime.
    cluster = "@@{cluster_json}@@"


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
    packages = [ref(AhvMacroPackage)]
    substrate = ref(JsonMacroSubstrate)


class JsonMacroProfile(Profile):
    """
    JSON-object substrate fields driven by macros.

    Each variable below holds a full JSON object (dict) as its default value.
    At launch the operator can supply a different object; the macro reference
    in the substrate is resolved to the provided dict before provisioning.

    JSON macro-capable fields demonstrated:
        disk_json    — full AHV disk spec object (replaces a disk list entry)
        nic_json     — full AHV NIC spec object  (replaces a NIC list entry)
        cluster_json — full cluster reference     (replaces cluster_reference)
    """

    deployments = [JsonMacroDeployment]

    # --- Runtime variables (dict type — JSON objects) ---

    disk_json = CalmVariable.Simple.dictionary(
        {
            "type": "",
            "kind": "image",
            "name": "<replace-with-image-name>",
            "uuid": "<replace-with-image-uuid>",
        },
        label="Disk (JSON)",
        is_mandatory=True,
        runtime=True,
        description="Full AHV disk spec as a JSON object.",
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


# ===========================================================================
# Profile 4 – AllMacroProfile
# Union of NormalMacroProfile + JsonMacroProfile.
# Every macro-capable AHV substrate field listed in spec section 3.2.
# ===========================================================================


class AllMacroVmResources(AhvVmResources):
    # INT macro fields
    memory = "@@{memory_mib}@@"
    vCPUs = "@@{vcpus}@@"
    cores_per_vCPU = "@@{cores}@@"

    # String macro field
    power_state = "@@{power_state}@@"

    boot_type = "LEGACY"

    # Whole disk object as JSON macro
    disks = ["@@{disk}@@"]

    # Whole NIC object as JSON macro
    nics = ["@@{nic}@@"]


class AllMacroAhvVm(AhvVm):
    # VM name macro (always supported)
    name = "@@{vm_name}@@"
    resources = AllMacroVmResources

    # Whole cluster reference as JSON macro
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
    packages = [ref(AhvMacroPackage)]
    substrate = ref(AllMacroSubstrate)


class AllMacroProfile(Profile):
    """
    All macro-capable AHV substrate fields driven at runtime (spec section 3.2).

    Combines scalar INT/string macros with full JSON-object macros:

    Field              Type    Macro
    -----------------  ------  ---------------------
    VM Name            string  @@{vm_name}@@
    vCPUs              INT     @@{vcpus}@@
    Cores per vCPU     INT     @@{cores}@@
    Memory             INT     @@{memory_mib}@@
    VM Power State     string  @@{power_state}@@
    Cluster            JSON    @@{cluster}@@
    Disk (full object) JSON    @@{disk}@@
    NIC  (full object) JSON    @@{nic}@@
    """

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
        ["ON", "OFF", "ACPI_SHUTDOWN"],
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

    disk = CalmVariable.Simple.dictionary(
        {
            "type": "",
            "kind": "image",
            "name": "<replace-with-image-name>",
            "uuid": "<replace-with-image-uuid>",
        },
        label="Disk (JSON)",
        is_mandatory=True,
        runtime=True,
        description=(
            "Full AHV disk spec as a JSON object. "
            "Replaces the single entry in the disk_list."
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
    packages = [AhvMacroPackage]
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
