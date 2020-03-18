from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.service import render_service_template
from calm.dsl.decompile.package import render_package_template
from calm.dsl.decompile.vm_disk_package import render_vm_disk_package_template
from calm.dsl.decompile.substrate import render_substrate_template
from calm.dsl.decompile.deployment import render_deployment_template
from calm.dsl.decompile.profile import render_profile_template
from calm.dsl.decompile.credential import render_credential_template
from calm.dsl.decompile.blueprint import render_blueprint_template
from calm.dsl.builtins import BlueprintType


def render_bp_file_template(cls, local_dir=None, spec_dir=None):

    if not isinstance(cls, BlueprintType):
        raise TypeError("{} is not of type {}".format(cls, BlueprintType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    # Find default cred
    default_cred = cls.default_cred

    credential_list = []
    cred_file_map = {}
    for index, cred in enumerate(cls.credentials):
        file_name = "Bp_cred_{}".format(index)
        cred_val = cred.secret.get("value", "")
        cred_file_map[file_name] = cred_val
        cred.secret["value"] = "read_local_file('{}')".format(file_name)
        if cred.__name__ == default_cred.__name__:
            cred.default=True
        credential_list.append(
            render_credential_template(cred, cred_var_name=file_name)
        )

    if local_dir:
        for cred_file, cred_val in cred_file_map.items():
            file_loc = "{}/{}".format(local_dir, cred_file)
            with open(file_loc, "w+") as fd:
                fd.write(cred_val)

    service_list = []
    for service in cls.services:
        service_list.append(render_service_template(service))

    package_list = []
    for package in cls.packages:
        if getattr(package, "__kind__") == "app_package":
            package_list.append(render_package_template(package))
        
        else:
            package_list.append(render_vm_disk_package_template(package))

    substrate_list = []
    for substrate in cls.substrates:
        substrate_list.append(render_substrate_template(substrate))

    profile_list = []
    deployments = []
    for profile in cls.profiles:
        profile_list.append(render_profile_template(profile))
        deployments.extend(profile.deployments)

    deployment_list = []
    for deployment in deployments:
        deployment_list.append(render_deployment_template(deployment))

    blueprint = render_blueprint_template(cls)
    user_attrs.update(
        {
            "credentials": credential_list,
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
