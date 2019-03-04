from .entity import EntityType, Entity
from .validator import PropertyValidator


# Credential

class CredentialType(EntityType):
    __schema_name__ = "Credential"
    __openapi_type__ = "app_credential"


class CredentialValidator(PropertyValidator, openapi_type="app_credential"):
    __default__ = None
    __kind__ = CredentialType


def _credential(**kwargs):
    name = getattr(CredentialType, "__schema_name__")
    bases = (Entity, )
    return CredentialType(name, bases, kwargs)


Credential = _credential()


def basic_cred(username, password):

    secret = {
        "attrs": {
            "is_secret_modified": True,
        },
        "value": password,
    }

    kwargs = {}
    kwargs["type"] = "PASSWORD"
    kwargs["username"] = username
    kwargs["secret"] = secret

    return _credential(**kwargs)
