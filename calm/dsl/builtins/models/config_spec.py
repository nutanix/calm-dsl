import inspect
import json
import uuid
import os
import sys

from .entity import EntityType, Entity
from .ref import ref
from .utils import read_file
from .validator import PropertyValidator
from .variable import CalmVariable
from calm.dsl.api import get_resource_api, get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


class UpdateConfig:
    def __new__(
        cls,
        name,
        target=None,
        patch_attrs=None,
    ):
        return patch_config_create(name, target, patch_attrs)


class ConfigSpecType(EntityType):
    __schema_name__ = "ConfigSpec"
    __openapi_type__ = "app_config_spec"

    def get_ref(cls, kind=None):
        """Note: app_blueprint_deployment kind to be used for pod deployment"""
        return super().get_ref(kind=ConfigSpecType.__openapi_type__)

    def compile(cls):
        cdict = super().compile()
        if "patch_attrs" not in cdict or len(cdict["patch_attrs"]) == 0:
            cdict.pop("patch_attrs", None)
            return cdict
        attrs = cdict.pop("patch_attrs")[0]
        categories_data = []
        categories = attrs.categories
        for op_category in categories:
            for op in op_category["val"]:
                val = {}
                val["operation"] = op_category["operation"]
                val["value"] = op
                categories_data.append(val)
        memory = attrs.memory
        if memory.min_value:
            memory.min_value = memory.min_value * 1024
        if memory.max_value:
            memory.max_value = memory.max_value * 1024
        if memory.value:
            memory.value = str(int(float(memory.value) * 1024))
        target = cdict["attrs_list"][0]["target_any_local_reference"]
        disk_data = []
        disks = attrs.disks
        adapter_name_index_map = {}
        for disk in disks:
            if disk.disk_operation in ["delete", "modify"]:
                val = target.__self__.substrate.__self__.provider_spec.resources.disks[
                    disk.index
                ].compile()
            elif disk.disk_operation in ["add"]:
                val = disk.disk_value.compile()
            val["operation"] = disk.disk_operation

            dtype = val["device_properties"]["disk_address"]["adapter_type"]
            if disk.operation != "add":
                if dtype not in adapter_name_index_map:
                    adapter_name_index_map[dtype] = 0
                else:
                    adapter_name_index_map[dtype] += 1
                val["device_properties"]["disk_address"][
                    "device_index"
                ] = adapter_name_index_map[dtype]
            if disk.operation == "":
                disk.operation = "equal"
            if disk.value and disk.value != "0":
                val["disk_size_mib"] = {}
                val["disk_size_mib"]["editable"] = disk.editable
                val["disk_size_mib"]["operation"] = disk.operation
                val["disk_size_mib"]["value"] = str(int(float(disk.value) * 1024))
            else:
                prev = val["disk_size_mib"]
                if not isinstance(prev, dict):
                    val["disk_size_mib"] = {}
                    val["disk_size_mib"]["editable"] = disk.editable
                    val["disk_size_mib"]["operation"] = disk.operation
                    val["disk_size_mib"]["value"] = str(prev)
            if disk.min_value:
                val["disk_size_mib"]["min_value"] = disk.min_value * 1024
            if disk.max_value:
                val["disk_size_mib"]["max_value"] = disk.max_value * 1024
            val.pop("bootable", None)
            disk_data.append(val)
        nic_data = []
        nics = attrs.nics
        counter = 1
        for nic in nics:
            if nic.operation in ["delete", "modify"]:
                val = target.__self__.substrate.__self__.provider_spec.resources.nics[
                    int(nic.index)
                ].compile()
            elif nic.operation in ["add"]:
                val = nic.nic_value.compile()
                nic.index = "A{}".format(counter)
                counter += 1
            val["operation"] = nic.operation
            val["editable"] = nic.editable
            val["identifier"] = str(nic.index)
            nic_data.append(val)

        data = {
            "type": "nutanix",
            "nic_delete_allowed": attrs.nic_delete,
            "categories_delete_allowed": attrs.categories_delete,
            "categories_add_allowed": attrs.categories_add,
            "disk_delete_allowed": attrs.disk_delete,
            "num_sockets_ruleset": attrs.numsocket.get_all_attrs(),
            "memory_size_mib_ruleset": memory.get_all_attrs(),
            "num_vcpus_per_socket_ruleset": attrs.vcpu.get_all_attrs(),
            "pre_defined_disk_list": disk_data,
            "pre_defined_nic_list": nic_data,
            "pre_defined_categories": categories_data,
        }
        cdict["attrs_list"][0]["data"] = data
        return cdict


class PatchConfigSpecType(ConfigSpecType):
    pass


class SnapshotConfigSpecType(ConfigSpecType):
    pass


class RestoreConfigSpecType(ConfigSpecType):
    pass


