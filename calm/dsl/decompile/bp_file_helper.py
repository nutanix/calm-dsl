from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.service import render_service_template
from calm.dsl.decompile.package import render_package_template
from calm.dsl.decompile.substrate import render_substrate_template
from calm.dsl.decompile.deployment import render_deployment_template
from calm.dsl.decompile.profile import render_profile_template
from calm.dsl.decompile.blueprint import render_blueprint_template
from calm.dsl.builtins import BlueprintType


def render_bp_file_template(cls, local_dir=None, spec_dir=None):

    if not isinstance(cls, BlueprintType):
        raise TypeError("{} is not of type {}".format(cls, BlueprintType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    service_list = []
    for service in cls.services:
        service_list.append(render_service_template(service))

    package_list = []
    for package in cls.packages:
        package_list.append(render_package_template(package))

    substrate_list = []
    for substrate in cls.substrates:
        substrate_list.append(render_substrate_template(substrate, spec_dir))

    profile_list = []
    deployments = []
    for profile in cls.profiles:
        profile_list.append(render_profile_template(profile))
        deployments.extend(profile.deployments)

    deployment_list = []
    for deployment in deployments:
        deployment_list.append(render_deployment_template(deployment))

    blueprint = render_blueprint_template(cls, local_dir)
    user_attrs.update(
        {
            "services": service_list,
            "packages": package_list,
            "substrates": substrate_list,
            "profiles": profile_list,
            "deployments": deployment_list,
            "blueprint": blueprint,
        }
    )

    text = render_template("bp_file_helper.py.jinja2", obj=user_attrs)
    return text.strip()
