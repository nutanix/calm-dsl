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
from .runbook import runbook_create
from .action import _action_create
from calm.dsl.builtins import get_valid_identifier, PatchDataField
from calm.dsl.constants import PROVIDER
from calm.dsl.store import Cache
from calm.dsl.builtins.models.config_attrs import ahv_disk_ruleset, ahv_nic_ruleset

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

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        # Calling pre_decompile of PatchConfigSpecType for patch configs
        if cdict.get("type", "") == "PATCH":
            cdict = PatchConfigSpecType.pre_decompile(cdict, context, prefix=prefix)

        return cdict

    def get_ref(cls, kind=None):
        """Note: app_blueprint_deployment kind to be used for pod deployment"""
        return super().get_ref(kind=ConfigSpecType.__openapi_type__)

    def compile(cls):
        cdict = super().compile()
        if "patch_attrs" not in cdict or len(cdict["patch_attrs"]) == 0:
            cdict.pop("patch_attrs", None)
            return cdict
        attrs = cdict.pop("patch_attrs")[0]
        target = cdict["attrs_list"][0]["target_any_local_reference"]

        resource_categories = (
            target.__self__.substrate.__self__.provider_spec.categories
        )
        categories_data = []
        categories = attrs.categories

        # attaching pre defined categories if no categories are supplied.
        if not categories:
            for key, value in resource_categories.items():
                val = {}
                val["operation"] = "modify"
                val["value"] = "{}:{}".format(key, value)
                categories_data.append(val)

        for op_category in categories:
            for op in op_category["val"]:
                val = {}
                val["operation"] = op_category["operation"]
                val["value"] = op
                categories_data.append(val)

        memory = attrs.memory

        # set memory values only if it is present as attribute in AhvUpdateConfigAttrs class
        if memory:
            if memory.min_value:
                memory.min_value = memory.min_value * 1024
            if memory.max_value:
                memory.max_value = memory.max_value * 1024
            if memory.value:
                memory.value = str(int(float(memory.value) * 1024))

        resource_disks = (
            target.__self__.substrate.__self__.provider_spec.resources.disks
        )
        disk_data = []
        disks = attrs.disks

        # attaching pre defined resource disks if no disks are supplied.
        if not disks:
            for idx, _disk in enumerate(resource_disks):
                _disk = _disk.compile()
                kwargs = {
                    "disk_operation": "modify",
                    "operation": "",
                    "index": idx,
                    "editable": False,
                }
                _value = _disk.get("disk_size_mib", 0)
                kwargs["value"] = str(_value // 1024)
                disks.append(ahv_disk_ruleset(**kwargs))

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

        resource_nics = target.__self__.substrate.__self__.provider_spec.resources.nics
        nic_data = []
        nics = attrs.nics

        # attaching pre defined nics if no nics are supplied.
        if not nics:
            for idx, _ in enumerate(resource_nics):
                kwargs = {"operation": "modify", "index": str(idx), "editable": False}
                nics.append(ahv_nic_ruleset(**kwargs))

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
            "pre_defined_disk_list": disk_data,
            "pre_defined_nic_list": nic_data,
            "pre_defined_categories": categories_data,
        }

        # setting num_sockets_ruleset, memory_size_mib_ruleset, vcpus to default blank dict if not present
        if isinstance(attrs.numsocket, PatchDataField):
            data["num_sockets_ruleset"] = attrs.numsocket.get_all_attrs()
        else:
            data["num_sockets_ruleset"] = {}

        if isinstance(memory, PatchDataField):
            data["memory_size_mib_ruleset"] = memory.get_all_attrs()
        else:
            data["memory_size_mib_ruleset"] = {}

        if isinstance(attrs.vcpu, PatchDataField):
            data["num_vcpus_per_socket_ruleset"] = attrs.vcpu.get_all_attrs()
        else:
            data["num_vcpus_per_socket_ruleset"] = {}

        # Setting actions attribute to PatchConfigSpecType to compile actions
        if isinstance(cls, PatchConfigSpecType):
            actions = attrs.get_config_actions()
            cls.set_actions(actions)

        cdict["attrs_list"][0]["data"] = data
        return cdict

    def post_compile(cls, cdict):
        cdict = super().post_compile(cdict)

        # Remove policy_reference after compiling as it is invalid in blueprint payload
        cdict.pop("policy_reference", "")
        return cdict


