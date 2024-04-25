import re
import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .task import CalmTask, create_call_config, dag
from .ref import ref
from .action import action, _action_create
from .runbook import runbook_create
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins.models.ahv_vm_disk import AhvDiskType
from calm.dsl.builtins.models.ahv_vm_nic import AhvNicType


LOG = get_logging_handle(__name__)


class AhvDiskRuleset(EntityType):
    __schema_name__ = "AhvDiskRuleset"
    __openapi_type__ = "ahv_disk_rule"

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):
        disk_operation = cdict.pop("operation", "")
        index = cdict.pop("index", "")
        disk_details = cdict.get("disk_size_mib", {})
        operation = ""
        editable = False
        disk_size = ""
        max_value = ""
        min_value = ""
        value = ""

        if disk_details:
            editable = disk_details.pop("editable", False)
            operation = disk_details.pop("operation", "")
            max_value = disk_details.pop("max_value", "")
            min_value = disk_details.pop("min_value", "")
            # creating valid disk size dictionary
            disk_size = disk_details.get("value", "")

        if disk_size:
            cdict["disk_size_mib"] = int(disk_size)
            value = str(disk_size) if disk_size else ""

        disk_value = AhvDiskType.decompile(cdict, context=context, prefix=prefix)

        kwargs = {
            "disk_operation": disk_operation,
            "operation": operation,
            "editable": editable,
            "disk_value": disk_value,
        }
        if max_value:
            kwargs["max_value"] = max_value
        if min_value:
            kwargs["min_value"] = min_value
        if value:
            kwargs["value"] = value
        if index:
            kwargs["index"] = index

        return mcls(None, (Entity,), kwargs)


class AhvDiskRulesetValidator(PropertyValidator, openapi_type="ahv_disk_rule"):
    __default__ = None
    __kind__ = AhvDiskRuleset


def ahv_disk_ruleset(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvDiskRuleset(name, bases, kwargs)


AhvDiskRulesetField = ahv_disk_ruleset()


class AhvNicRuleset(EntityType):
    __schema_name__ = "AhvNicRuleset"
    __openapi_type__ = "ahv_nic_rule"

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):

        operation = cdict.pop("operation", "")
        editable = cdict.pop("editable", False)
        value = cdict.pop("value", "")
        index = cdict.pop("identifier", "")

        nic_value = AhvNicType.decompile(cdict, context=context, prefix=prefix)

        kwargs = {"operation": operation, "editable": editable, "nic_value": nic_value}
        if value:
            kwargs["value"] = value
        if index:
            kwargs["index"] = index

        return mcls(None, (Entity,), kwargs)


class AhvNicRulesetValidator(PropertyValidator, openapi_type="ahv_nic_rule"):
    __default__ = None
    __kind__ = AhvNicRuleset


def ahv_nic_ruleset(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvNicRuleset(name, bases, kwargs)


AhvNicRulesetField = ahv_nic_ruleset()


class PatchDataField(EntityType):
    __schema_name__ = "PatchDataField"
    __openapi_type__ = "patch_data_field"


class PatchDataFieldValidator(PropertyValidator, openapi_type="patch_data_field"):
    __default__ = None
    __kind__ = PatchDataField


def patch_data_field(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return PatchDataField(name, bases, kwargs)


AhvPatchDataField = patch_data_field()


class ConfigAttrs(EntityType):
    __schema_name__ = "ConfigAttrs"
    __openapi_type__ = "config_attrs"

    def get_config_actions(cls):
        cdict = super().compile()
        return cdict["action_list"]


class ConfigAttrsValidator(PropertyValidator, openapi_type="config_attrs"):
    __default__ = None
    __kind__ = ConfigAttrs


def config_attrs(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ConfigAttrs(name, bases, kwargs)


AhvUpdateConfigAttrs = config_attrs()
