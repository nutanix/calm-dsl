from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import DeploymentType
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)
DEPLOYMENT_NAME_MAP = {}


def render_deployment_template(cls):

    global DEPLOYMENT_NAME_MAP
    LOG.debug("Rendering {} deployment template".format(cls.__name__))
    if not isinstance(cls, DeploymentType):
        raise TypeError("{} is not of type {}".format(cls, DeploymentType))

    # Entity context
    entity_context = "Deployment_" + cls.__name__

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or "{} Deployment description".format(
        cls.__name__
    )

    # Update deployment name map and gui name
    gui_display_name = getattr(cls, "name", "")
    if not gui_display_name:
        gui_display_name = cls.__name__

    elif gui_display_name != cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    DEPLOYMENT_NAME_MAP[gui_display_name] = cls.__name__

    depends_on_list = []
    for entity in user_attrs.get("dependencies", []):
        depends_on_list.append(render_ref_template(entity))

    if cls.substrate:
        user_attrs["substrate"] = render_ref_template(cls.substrate)

    package_list = []
    for entity in user_attrs.get("packages", []):
        package_list.append(render_ref_template(entity))

    user_attrs["packages"] = ", ".join(package_list)
    user_attrs["dependencies"] = ",".join(depends_on_list)

    text = render_template("deployment.py.jinja2", obj=user_attrs)
    return text.strip()


def get_deployment_display_name(name):
    """returns the class name used for entity ref"""

    global DEPLOYMENT_NAME_MAP
    return DEPLOYMENT_NAME_MAP.get(name, None)
