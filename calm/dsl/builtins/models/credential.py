from .entity import EntityType, Entity
from .validator import PropertyValidator
from .utils import read_file

import re


# Credential


class CredentialType(EntityType):
    __schema_name__ = "Credential"
    __openapi_type__ = "app_credential"


class CredentialValidator(PropertyValidator, openapi_type="app_credential"):
    __default__ = None
    __kind__ = CredentialType


def _credential(**kwargs):
    name = getattr(CredentialType, "__schema_name__")
    name = kwargs.get("name", name)
    bases = (Entity,)
    return CredentialType(name, bases, kwargs)


Credential = _credential()


def basic_cred(
    username, password="", name="default", default=False, type="PASSWORD", filename=None
):

    if filename:
        password = read_file(filename, depth=2)

    secret = {"attrs": {"is_secret_modified": True}, "value": password}

    kwargs = {}
    kwargs["type"] = type
    kwargs["username"] = username
    kwargs["secret"] = secret
    kwargs["name"] = name
    kwargs["default"] = default

    return _credential(**kwargs)


def secret_cred(username, password, name="default", default=False):
    # TODO Handing of PASSWORD/SSH

    secret = {"attrs": {"is_secret_modified": True}, "value": password}

    kwargs = {}
    kwargs["type"] = "SECRET"       # Will replace to PASSWORD at runtime
    kwargs["username"] = username
    kwargs["secret"] = secret
    kwargs["name"] = name
    kwargs["default"] = default

    return _credential(**kwargs)


def secret_cred(
    username,
    name="default",
    secret="default",
    pass_phrase="",
    type="PASSWORD",
    default=False,
):

    secret = {"attrs": {"is_secret_modified": True}, "value": secret}

    # This secret value will be replaced when user is creatring a blueprint
    # Adding "_" as separtor between type and passphrase for identification of secret cred
    # ex: type = "PASSWORD_dslphrase" or "KEY_phrase" or ("KEY_" when phrase = "")

    if not re.match("^[a-zA-Z0-9]*$", pass_phrase):
        raise Exception("Passphrase must be aplhanumeric string only")

    type = "{}_{}".format(type, pass_phrase)

    kwargs = {}
    kwargs["type"] = type  # Will replace to valid type at runtime
    kwargs["username"] = username
    kwargs["secret"] = secret
    kwargs["name"] = name
    kwargs["default"] = default
