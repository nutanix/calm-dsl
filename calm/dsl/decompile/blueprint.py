from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import BlueprintType
from calm.dsl.decompile.credential import get_cred_var_name
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_blueprint_template(cls):

    LOG.debug("Rendering {} blueprint template".format(cls.__name__))
    if not isinstance(cls, BlueprintType):
        raise TypeError("{} is not of type {}".format(cls, BlueprintType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__ or ""

    credential_list = []
    for cred in cls.credentials:
        credential_list.append(get_cred_var_name(cred.__name__))

    service_list = []
    for service in cls.services:
        service_list.append(service.__name__)

    package_list = []
    for package in cls.packages:
        package_list.append(package.__name__)

    substrate_list = []
    for substrate in cls.substrates:
        substrate_list.append(substrate.__name__)

    profile_list = []
    for profile in cls.profiles:
        profile_list.append(profile.__name__)

    user_attrs.update(
        {
            "services": ", ".join(service_list),
            "packages": ", ".join(package_list),
            "substrates": ", ".join(substrate_list),
            "profiles": ", ".join(profile_list),
            "credentials": ", ".join(credential_list),
        }
    )

    text = render_template("blueprint.py.jinja2", obj=user_attrs)
    return text.strip()