class PatchConfigSpecType(ConfigSpecType):
    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        patch_attr_data = cdict["attrs_list"][0]["data"]
        actions = []
        patch_action_data = cdict.get("runbook", {})
        if patch_action_data:
            patch_action_data.pop("uuid", "")
            patch_action_data.get("main_task_local_reference", {}).pop("uuid", "")
            task_definition_list = patch_action_data.get("task_definition_list", [])
            for tdl in task_definition_list:
                # Removing additional attributes
                tdl.pop("uuid", "")
                tdl.get("target_any_local_reference", {}).pop("uuid", "")
                for child in tdl.get("child_tasks_local_reference_list", []):
                    child.pop("uuid", "")
                for edge in tdl.get("attrs", {}).get("edges", []):
                    edge.get("from_task_reference", {}).pop("uuid", "")
                    edge.get("to_task_reference", {}).pop("uuid", "")

            action_name = "custom_app_edit_action"
            if len(task_definition_list) > 1:
                action_name = task_definition_list[1].get("name", action_name)

            actions = [
                _action_create(
                    **{
                        "name": get_valid_identifier(action_name),
                        "description": "",
                        "critical": True,
                        "type": "user",
                        "runbook": patch_action_data,
                    }
                ).get_dict()
            ]

        for idx, _disk in enumerate(patch_attr_data.get("pre_defined_disk_list", [])):
            _disk["index"] = idx

        kwargs = {
            "nic_delete": patch_attr_data.get("nic_delete_allowed", False),
            "categories_delete": patch_attr_data.get(
                "categories_delete_allowed", False
            ),
            "categories_add": patch_attr_data.get("categories_add_allowed", False),
            "disk_delete": patch_attr_data.get("disk_delete_allowed", False),
            "disks": patch_attr_data.get("pre_defined_disk_list", []),
            "nics": patch_attr_data.get("pre_defined_nic_list", []),
            "categories": patch_attr_data.get("pre_defined_categories", []),
            "numsocket": patch_attr_data.get("num_sockets_ruleset", {}),
            "memory": patch_attr_data.get("memory_size_mib_ruleset", {}),
            "vcpu": patch_attr_data.get("num_vcpus_per_socket_ruleset", {}),
            "action_list": actions,
        }

        cdict["patch_attrs"] = [kwargs]
        cdict.pop("runbook", "")
        return cdict

    def compile(cls):
        cdict = super().compile()

        attrs = getattr(cls, "attrs_list")[0] if getattr(cls, "attrs_list") else None
        try:
            target_deployment = attrs["target_any_local_reference"]
            services_ref = target_deployment.__self__.get_service_ref()
        except:
            LOG.error("No deployment target set for patch config")
            sys.exit(-1)

        if not services_ref:
            LOG.error("No service to target patch config actions.")
            sys.exit(-1)

        # there will be a single action in the patch_config
        actions = getattr(cls, "action_list", [])
        if len(actions) > 1:
            LOG.error("Single action is allowed at patch_config")
            sys.exit(-1)

        if actions:
            actions = actions[0].get_dict()
            config_runbook = actions["runbook"]
            for tdl in config_runbook["task_definition_list"]:
                tdl["uuid"] = str(uuid.uuid4())
                tdl["target_any_local_reference"] = services_ref.get_dict()

            cdict["runbook"] = config_runbook

        return cdict

    @classmethod
    def set_actions(cls, actions):
        setattr(cls, "action_list", actions)


class SnapshotConfigSpecType(ConfigSpecType):
    def compile(cls):
        cdict = super().compile()
        rule_ref = {}
        snapshot_location_type = None
        policy = None
        policy_ref = getattr(cls, "policy")
        if policy_ref:
            policy = policy_ref.compile()
        if policy:
            rule = policy.pop("rule_uuid", None)

            # Reading protection policy data from cache, required if no rule is present in above policy reference
            protection_policy_cache_data = Cache.get_entity_data_using_uuid(
                entity_type="app_protection_policy",
                uuid=policy.get("uuid"),
            )

            if not protection_policy_cache_data:
                LOG.error(
                    "Protection Policy {} not found. Please run: calm update cache".format(
                        policy.get("name")
                    )
                )
                sys.exit(
                    "Protection policy {} does not exist".format(policy.get("name"))
                )

            protection_rule_list = []

            for _policy in protection_policy_cache_data:
                protection_rule_list.append(
                    {
                        "uuid": _policy["rule_uuid"],
                        "name": _policy["rule_name"],
                        "rule_type": _policy.get("rule_type", ""),
                    }
                )

            rule_ref["kind"] = "app_protection_rule"

            # if no rule is given, pick first rule specified in policy
            if not rule:
                if protection_rule_list and isinstance(protection_rule_list, list):
                    rule_ref["uuid"] = protection_rule_list[0]["uuid"]
                    rule_ref["name"] = protection_rule_list[0]["name"]
                    if protection_rule_list["rule_type"] == "Remote":
                        snapshot_location_type = "REMOTE"
            else:
                for pr in protection_rule_list:
                    if pr.get("uuid") == rule:
                        rule_ref["uuid"] = rule
                        rule_ref["name"] = pr.get("name")
                        if pr.get("rule_type", "") == "Remote":
                            snapshot_location_type = "REMOTE"

            if "uuid" not in rule_ref:
                LOG.error(
                    "No Protection Rule {} found under Protection Policy {}".format(
                        rule, policy["name"]
                    )
                )
                sys.exit("Invalid protection rule")

        if (
            cdict["attrs_list"][0].get("snapshot_location_type")
            and snapshot_location_type
        ):
            cdict["attrs_list"][0]["snapshot_location_type"] = snapshot_location_type
        if policy:
            cdict["attrs_list"][0]["app_protection_policy_reference"] = policy
            cdict["attrs_list"][0]["app_protection_rule_reference"] = rule_ref

        return cdict


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


