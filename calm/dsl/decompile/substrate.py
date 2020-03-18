from ruamel import yaml

from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.credential import get_cred_var_name
from calm.dsl.decompile.file_handler import get_specs_dir, get_specs_dir_key
from calm.dsl.builtins import SubstrateType


def render_substrate_template(cls):

    if not isinstance(cls, SubstrateType):
        raise TypeError("{} is not of type {}".format(cls, SubstrateType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__
    user_attrs["readiness_probe"] = cls.readiness_probe.get_dict()

    # TODO fix this mess
    cred = user_attrs["readiness_probe"].pop("credential")
    user_attrs["readiness_probe_cred"] = "ref({})". format(get_cred_var_name(cred.__name__))

    # TODO use provider specific methods for reading provider_spec
    # i.e for ahv : read_ahv_spec()

    provider_spec = cls.provider_spec
    # creating a file for storing provider_spe
    provider_spec_file_name = cls.__name__ + "_provider_spec.yaml"
    user_attrs["provider_spec"] = "{}/{}".format(get_specs_dir_key(), provider_spec_file_name)

    spec_dir = get_specs_dir()
    # TODO Edit for windows
    file_location = "{}/{}".format(spec_dir, provider_spec_file_name)
    with open(file_location, "w+") as fd:
        fd.write(yaml.dump(provider_spec, default_flow_style=False))

    text = render_template(schema_file="substrate.py.jinja2", obj=user_attrs)
    return text.strip()
