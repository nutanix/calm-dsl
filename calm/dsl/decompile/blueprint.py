from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import ProfileType, BlueprintType
from tests.decompile.test_decompile import bp_cls
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.credential import render_credential_template


def render_blueprint_template(cls):

    if not isinstance(cls, BlueprintType):
        raise TypeError("{} is not of type {}".format(cls, BlueprintType))
    
    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

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
    
    creds = []
    for cred in cls.credentials:
        creds.append(render_credential_template(cred))
    
    user_attrs.update(
        {
            "services": ", ".join(service_list),
            "packages": ", ".join(package_list),
            "substrates": ", ".join(substrate_list),
            "profiles": ", ".join(profile_list),
            "credentials": ", ".join(creds)
        }
    )

    text = render_template("blueprint.py.jinja2", obj=user_attrs)
    return text.strip()


print(render_blueprint_template(bp_cls))
