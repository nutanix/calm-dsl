import sys

from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER, KUBERNETES, VM
from calm.dsl.providers import get_provider
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# K8S vanilla account


class KubernetesVanillaAccountSpecType(AccountSpecType):
    __schema_name__ = "KubernetesVanillaAccountSpec"
    __openapi_type__ = "kubernetes_vanilla_account_spec"


class KubernetesVanillaAccountSpecValidator(
    PropertyValidator, openapi_type="kubernetes_vanilla_account_spec"
):
    __default__ = None
    __kind__ = KubernetesVanillaAccountSpecType


def kubernetes_vanilla_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return KubernetesVanillaAccountSpecType(name, bases, kwargs)


VanillaAccountSpec = kubernetes_vanilla_account_spec()


# K8S karbon account spec


class KubernetesKarbonAccountSpecType(AccountSpecType):
    __schema_name__ = "KubernetesKarbonAccountSpec"
    __openapi_type__ = "kubernetes_karbon_account_spec"

    def compile(cls):
        cdict = super().compile()

        K8sProvider = get_provider(VM.K8S_POD)
        K8sObj = K8sProvider.get_api_obj()

        res, err = K8sObj.karbon_clusters()
        if err:
            LOG.error(err)
            sys.exit(-1)

        res = res.json()

        cluster_name = cdict.pop("cluster", None)
        if not cluster_name:
            LOG.error("Karbon cluster not given.")
            sys.exit(-1)

        cluster_uuid = None
        for entity in res["entities"]:
            if entity["status"]["name"] == cluster_name:
                cluster_uuid = entity["status"]["resources"]["cluster_uuid"]

        if not cluster_uuid:
            LOG.error("Invalid karbon cluster '{}' given.".format(cluster_name))

        cdict["cluster_uuid"] = cluster_uuid
        return cdict


class KubernetesKarbonAccountSpecValidator(
    PropertyValidator, openapi_type="kubernetes_karbon_account_spec"
):
    __default__ = None
    __kind__ = KubernetesKarbonAccountSpecType


def kubernetes_karbon_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return KubernetesKarbonAccountSpecType(name, bases, kwargs)


KarbonAccountSpec = kubernetes_karbon_account_spec()


# Kubernetes Auth


def basic_auth(username, password):
    return {
        "username": username,
        "password": {
            "attrs": {
                "is_secret_modified": True,
            },
            "value": password,
        },
        "type": AUTH.KUBERNETES.BASIC,
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
        "type": AUTH.KUBERNETES.CLIENT_CERTIFICATE,
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
        "type": AUTH.KUBERNETES.CA_CERTIFICATE,
    }


class KubernetesAuth:
    basic = basic_auth
    client_certificate = client_certificate_auth
    ca_ceritificate = ca_ceritificate_auth
