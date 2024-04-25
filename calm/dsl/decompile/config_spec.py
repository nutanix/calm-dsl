import re
import json

from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ConfigSpecType, get_valid_identifier
from calm.dsl.constants import PROVIDER
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins import ConfigAttrs
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.ahv_vm_disk import render_ahv_vm_disk
from calm.dsl.decompile.ahv_vm_nic import render_ahv_vm_nic
from calm.dsl.decompile.ref_dependency import get_entity_gui_dsl_name

LOG = get_logging_handle(__name__)

CONFIG_SPEC_MAP = {}


def render_restore_config_template(cls, entity_context):
    LOG.debug("Rendering {} restore config template".format(cls.__name__))
    if not isinstance(cls, ConfigSpecType):
        raise TypeError("{} is not of type {}".format(cls, ConfigSpecType))

    _user_attrs = cls.get_user_attrs()
    user_attrs = dict()
    user_attrs["name"] = _user_attrs["name"] or cls.__name__
    attrs = _user_attrs["attrs_list"][0]
    user_attrs["target"] = attrs["target_any_local_reference"]["name"]

    # Mapping target to it's corresponding dsl class
    user_attrs["target"] = get_entity_gui_dsl_name(user_attrs["target"])

    user_attrs["description"] = attrs.get("snapshot_description", "")
    user_attrs["delete_vm_post_restore"] = attrs.get("delete_vm_post_restore", None)

    if _user_attrs["type"] == "AHV_RESTORE":
        user_attrs["provider"] = "Ahv"
        user_attrs["delete_vm_post_restore"] = attrs["delete_vm_post_restore"]
    elif _user_attrs["type"] == "VMWARE_RESTORE":
        user_attrs["provider"] = "Vmware"
    else:
        LOG.warning("Given snapshot type not supported for decompilation")

    text = render_template(schema_file="restore_config.py.jinja2", obj=user_attrs)
    return text.strip()


def render_snapshot_config_template(cls, entity_context, CONFIG_SPEC_MAP):
    LOG.debug("Rendering {} snapshot config template".format(cls.__name__))
    if not isinstance(cls, ConfigSpecType):
        raise TypeError("{} is not of type {}".format(cls, ConfigSpecType))

    _user_attrs = cls.get_user_attrs()
    user_attrs = dict()
    user_attrs["name"] = _user_attrs["name"] or cls.__name__
    user_attrs["restore_config"] = CONFIG_SPEC_MAP[
        _user_attrs["config_references"][0].name
    ]["local_name"]
    attrs = _user_attrs["attrs_list"][0]
    user_attrs["target"] = attrs["target_any_local_reference"]["name"]

    # Mapping target to it's corresponding dsl class
    user_attrs["target"] = get_entity_gui_dsl_name(user_attrs["target"])

    user_attrs["num_of_replicas"] = attrs["num_of_replicas"]
    user_attrs["description"] = attrs.get("snapshot_description", "")
    user_attrs["snapshot_location_type"] = attrs.get("snapshot_location_type", None)

    if _user_attrs["type"] == "AHV_SNAPSHOT":
        user_attrs["provider"] = "Ahv"
    elif _user_attrs["type"] == "VMWARE_SNAPSHOT":
        user_attrs["provider"] = "Vmware"
    else:
        LOG.warning("Given snapshot type not supported for decompilation")

    if attrs.get("app_protection_policy_reference", {}).get("name", {}):
        user_attrs["policy"] = attrs["app_protection_policy_reference"]["name"]
    if attrs.get("app_protection_rule_reference", {}).get("name", {}):
        user_attrs["rule"] = attrs["app_protection_rule_reference"]["name"]
    text = render_template(schema_file="snapshot_config.py.jinja2", obj=user_attrs)
    return text.strip()


def render_patch_field_ahv_nic(cls):
    LOG.debug("Rendering patch field ahv nic template")

    _user_attrs = cls.get_user_attrs()
    nic_value = cls.nic_value

    if cls.operation == "add":
        _user_attrs["nic_data"] = render_ahv_vm_nic(nic_value)

    text = render_template(schema_file="patch_field_ahv_nic.py.jinja2", obj=_user_attrs)
    return text.strip()


