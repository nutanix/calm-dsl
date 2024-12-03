from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ProfileType, get_valid_identifier
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.decompile.ref_dependency import update_profile_name
from calm.dsl.decompile.config_spec import (
    render_snapshot_config_template,
    render_restore_config_template,
    render_update_config_template,
)
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

CONFIG_SPEC_MAP = {}


def render_profile_template(
    cls, update_config_patch_attr_map, secrets_dict=[], endpoints=[], ep_list=[]
):

    LOG.debug("Rendering {} profile template".format(cls.__name__))
    if not isinstance(cls, ProfileType):
        raise TypeError("{} is not of type {}".format(cls, ProfileType))

    # Entity context
    entity_context = "Profile_" + cls.__name__
    context = "app_profile_list." + (getattr(cls, "name", "") or cls.__name__) + "."

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or ""

    # Update profile name map and gui name
    gui_display_name = getattr(cls, "name", "") or cls.__name__
    if gui_display_name != cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    # updating ui and dsl name mapping
    update_profile_name(gui_display_name, cls.__name__)

    restore_config_list = []
    for idx, entity in enumerate(user_attrs.get("restore_configs", [])):
        CONFIG_SPEC_MAP[entity.name] = {
            "global_name": "{}.restore_configs[{}]".format(cls.__name__, idx),
            "local_name": "restore_configs[{}]".format(idx),
        }
        restore_config_list.append(
            render_restore_config_template(entity, entity_context)
        )

    snapshot_config_list = []
    for idx, entity in enumerate(user_attrs.get("snapshot_configs", [])):
        CONFIG_SPEC_MAP[entity.name] = {
            "global_name": "{}.snapshot_configs[{}]".format(cls.__name__, idx),
            "local_name": "snapshot_configs[{}]".format(idx),
        }
        snapshot_config_list.append(
            render_snapshot_config_template(entity, entity_context, CONFIG_SPEC_MAP)
        )
    update_config_list = []
    for idx, entity in enumerate(user_attrs.get("patch_list", [])):
        CONFIG_SPEC_MAP[entity.name] = {
            "global_name": "{}.update_configs[{}]".format(cls.__name__, idx),
            "local_name": "update_configs[{}]".format(idx),
        }

        entity_name = get_valid_identifier(entity.name)
        patch_attr_name = update_config_patch_attr_map[entity_name]
        patch_attr_name = get_valid_identifier(
            entity_name + "_Update" + patch_attr_name
        )
        update_config_list.append(
            render_update_config_template(entity, patch_attr_name)
        )

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

    deployment_list = []
    for deployment in user_attrs.get("deployments", []):
        deployment_list.append(deployment.__name__)

    variable_list = []
    for entity in user_attrs.get("variables", []):
        variable_list.append(
            render_variable_template(
                entity,
                entity_context,
                secrets_dict=secrets_dict,
                context=context,
                endpoints=endpoints,
                ep_list=ep_list,
            )
        )

    user_attrs["variables"] = variable_list
    user_attrs["deployments"] = ", ".join(deployment_list)
    user_attrs["actions"] = action_list
    user_attrs["patch_list"] = ", ".join(update_config_list)
    user_attrs["restore_configs"] = ", ".join(restore_config_list)
    user_attrs["snapshot_configs"] = ", ".join(snapshot_config_list)

    text = render_template("profile.py.jinja2", obj=user_attrs)
    return text.strip()
