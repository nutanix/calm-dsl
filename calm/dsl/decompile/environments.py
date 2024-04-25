from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.ref import render_ref_template
from calm.dsl.decompile.provider import render_provider_template
from calm.dsl.decompile.substrate import render_substrate_template
from calm.dsl.builtins.models.environment import EnvironmentType
from .decompile_helpers import process_variable_name
from calm.dsl.decompile.variable import get_secret_variable_files
from calm.dsl.builtins import get_valid_identifier

from calm.dsl.decompile.credential import (
    render_credential_template,
    get_cred_files,
    get_cred_var_name,
)

from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_environment_template(
    environment_cls,
    metadata_obj=None,
    entity_context="",
    CONFIG_SPEC_MAP={},
    credentials=[],
):
    LOG.debug("Rendering {} environment template".format(environment_cls.__name__))
    if not isinstance(environment_cls, EnvironmentType):
        raise TypeError("{} is not of type {}".format(environment_cls, environment))

    # Update entity context
    entity_context = entity_context + "_Environment_" + environment_cls.__name__

    environment_name = getattr(environment_cls, "name", "") or environment_cls.__name__

    rendered_credential_list = []
    credentials_list = []
    for cred in credentials:
        rendered_credential_list.append(render_credential_template(cred))
        credentials_list.append(get_cred_var_name(cred.name))

    # Getting the local files used for secrets
    secret_files = get_secret_variable_files()
    secret_files.extend(get_cred_files())

    class_name = "ENV_{}".format(get_valid_identifier(environment_cls.__name__))

    user_attrs = {
        "name": class_name,
        "credentials": rendered_credential_list,
        "credentials_list": credentials_list,
        "secret_files": secret_files,
    }

    rendered_substrates_list = []

    # holds substrate class names to include in decompiled 'Environment' class
    substrates_list = []

    substrate_name_counter = 1

    if environment_cls.substrates:
        for substrate in environment_cls.substrates:
            if substrate.__name__ in substrates_list:
                new_name = "{}_{}".format(substrate.name, str(substrate_name_counter))
                substrate.__name__ = get_valid_identifier(
                    new_name
                )  # creating valid python class name for substrate
                rendered_substrates_list.append(render_substrate_template(substrate))
                substrates_list.append(substrate.__name__)
                substrate_name_counter += 1
            else:
                substrate.__name__ = get_valid_identifier(
                    substrate.name
                )  # creating valid python class name for substrate
                rendered_substrates_list.append(render_substrate_template(substrate))
                substrates_list.append(substrate.__name__)

    user_attrs["substrates"] = rendered_substrates_list
    user_attrs["substrates_list"] = substrates_list

    rendered_providers_list = []
    if environment_cls.providers:
        for provider in environment_cls.providers:
            rendered_providers_list.append(render_provider_template(provider))
    user_attrs["providers"] = rendered_providers_list

    gui_display_name = getattr(environment_cls, "name", "") or environment_cls.__name__
    if gui_display_name != environment_cls.__name__:
        user_attrs["gui_display_name"] = gui_display_name

    text = render_template(schema_file="environments.py.jinja2", obj=user_attrs)
    return text.strip()