def render_patch_field_ahv_disk(cls):
    LOG.debug("Rendering patch field ahv disk template")

    _user_attrs = cls.get_user_attrs()
    disk_value = cls.disk_value

    if cls.disk_operation == "add":
        _user_attrs["disk_data"] = render_ahv_vm_disk(disk_value, {})

    # converting values from miB to giB
    _user_attrs["value"] = (
        str(int(_user_attrs["value"]) // 1024) if _user_attrs["value"] else ""
    )
    _user_attrs["max_val"] = (
        str(int(_user_attrs["max_value"]) // 1024) if _user_attrs["max_value"] else ""
    )
    _user_attrs["min_val"] = (
        str(int(_user_attrs["min_value"]) // 1024) if _user_attrs["min_value"] else ""
    )

    text = render_template(
        schema_file="patch_field_ahv_disk.py.jinja2", obj=_user_attrs
    )
    return text.strip()


def render_patch_field_category_template(cls):
    LOG.debug("Rendering patch field category template")
    category_value = cls["value"]

    # convert category_value string ('TemplateType:Vm') to dictionary {'TemplateType': 'Vm'} using regex
    pattern = r"(\w+):(\w+)"
    category_value = re.sub(pattern, r'{"\1": "\2"}', category_value)
    cls["value"] = json.loads(category_value)

    text = render_template(schema_file="patch_field_category.py.jinja2", obj=cls)
    return text.strip()


def render_update_config_template(cls, patch_attr_name):
    LOG.debug("Rendering {} patch config template".format(cls.__name__))
    if not isinstance(cls, ConfigSpecType):
        raise TypeError("{} is not of type {}".format(cls, ConfigSpecType))

    _user_attrs = cls.get_user_attrs()
    user_attrs = dict()
    user_attrs["name"] = _user_attrs["name"] or cls.__name__
    attrs = _user_attrs["attrs_list"][0]
    user_attrs["target"] = attrs["target_any_local_reference"]["name"]

    # Mapping target to it's corresponding dsl class
    user_attrs["target"] = get_entity_gui_dsl_name(user_attrs["target"])
    user_attrs["patch_attr"] = patch_attr_name

    text = render_template(schema_file="update_config.py.jinja2", obj=user_attrs)
    return text.strip()


def render_config_attr_template(
    cls, patch_attr_update_config_map, secrets_dict=[], endpoints=[], ep_list=[]
):

    LOG.debug("Rendering {} Update Config Attr template".format(cls.__name__))
    if not isinstance(cls, ConfigAttrs):
        raise TypeError("{} is not of type {}".format(cls, ConfigAttrs))

    # Entity context
    entity_context = "UpdateConfigAttr_" + cls.__name__
    context = "update_config_attr." + (getattr(cls, "name", "") or cls.__name__) + "."

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = get_valid_identifier(
        patch_attr_update_config_map[cls.__name__] + "_Update" + cls.__name__
    )
    user_attrs["description"] = cls.__doc__ or ""
    user_attrs["disk_delete"] = cls.disk_delete
    user_attrs["categories_delete"] = cls.categories_delete
    user_attrs["nic_delete"] = cls.nic_delete
    user_attrs["categories_add"] = cls.categories_add
    memory_obj = user_attrs.get("memory", None)

    if memory_obj:
        # max_value, min_value are strictly of type int
        memory_obj.max_value = int(memory_obj.max_value / 1024)
        memory_obj.min_value = int(memory_obj.min_value / 1024)
        user_attrs["memory"] = memory_obj.get_dict()

        # Converting memory values from mib to GiB
        value = user_attrs["memory"]["value"]

        if value:
            value = int(value) / 1024.0
            # Handling case with trailing zero decimal. Converts 2.0 to "2", 2.5 to "2.5"
            user_attrs["memory"]["value"] = (
                str(int(value)) if value.is_integer() else str(value)
            )

    vcpu_obj = user_attrs.get("vcpu", None)
    if vcpu_obj:
        user_attrs["vcpu"] = vcpu_obj.get_dict()

    numsocket_obj = user_attrs.get("numsocket", None)
    if numsocket_obj:
        user_attrs["numsocket"] = numsocket_obj.get_dict()

    category_list = []
    for _, entity in enumerate(user_attrs.get("categories", [])):
        if entity:
            category_list.append(render_patch_field_category_template(entity))

    disk_list = []
    for _, entity in enumerate(user_attrs.get("disks", [])):
        if entity:
            disk_list.append(render_patch_field_ahv_disk(entity))

    nic_list = []
    for _, entity in enumerate(user_attrs.get("nics", [])):
        if entity:
            nic_list.append(render_patch_field_ahv_nic(entity))

    action_list = []
    for action in user_attrs.get("actions", []):
        action_list.append(
            render_action_template(
                action,
                entity_context,
                CONFIG_SPEC_MAP,
                secrets_dict=secrets_dict,
                context=context,
                endpoints=endpoints,
                ep_list=ep_list,
            )
        )

    user_attrs["actions"] = action_list
    user_attrs["category_list"] = ", ".join(
        category for category in category_list if category
    )
    user_attrs["disk_list"] = ", ".join(disk_list)
    user_attrs["nic_list"] = ", ".join(nic for nic in nic_list if nic)

    text = render_template("update_config_attr.py.jinja2", obj=user_attrs)

    return text.strip()
