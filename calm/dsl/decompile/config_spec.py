from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ConfigSpecType, get_valid_identifier
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_restore_config_template(cls, entity_context):
    LOG.debug("Rendering {} restore config template".format(cls.__name__))
    if not isinstance(cls, ConfigSpecType):
        raise TypeError("{} is not of type {}".format(cls, ConfigSpecType))

    _user_attrs = cls.get_user_attrs()
    user_attrs = dict()
    user_attrs["name"] = _user_attrs["name"] or cls.__name__
    attrs = _user_attrs["attrs_list"][0]
    user_attrs["target"] = get_valid_identifier(
        attrs["target_any_local_reference"]["name"]
    )
    user_attrs["delete_vm_post_restore"] = attrs["delete_vm_post_restore"]
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
    user_attrs["target"] = get_valid_identifier(
        attrs["target_any_local_reference"]["name"]
    )
    user_attrs["num_of_replicas"] = attrs["num_of_replicas"]
    if attrs.get("app_protection_policy_reference", None):
        user_attrs["policy"] = attrs["app_protection_policy_reference"]["name"]
    if attrs.get("app_protection_rule_reference", None):
        user_attrs["rule"] = attrs["app_protection_rule_reference"]["name"]
    text = render_template(schema_file="snapshot_config.py.jinja2", obj=user_attrs)
    return text.strip()
