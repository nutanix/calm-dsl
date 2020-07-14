from .entity import EntityType, Entity
from .validator import PropertyValidator
from .utils import read_file


# Credential


class CredentialType(EntityType):
    __schema_name__ = "Credential"
    __openapi_type__ = "app_credential"


class CredentialValidator(PropertyValidator, openapi_type="app_credential"):
    __default__ = None
    __kind__ = CredentialType


def _credential(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return CredentialType(name, bases, kwargs)


Credential = _credential()


def basic_cred(
    username,
    password="",
    name="default",
    default=False,
    type="PASSWORD",
    filename=None,
    editables=dict(),
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
    if editables:
        kwargs["editables"] = editables

    return _credential(**kwargs)


def secret_cred(
    username,
    name="default",
    secret="default",
    type="PASSWORD",
    default=False,
    editables=dict(),
):

    # This secret value will be replaced when user is creatring a blueprint
    secret = {"attrs": {"is_secret_modified": True}, "value": "", "secret": secret}

    kwargs = {}
    kwargs["type"] = type
    kwargs["username"] = username
    kwargs["secret"] = secret
    kwargs["name"] = name
    kwargs["default"] = default
    if editables:
        kwargs["editables"] = editables

    return _credential(**kwargs)