class ConfigSpecValidator(PropertyValidator, openapi_type="app_config_spec"):
    __default__ = None
    __kind__ = ConfigSpecType


CONFIG_SPEC_TYPE_MAP = {
    "snapshot": SnapshotConfigSpecType,
    "restore": RestoreConfigSpecType,
    "patch": PatchConfigSpecType,
}


def _config_spec(config_type="snapshot", **kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    config = CONFIG_SPEC_TYPE_MAP[config_type](name, bases, kwargs)
    return config


def _config_create(config_type="snapshot", **kwargs):
    name = kwargs.get("name", kwargs.get("__name__", None))
    bases = (_config_spec(config_type),)
    config = CONFIG_SPEC_TYPE_MAP[config_type](name, bases, kwargs)
    return config


def patch_config_create(
    name,
    target=None,
    patch_attrs=None,
    description="",
):
    attrs = {
        "target_any_local_reference": target,
        "data": {},
        "uuid": str(uuid.uuid4()),
    }
    kwargs = {
        "name": name,
        "description": description,
        "attrs_list": [attrs],
        "patch_attrs": [patch_attrs],
        "type": "PATCH",
    }
    return _config_create(config_type="patch", **kwargs)


def snapshot_config_create(
    name,
    target=None,
    snapshot_type="CRASH_CONSISTENT",
    num_of_replicas="ONE",
    config_references=[],
    snapshot_location_type="LOCAL",
    policy=None,
    description="",
):
    rule_ref = {}
    if policy:
        rule = policy.pop("rule_uuid", None)
        client = get_api_client()
        res, err = client.app_protection_policy.read(id=policy.get("uuid"))
        if err:
            LOG.error("[{}] - {}".format(err["code"], err["error"]))
            sys.exit("Unable to retrieve protection policy details")

        res = res.json()
        protection_rule_list = res["status"]["resources"]["app_protection_rule_list"]

        rule_ref["kind"] = "app_protection_rule"
        if not rule:
            if protection_rule_list and isinstance(protection_rule_list, list):
                rule_ref["uuid"] = protection_rule_list[0]["uuid"]
                rule_ref["name"] = protection_rule_list[0]["name"]
                if protection_rule_list[0].get(
                    "remote_snapshot_retention_policy", None
                ):
                    snapshot_location_type = "REMOTE"
        else:
            for pr in protection_rule_list:
                if pr.get("uuid") == rule:
                    rule_ref["uuid"] = rule
                    rule_ref["name"] = pr.get("name")
                    if pr.get("remote_snapshot_retention_policy", None):
                        snapshot_location_type = "REMOTE"

        if "uuid" not in rule_ref:
            LOG.error(
                "No Protection Rule {} found under Protection Policy {}".format(
                    rule, res["metadata"]["name"]
                )
            )
            sys.exit("Invalid protection rule")

    if config_references:
        for config_ref in config_references:
            config_ref.__self__.attrs_list[0][
                "snapshot_location_type"
            ] = snapshot_location_type

    attrs = {
        "target_any_local_reference": target,
        "snapshot_location_type": snapshot_location_type,
        "num_of_replicas": num_of_replicas,
    }
    if policy:
        attrs["app_protection_policy_reference"] = policy
        attrs["app_protection_rule_reference"] = rule_ref
    snapshot_name = CalmVariable.Simple(
        name, name="snapshot_name", runtime=True, is_mandatory=True
    )
    snapshot_type = CalmVariable.Simple(
        snapshot_type, name="snapshot_type", runtime=True, is_mandatory=True
    )
    kwargs = {
        "name": name,
        "description": description,
        "attrs_list": [attrs],
        "type": "",  # Set at profile level during compile
        "variables": [snapshot_name, snapshot_type],
        "config_references": config_references,
    }
    return _config_create(config_type="snapshot", **kwargs)


def restore_config_create(
    name,
    target,
    snapshot_location_type="LOCAL",
    delete_vm_post_restore=False,
    description="",
):
    attrs = {
        "target_any_local_reference": target,
        "delete_vm_post_restore": delete_vm_post_restore,
        "snapshot_location_type": snapshot_location_type,
    }
    snapshot_uuids = CalmVariable.Simple(
        "", name="snapshot_uuids", runtime=True, is_mandatory=True
    )
    delete_vm_post_restore = CalmVariable.Simple(
        str(delete_vm_post_restore).lower(),
        name="delete_vm_post_restore",
        runtime=True,
        is_mandatory=True,
    )
    kwargs = {
        "name": name,
        "description": description,
        "attrs_list": [attrs],
        "type": "",  # Set at profile level based on target
        "variables": [snapshot_uuids, delete_vm_post_restore],
    }
    return _config_create(config_type="restore", **kwargs)
