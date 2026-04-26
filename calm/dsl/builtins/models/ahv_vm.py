import sys

from distutils.version import LooseVersion as LV

from .calm_ref import Ref
from .entity import EntityType, Entity
from .validator import PropertyValidator
from .provider_spec import ProviderSpecType
from .helper import common as common_helper
from .macro_helper import has_macro, validate_ahv_macro_fields
from calm.dsl.constants import MACRO_SUPPORT_AHV_SPEC_MIN_VERSION
from calm.dsl.store.version import Version
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# AHV VM Resources


class AhvVmResourcesType(EntityType):
    __schema_name__ = "AhvVmResources"
    __openapi_type__ = "vm_ahv_resources"

    def compile(cls):
        cdict = super().compile()

        validate_ahv_macro_fields(cdict, "AhvVmResources")

        ADAPTER_INDEX_MAP = {"SCSI": 0, "PCI": 0, "IDE": 0, "SATA": 0}

        # Traverse over disks and modify the adapter index in disk address
        # Get boot config from disks also
        boot_config = {}
        disk_list = cdict.get("disk_list", [])
        for disk in disk_list:
            # A whole-disk JSON variable macro (e.g. "@@{disk}@@") is a plain string.
            # It has no .device_properties or .bootable attributes; skip adapter-index
            # assignment and boot-config detection — the server resolves it at runtime.
            if has_macro(disk):
                continue

            device_prop = disk.device_properties.get_dict()
            adapter_type = device_prop["disk_address"]["adapter_type"]

            device_prop["disk_address"]["device_index"] = ADAPTER_INDEX_MAP[
                adapter_type
            ]
            ADAPTER_INDEX_MAP[adapter_type] += 1
            disk.device_properties = device_prop

            if disk.bootable and not boot_config:
                boot_config = {
                    "boot_device": {"disk_address": device_prop["disk_address"]}
                }

            elif disk.bootable and boot_config:
                raise ValueError("More than one bootable disks found")

        # Converting memory from GiB to MiB.
        # When memory is a macro string the server resolves it at runtime; skip arithmetic.
        memory = cdict.get("memory_size_mib")
        if has_macro(memory):
            calm_version = Version.get_version("Calm")
            if calm_version and LV(calm_version) < LV(
                MACRO_SUPPORT_AHV_SPEC_MIN_VERSION
            ):
                err_msg = (
                    f"Macro expressions in memory_size_mib require Calm >= "
                    f"{MACRO_SUPPORT_AHV_SPEC_MIN_VERSION} "
                    f"(current: {calm_version})"
                )
                LOG.error(err_msg)
                sys.exit(err_msg)
        else:
            cdict["memory_size_mib"] = memory * 1024

        # Merging boot_type to boot_config
        cdict["boot_config"] = boot_config
        boot_type = cdict.pop("boot_type", None)
        if boot_type == "UEFI":
            cdict["boot_config"]["boot_type"] = "UEFI"
        elif boot_type == "SECURE_BOOT":
            cdict["boot_config"]["boot_type"] = "SECURE_BOOT"

        if not cdict["boot_config"]:
            cdict.pop("boot_config", None)

        # Merging vtpm_enabled to vtpm_config
        calm_version = Version.get_version("Calm")
        if LV(calm_version) >= LV("4.2.0"):
            vtpm_config = {"vtpm_enabled": cdict.pop("vtpm_enabled", False)}
            cdict["vtpm_config"] = vtpm_config
            if boot_type == "LEGACY":
                cdict.pop("vtpm_config", None)

        serial_port_list = []
        if cdict.get("serial_port_list"):
            for ind, connection_status in cdict["serial_port_list"].items():
                if not isinstance(ind, int):
                    raise TypeError("index {} is not of type integer".format(ind))

                if not isinstance(connection_status, bool):
                    raise TypeError(
                        "connection status {} is not of type bool".format(
                            connection_status
                        )
                    )

                serial_port_list.append(
                    {"index": ind, "is_connected": connection_status}
                )

        cdict["serial_port_list"] = serial_port_list

        return cdict

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        return cdict

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):
        validate_ahv_macro_fields(cdict, "AhvVmResources", flow="decompile")

        # Check for serial ports
        serial_port_list = cdict.pop("serial_port_list", [])
        serial_port_dict = {}
        for sp in serial_port_list:
            serial_port_dict[sp["index"]] = sp["is_connected"]

        cdict["serial_port_list"] = serial_port_dict

        if not cdict.get("guest_customization", None):
            cdict.pop("guest_customization", None)

        return super().decompile(cdict, prefix=prefix)


class AhvVmResourcesValidator(PropertyValidator, openapi_type="vm_ahv_resources"):
    __default__ = None
    __kind__ = AhvVmResourcesType


def ahv_vm_resources(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvVmResourcesType(name, bases, kwargs)


AhvVmResources = ahv_vm_resources()


# AHV VM


class AhvVmType(ProviderSpecType):
    __schema_name__ = "AhvVm"
    __openapi_type__ = "vm_ahv"

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        if "__name__" in cdict:
            cdict["__name__"] = "{}{}".format(prefix, cdict["__name__"])

        return cdict

    def compile(cls):
        cdict = super().compile()

        validate_ahv_macro_fields(cdict, "AhvVm")

        vpc_name, network_type = None, None

        for nic in cdict["resources"].nics:
            # A whole-NIC JSON variable macro (e.g. "@@{nic}@@") is a plain string.
            # It has no .vpc_reference or .subnet_reference attributes; the server
            # resolves the full NIC object at runtime, so skip network-type validation.
            if has_macro(nic):
                continue

            if nic.vpc_reference:
                if not network_type:
                    network_type = "OVERLAY"
                elif network_type != "OVERLAY":
                    LOG.error(
                        "Network type mismatch - all subnets must either be vLANs or overlay subnets"
                    )
                    sys.exit("Network type mismatch")
                if "@@{" not in nic.vpc_reference["name"]:
                    if not vpc_name:
                        vpc_name = nic.vpc_reference["name"]
                    elif vpc_name != nic.vpc_reference["name"]:
                        LOG.error(
                            "VPC mismatch - all overlay subnets should belong to the same VPC"
                        )
                        sys.exit("VPC mismatch")

            if nic.subnet_reference and nic.subnet_reference["cluster"]:
                if not network_type:
                    network_type = "VLAN"
                elif network_type != "VLAN":
                    LOG.error(
                        "Network type mismatch - all subnets must either be vLANs or overlay subnets"
                    )
                    sys.exit("Network type mismatch")

                # if not cdict["cluster_reference"]:
                #    cluster = Ref.Cluster(name=nic.subnet_reference["cluster"])
                #    cdict["cluster_reference"] = cluster
                #    cls.cluster = cluster

        return cdict


class AhvVmValidator(PropertyValidator, openapi_type="vm_ahv"):
    __default__ = None
    __kind__ = AhvVmType


def ahv_vm(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvVmType(name, bases, kwargs)


AhvVm = ahv_vm()
