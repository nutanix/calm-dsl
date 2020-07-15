from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import PackageType
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.decompile.action import render_action_template
from calm.dsl.decompile.ref_dependency import update_package_name
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_package_template(cls):

    LOG.debug("Rendering {} package template".format(cls.__name__))
    if not isinstance(cls, PackageType):
        raise TypeError("{} is not of type {}".format(cls, PackageType))

    # Entity context
    entity_context = "Package_" + cls.__name__

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or ""

    # Update package name map
    gui_display_name = getattr(cls, "name", "") or cls.__name__
    if gui_display_name != cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    # updating ui and dsl name mapping
    update_package_name(gui_display_name, cls.__name__)

    service_list = []
    for entity in user_attrs.get("services", []):
        service_list.append(render_ref_template(entity))

    variable_list = []
    for entity in user_attrs.get("variables", []):
        variable_list.append(render_variable_template(entity, entity_context))

    action_list = []
    if hasattr(cls, "__install__"):
        cls.__install__.__name__ = "__install__"
        cls.__install__.name = "__install__"
        action_list.append(render_action_template(cls.__install__, entity_context))

    if hasattr(cls, "__uninstall__"):
        cls.__uninstall__.__name__ = "__uninstall__"
        cls.__uninstall__.name = "__uninstall__"
        action_list.append(render_action_template(cls.__uninstall__, entity_context))

    user_attrs["services"] = ",".join(service_list)
    user_attrs["variables"] = variable_list
    user_attrs["actions"] = action_list

    text = render_template("package.py.jinja2", obj=user_attrs)
    return text.strip()
