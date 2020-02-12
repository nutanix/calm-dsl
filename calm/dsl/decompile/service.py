from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ServiceType
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.decompile.action import render_action_template


def render_service_template(cls):

    if not isinstance(cls, ServiceType):
        raise TypeError("{} is not of type {}".format(cls, ServiceType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    depends_on_list = []
    for entity in user_attrs.get("dependencies", []):
        depends_on_list.append(render_ref_template(entity))

    variable_list = []
    for entity in user_attrs.get("variables", []):
        variable_list.append(render_variable_template(entity))

    action_list = []
    system_actions = {v: k for k, v in ServiceType.ALLOWED_SYSTEM_ACTIONS.items()}
    for entity in user_attrs.get("actions", []):
        name = entity.__name__
        if entity.__name__ in list(system_actions.keys()):
            entity.__name__ = system_actions[entity.__name__]
        action_list.append(render_action_template(entity))

    user_attrs["dependencies"] = ",".join(depends_on_list)
    user_attrs["variables"] = variable_list
    user_attrs["actions"] = action_list

    # TODO add ports, ..etc.

    text = render_template("service.py.jinja2", obj=user_attrs)
    return text.strip()
