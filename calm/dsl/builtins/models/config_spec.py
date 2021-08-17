import inspect
import json
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


class ConfigSpecType(EntityType):
    __schema_name__ = "ConfigSpec"
    __openapi_type__ = "app_config_spec"

    def get_ref(cls, kind=None):
        """Note: app_blueprint_deployment kind to be used for pod deployment"""
        return super().get_ref(kind=ConfigSpecType.__openapi_type__)


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
