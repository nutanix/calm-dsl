from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import RefType
from calm.dsl.tools import get_logging_handle
from calm.dsl.decompile.ref_dependency import (
    get_service_name,
    get_profile_name,
    get_substrate_name,
)
from calm.dsl.decompile.ref_dependency import get_package_name, get_deployment_name


LOG = get_logging_handle(__name__)


def render_ref_template(cls):

    LOG.debug("Rendering {} ref template".format(cls.__name__))
    if not isinstance(cls, RefType):
        raise TypeError("{} is not of type {}".format(cls, RefType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = getattr(cls, "name")
    if not user_attrs["name"]:
        user_attrs["name"] = cls.__name__
    schema_file = "ref.py.jinja2"

    kind = cls.kind
    if kind == "app_service":
        cls_name = get_service_name(user_attrs["name"])
        if cls_name:
            user_attrs["name"] = cls_name
    elif kind == "app_package":
        cls_name = get_package_name(user_attrs["name"])
        if cls_name:
            user_attrs["name"] = cls_name
    elif kind == "app_substrate":
        cls_name = get_substrate_name(user_attrs["name"])
        if cls_name:
            user_attrs["name"] = cls_name
    elif kind == "app_blueprint_deployment":
        cls_name = get_deployment_name(user_attrs["name"])
        if cls_name:
            user_attrs["name"] = cls_name
    elif kind == "app_profile":
        cls_name = get_profile_name(user_attrs["name"])
        if cls_name:
            user_attrs["name"] = cls_name

    # Updating name attribute of class
    cls.name = user_attrs["name"]

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
