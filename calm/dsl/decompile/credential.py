import os

from calm.dsl.decompile.render import render_template
from calm.dsl.builtins import CredentialType
from calm.dsl.decompile.file_handler import get_local_dir
from calm.dsl.log import get_logging_handle
from calm.dsl.builtins import get_valid_identifier

LOG = get_logging_handle(__name__)
CRED_VAR_NAME_MAP = {}
CRED_FILES = []


def render_credential_template(cls):

    global CRED_VAR_NAME_MAP, CRED_FILES
    LOG.debug("Rendering {} credential template".format(cls.__name__))
    if not isinstance(cls, CredentialType):
        raise TypeError("{} is not of type {}".format(cls, CredentialType))

    user_attrs = cls.get_user_attrs()
    user_attrs["description"] = cls.__doc__

    cred_type = user_attrs.get("cred_class", "")

    var_name = "BP_CRED_{}".format(get_valid_identifier(cls.__name__))
    user_attrs["var_name"] = var_name
    if user_attrs.get("editables", {}):
        user_attrs["editables"] = user_attrs["editables"].get_dict()
    CRED_VAR_NAME_MAP[user_attrs["name"]] = var_name

    if cred_type == "static":

        file_name = "{}_{}".format(var_name, user_attrs["type"])
        create_file_from_file_name(file_name)
        user_attrs["value"] = file_name
        text = render_template("basic_credential.py.jinja2", obj=user_attrs)

    elif cred_type == "dynamic":

        for var_obj in user_attrs.get("variable_list", []):
            if var_obj.type == "SECRET":
                file_name = "{}_VAR_{}_SECRET".format(
                    var_name, get_valid_identifier(var_obj.name)
                )
                create_file_from_file_name(file_name)
                var_obj.value = file_name

        text = render_template("dynamic_credential.py.jinja2", obj=user_attrs)

    else:
        raise TypeError("{} is not a supported cred class".format(cred_type))
    return text.strip()


def create_file_from_file_name(file_name):
    """create a file on local directory and add to global file stack for given file name"""
    file_loc = os.path.join(get_local_dir(), file_name)

    # Storing empty value in the file
    with open(file_loc, "w+") as fd:
        fd.write("")

    CRED_FILES.append(file_name)


def get_cred_var_name(cred_name):
    """Get the var name for credential"""

    if cred_name not in CRED_VAR_NAME_MAP:
        raise ValueError("{} not found".format(cred_name))

    return CRED_VAR_NAME_MAP[cred_name]


def get_cred_files():
    """Returns the cred files created for credential"""

    global CRED_FILES
    return CRED_FILES


def init_cred_globals():
    """Reinitialises global vars used for credentials"""

    global CRED_VAR_NAME_MAP, CRED_FILES
    CRED_VAR_NAME_MAP = {}
    CRED_FILES = []
