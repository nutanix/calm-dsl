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
