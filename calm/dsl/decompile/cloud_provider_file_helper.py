import click
import sys
import traceback
import os

# from io import StringIO
# import json
# import ast
# from Crypto.Cipher import AES

from calm.dsl.builtins import get_valid_identifier
from calm.dsl.builtins.models.cloud_provider import CloudProviderType
from calm.dsl.builtins.models.resource_type import ResourceTypeEntity
from calm.dsl.decompile.bp_file_helper import encrypt_decompile_secrets
from calm.dsl.decompile.render import render_template
from calm.dsl.decompile.resource_type import render_resource_type_template
from calm.dsl.decompile.credential import render_credential_template, get_cred_files
from calm.dsl.decompile.cloud_provider import render_cloud_provider_template
from calm.dsl.decompile.variable import get_secret_variable_files
from calm.dsl.decompile.ref_dependency import update_entity_gui_dsl_name
from calm.dsl.decompile.file_handler import get_local_dir
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

SECRETS_FILE_ENCRYPTION_KEY = (
    b"dslengine@calm23"  # the key must be a multiple of 16 bytes
)


def render_cloud_provider_file_template(
    cls, with_secrets=False, contains_encrypted_secrets=False
):

    if not isinstance(cls, CloudProviderType):
        raise TypeError("{} is not of type {}".format(cls, CloudProviderType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    # Step-1: Decompile creds configured on the Provider. Since these are referred to, at
    # multiple places, its crucial this happens first.
    secrets_dict = []
    credential_list = []
    cred_file_dict = dict()
    for _, cred in enumerate(cls.credentials):
        cred_name = getattr(cred, "name", "") or cred.__name__
        cred_type = cred.type
        cred_file_name = "PROVIDER_CRED_{}_{}".format(
            get_valid_identifier(cred_name), cred_type
        )

        credential_list.append(render_credential_template(cred, context="PROVIDER"))
        cred_file_dict[cred_file_name] = getattr(cred, "secret", "").get("value", "")
        secrets_dict.append(
            {
                "context": "credential_definition_list." + cred_name,
                "secret_name": cred_name,
                "secret_value": cred_file_dict[cred_file_name],
            }
        )

    # Step-2: Decompile Resource Types
    entity_name_text_map = {}  # Map to store the [Name: Rendered template for entity]
    for resource_type in cls.resource_types:
        entity_name_text_map[resource_type.get_ref().name] = resource_type

    dependepent_entities = [v for v in entity_name_text_map.values()]
    for k, v in enumerate(dependepent_entities):
        update_entity_gui_dsl_name(v.get_gui_name(), v.__name__)

    # Rendering templates
    implied_credentials = []
    implied_credential_templates = []
    for k, v in enumerate(dependepent_entities):
        if isinstance(v, ResourceTypeEntity):
            dependepent_entities[k] = render_resource_type_template(
                v,
                secrets_dict,
                credential_list=implied_credentials,
                rendered_credential_list=implied_credential_templates,
            )

    # Step-3: Decompile Provider fields
    provider = render_cloud_provider_template(
        cls,
        secrets_dict,
        credential_list=implied_credentials,
        rendered_credential_list=implied_credential_templates,
    )

    # Step-4: Decompile implicit credentials i.e..,.
    # credentials created out of HTTP tasks/variables using basic auth
    for index, cred in enumerate(implied_credentials):
        cred_name = cred["name_in_file"]
        cred_file_name = "{}_{}".format(cred_name, cred["type"])
        credential_list.append(implied_credential_templates[index])
        cred_file_dict[cred_file_name] = cred.get("password", {}).get("value", "")
        secrets_dict.append(
            {
                "context": "credential_definition_list." + cred_name,
                "secret_name": cred["name"],
                "secret_value": cred_file_dict[cred_file_name],
            }
        )

    # Getting the local files used for secrets
    secret_files = get_secret_variable_files()
    secret_files.extend(get_cred_files())

    if with_secrets or contains_encrypted_secrets:
        # If contains_encrypted_secrets is True then populate secrets directly from payload
        # Fill the secret if flag is set
        if secret_files and (not contains_encrypted_secrets):
            click.secho("Enter the value to be used in secret files")
        for file_name in secret_files:
            if contains_encrypted_secrets:
                try:
                    secret_val = cred_file_dict[file_name]
                except KeyError:

                    # Secret files corresponding to non-cred secrets. Value would have been
                    # already written to the file if available in the payload. No need to write again
                    continue
                except Exception as exp:
                    LOG.debug("Got traceback\n{}".format(traceback.format_exc()))
                    LOG.error("Secret value not found due to {}".format(exp))
                    sys.exit(-1)
            else:
                secret_val = click.prompt(
                    "\nValue for {}".format(file_name),
                    default="",
                    show_default=False,
                    hide_input=True,
                )
            file_loc = os.path.join(get_local_dir(), file_name)
            with open(file_loc, "w+") as fd:
                fd.write(secret_val)

    is_any_secret_value_available = False
    for _e in secrets_dict:
        if _e.get("secret_value", ""):
            is_any_secret_value_available = True
            break
    if is_any_secret_value_available:
        LOG.info("Creating secret metadata file")
        encrypt_decompile_secrets(secrets_dict=secrets_dict)

    user_attrs.update(
        {
            "secret_files": secret_files,
            "credentials": credential_list,
            "dependent_entities": dependepent_entities,
            "provider": provider,
            "contains_encrypted_secrets": contains_encrypted_secrets,
        }
    )
    text = render_template("cloud_provider_file_helper.py.jinja2", obj=user_attrs)
    return text.strip()
