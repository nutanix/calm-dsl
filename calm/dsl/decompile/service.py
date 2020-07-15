from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ServiceType
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.ref_dependency import update_service_name
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_service_template(cls):

    LOG.debug("Rendering {} service template".format(cls.__name__))
    if not isinstance(cls, ServiceType):
        raise TypeError("{} is not of type {}".format(cls, ServiceType))

    # Entity context
    entity_context = "Service_" + cls.__name__

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or ""

    # Update service name map and gui name
    gui_display_name = getattr(cls, "name", "") or cls.__name__
    if gui_display_name != cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    # updating ui and dsl name mapping
    update_service_name(gui_display_name, cls.__name__)

    depends_on_list = []
    for entity in user_attrs.get("dependencies", []):
        depends_on_list.append(render_ref_template(entity))

    variable_list = []
    for entity in user_attrs.get("variables", []):
        variable_list.append(render_variable_template(entity, entity_context))

    action_list = []
    system_actions = {v: k for k, v in ServiceType.ALLOWED_SYSTEM_ACTIONS.items()}
    for entity in user_attrs.get("actions", []):
        if entity.__name__ in list(system_actions.keys()):
            entity.name = system_actions[entity.__name__]
            entity.__name__ = system_actions[entity.__name__]
        rendered_txt = render_action_template(entity, entity_context)
        if rendered_txt:
            action_list.append(rendered_txt)

    user_attrs["dependencies"] = ",".join(depends_on_list)
    user_attrs["variables"] = variable_list
    user_attrs["actions"] = action_list

    # TODO add ports, ..etc.

    text = render_template("service.py.jinja2", obj=user_attrs)
    return text.strip()
