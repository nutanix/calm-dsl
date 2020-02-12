import os
from ruamel import yaml

from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import SubstrateType
from calm.dsl.decompile.variable import render_variable_template
from calm.dsl.decompile.action import render_action_template


def render_substrate_template(cls, spec_dir=None):

    if not isinstance(cls, SubstrateType):
        raise TypeError("{} is not of type {}".format(cls, SubstrateType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__
    user_attrs["readiness_probe"] = cls.readiness_probe.get_dict()

    provider_spec = cls.provider_spec

    # creating a file for storing provider_spe
    provider_spec_file_name = cls.__name__ + "_provider_spec"
    user_attrs["provider_spec"] = "specs/{}".format(provider_spec_file_name)

    if spec_dir:
        # TODO Edit for windows
        spec_dir = "{}/{}".format(spec_dir, provider_spec_file_name)
        with open(spec_dir, "w+") as fd:
            fd.write(yaml.dump(provider_spec, default_flow_style=False))

    text = render_template(schema_file="substrate.py.jinja2", obj=user_attrs)
    return text.strip()
