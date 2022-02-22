import re
import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .task import CalmTask, create_call_config, dag
from .ref import ref
from .action import action, _action_create
from .runbook import runbook_create
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class AhvDiskRuleset(EntityType):
    __schema_name__ = "AhvDiskRuleset"
    __openapi_type__ = "ahv_disk_rule"


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


class ConfigAttrsValidator(PropertyValidator, openapi_type="config_attrs"):
    __default__ = None
    __kind__ = ConfigAttrs


def config_attrs(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ConfigAttrs(name, bases, kwargs)


AhvUpdateConfigAttrs = config_attrs()
