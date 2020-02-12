from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import BlueprintType
from calm.dsl.decompile.credential import render_credential_template


def render_blueprint_template(cls, local_dir=None):

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
    cred_file_map = {}
    for cred in cls.credentials:
        file_name = "cred_{}".format(cred.__name__)
        cred_val = cred.secret.get("value", "")
        cred_file_map[file_name] = cred_val
        cred.secret["value"] = "read_local_file('{}')".format(file_name)
        creds.append(render_credential_template(cred))

    if local_dir:
        for cred_file, cred_val in cred_file_map.items():
            file_loc = "{}/{}".format(local_dir, cred_file)
            with open(file_loc, "w+") as fd:
                fd.write(cred_val)

    user_attrs.update(
        {
            "services": ", ".join(service_list),
            "packages": ", ".join(package_list),
            "substrates": ", ".join(substrate_list),
            "profiles": ", ".join(profile_list),
            "credentials": ", ".join(creds),
        }
    )

    text = render_template("blueprint.py.jinja2", obj=user_attrs)
    return text.strip()