def _update_ahv_snapshot_config(attrs, snapshot_location_type, **kwargs):
    attrs["snapshot_location_type"] = snapshot_location_type


def _update_vmw_snapshot_config(attrs, **kwargs):
    attrs["snapshot_name"] = ""
    attrs["vm_memory_snapshot_enabled"] = ""
    attrs["snapshot_description"] = ""
    attrs["snapshot_quiesce_enabled"] = ""

    snapshot_description = CalmVariable.Simple(
        "", name="snapshot_description", runtime=True, is_mandatory=True
    )
    vm_memory_snapshot_enabled = CalmVariable.Simple(
        "false", name="vm_memory_snapshot_enabled", runtime=True, is_mandatory=True
    )
    snapshot_quiesce_enabled = CalmVariable.Simple(
        "false", name="snapshot_quiesce_enabled", runtime=True, is_mandatory=True
    )
    updated_variables = [
        snapshot_description,
        vm_memory_snapshot_enabled,
        snapshot_quiesce_enabled,
    ]
    kwargs["variables"].extend(updated_variables)


def _update_ahv_restore_config(
    attrs, snapshot_location_type, delete_vm_post_restore, **kwargs
):
    attrs["delete_vm_post_restore"] = delete_vm_post_restore
    attrs["snapshot_location_type"] = snapshot_location_type
    delete_vm_post_restore = CalmVariable.Simple(
        str(delete_vm_post_restore).lower(),
        name="delete_vm_post_restore",
        runtime=True,
        is_mandatory=True,
    )
    kwargs["variables"].append(delete_vm_post_restore)


def _update_vmw_restore_config(attrs, **kwargs):
    attrs["suppress_power_on"] = "true"


def snapshot_config_create(
    name,
    provider,
    target=None,
    snapshot_type="CRASH_CONSISTENT",
    num_of_replicas="ONE",
    config_references=[],
    snapshot_location_type="LOCAL",
    policy=None,
    description="",
):
    # Only AHV support snapshot location. VMWARE doesn't support snapshot location
    # therefore not setting snapshot location in config reference for VMWARE
    if config_references:
        if provider == PROVIDER.TYPE.AHV:
            for config_ref in config_references:
                config_ref.__self__.attrs_list[0][
                    "snapshot_location_type"
                ] = snapshot_location_type

    attrs = {
        "target_any_local_reference": target,
        "num_of_replicas": num_of_replicas,
    }
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
        "policy": policy,
    }

    if provider == PROVIDER.TYPE.AHV:
        _update_ahv_snapshot_config(attrs, snapshot_location_type)
    elif provider == PROVIDER.TYPE.VMWARE:
        _update_vmw_snapshot_config(attrs, **kwargs)

    return _config_create(config_type="snapshot", **kwargs)


def restore_config_create(
    name,
    provider,
    target,
    snapshot_location_type="LOCAL",
    delete_vm_post_restore=False,
    description="",
):
    attrs = {
        "target_any_local_reference": target,
    }

    snapshot_uuids = CalmVariable.Simple(
        "", name="snapshot_uuids", runtime=True, is_mandatory=True
    )

    kwargs = {
        "name": name,
        "description": description,
        "attrs_list": [attrs],
        "type": "",  # Set at profile level based on target
        "variables": [snapshot_uuids],
    }

    if provider == PROVIDER.TYPE.AHV:
        _update_ahv_restore_config(
            attrs, snapshot_location_type, delete_vm_post_restore, **kwargs
        )
    elif provider == PROVIDER.TYPE.VMWARE:
        _update_vmw_restore_config(attrs, **kwargs)

    return _config_create(config_type="restore", **kwargs)
