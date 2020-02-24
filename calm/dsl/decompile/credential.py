import uuid

from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import CredentialType


CRED_VAR_NAME_MAP = {}


def render_credential_template(cls, cred_var_name=None):

    global CRED_VAR_NAME_MAP
    if not isinstance(cls, CredentialType):
        raise TypeError("{} is not of type {}".format(cls, CredentialType))

    user_attrs = cls.get_user_attrs()
    user_attrs["name"] = cls.__name__
    user_attrs["description"] = cls.__doc__
    user_attrs["var_name"] = cred_var_name or "CRED_{}".format(str(uuid.uuid4())[:8])

    CRED_VAR_NAME_MAP[user_attrs["name"]] = user_attrs["var_name"]

    cred_type = cls.type
    if cred_type == "PASSWORD":
        user_attrs["value"] = user_attrs["secret"].get("value", "")

    text = render_template("cred_passwd_type.py.jinja2", obj=user_attrs)
    return text.strip()


def get_cred_var_name(cred_name):
    """Get the var name for credential"""

    if cred_name not in CRED_VAR_NAME_MAP:
        raise ValueError("{} not found".format(cred_name))

    return CRED_VAR_NAME_MAP[cred_name]
