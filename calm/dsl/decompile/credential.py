import uuid
import os

from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import CredentialType
from calm.dsl.decompile.file_handler import get_local_dir


CRED_VAR_NAME_MAP = {}


def render_credential_template(cls):

    global CRED_VAR_NAME_MAP
    if not isinstance(cls, CredentialType):
        raise TypeError("{} is not of type {}".format(cls, CredentialType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__

    file_name = "BP_cred_{}".format(len(CRED_VAR_NAME_MAP))
    file_loc = os.path.join(get_local_dir(), file_name)

    # Storing cred value in the file
    cred_val = cls.secret.get("value", "")
    with open(file_loc, "w+") as fd:
        fd.write(cred_val)

    user_attrs["var_name"] = file_name
    user_attrs["value"] = "read_local_file('{}')".format(file_name)
    # update the map
    CRED_VAR_NAME_MAP[user_attrs["name"]] = user_attrs["var_name"]

    text = render_template("credential.py.jinja2", obj=user_attrs)
    return text.strip()


def get_cred_var_name(cred_name):
    """Get the var name for credential"""

    if cred_name not in CRED_VAR_NAME_MAP:
        raise ValueError("{} not found".format(cred_name))

    return CRED_VAR_NAME_MAP[cred_name]


def get_cred_files():
    """Returns the cred files created for credential"""

    global CRED_VAR_NAME_MAP
    return list(CRED_VAR_NAME_MAP.values())
