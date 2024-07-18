from calm.dsl.builtins.models.resource_type import ResourceTypeEntity
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.decompile_helpers import modify_var_format
from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ref_dependency import update_resource_type_name
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_resource_type_template(
    cls, secrets_dict, credential_list=[], rendered_credential_list=[]
):

    LOG.debug("Rendering {} resource_type template".format(cls.__name__))
    if not isinstance(cls, ResourceTypeEntity):
        raise TypeError("{} is not of type {}".format(cls, ResourceTypeEntity))

    # Entity context
    entity_context = "ResourceType_" + cls.__name__
    context = "resource_type_list." + (getattr(cls, "name", "") or cls.__name__) + "."

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or ""

    gui_display_name = getattr(cls, "name", "") or cls.__name__
    if gui_display_name != cls.__name__:
        user_attrs[
            "gui_display_name"
        ] = gui_display_name  # Update RT name map and gui name

    update_resource_type_name(
        gui_display_name, cls.__name__
    )  # updating ui and dsl name mapping

    action_list = []
    for action in user_attrs.get("actions", []):
        action_list.append(
            render_action_template(
                action,
                entity_context,
                secrets_dict=secrets_dict,
                context=context,
                credential_list=credential_list,
                rendered_credential_list=rendered_credential_list,
            )
        )

    variable_list = []
    for entity in user_attrs.get("variables", []):
        var_template = render_variable_template(
            entity,
            entity_context,
            secrets_dict=secrets_dict,
            context=context,
            credentials_list=credential_list,
            rendered_credential_list=rendered_credential_list,
        )
        variable_list.append(modify_var_format(var_template))

    schema_list = []
    for entity in user_attrs.get("schemas", []):
        var_template = render_variable_template(
            entity,
            entity_context,
            secrets_dict=secrets_dict,
            context=context,
            variable_context="schema",
            credentials_list=credential_list,
            rendered_credential_list=rendered_credential_list,
        )
        schema_list.append(modify_var_format(var_template))

    user_attrs["variables"] = variable_list
    user_attrs["schemas"] = schema_list
    user_attrs["actions"] = action_list

    text = render_template("resource_type.py.jinja2", obj=user_attrs)
    return text.strip()
