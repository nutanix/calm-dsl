from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class KubernetesAccountSpecType(AccountSpecType):
    __schema_name__ = "KubernetesAccountSpec"
    __openapi_type__ = "kubernetes_account_spec"

    __provider_type__ = PROVIDER.ACCOUNT.KUBERNETES


class KubernetesAccountSpecValidator(
    PropertyValidator, openapi_type="kubernetes_account_spec"
):
    __default__ = None
    __kind__ = KubernetesAccountSpecType


def kubernetes_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return KubernetesAccountSpecType(name, bases, kwargs)


KubernetesAccountSpec = kubernetes_account_spec()


def basic_auth(username, password):
    return {
        "username": username,
        "password": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": password,
        },
        "type": "basic",
    }


def client_certificate_auth(client_key, client_certificate):
    return {
        "client_certificate": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_certificate,
        },
        "client_key": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_key,
        },
        "type": "client_certificate",
    }


def ca_ceritificate_auth(client_key, client_certificate, ca_certificate):
    return {
        "client_certificate": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_certificate,
        },
        "client_key": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": client_key,
        },
        "ca_certificate": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": ca_certificate,
        },
        "type": "ca_certificate",
    }


class KubernetesAuth:
    basic = basic_auth
    client_certificate = client_certificate_auth
    ca_ceritificate = ca_ceritificate_auth
