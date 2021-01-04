import sys

from .entity import Entity, EntityType
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import PROVIDER
from calm.dsl.providers import get_provider
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# K8S vanilla account


class KubernetesVanillaAccountSpecType(EntityType):
    __schema_name__ = "KubernetesVanillaAccountSpec"
    __openapi_type__ = "kubernetes_vanilla_account_spec"


class KubernetesVanillaAccountSpecValidator(
    PropertyValidator, openapi_type="kubernetes_vanilla_account_spec"
):
    __default__ = None
    __kind__ = KubernetesVanillaAccountSpecType


# K8S karbon account spec


class KubernetesKarbonAccountSpecType(EntityType):
    __schema_name__ = "KubernetesKarbonAccountSpec"
    __openapi_type__ = "kubernetes_karbon_account_spec"

    def compile(cls):
        cdict = super().compile()

        K8sProvider = get_provider(PROVIDER.VM.K8S_POD)
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
            LOG.error("Invalid karbon cluster '{}' given.". format(cluster_name))
        
        cdict["cluster_uuid"] = cluster_uuid
        return cdict


class KubernetesKarbonAccountSpecValidator(
    PropertyValidator, openapi_type="kubernetes_karbon_account_spec"
):
    __default__ = None
    __kind__ = KubernetesKarbonAccountSpecType


# KubernetesAccountSpec class 


class KubernetesAccountSpecType(AccountSpecType):

    __provider_type__ = PROVIDER.ACCOUNT.KUBERNETES

    k8s_subclasses = {
        "vanilla": KubernetesVanillaAccountSpecType,
        "karbon": KubernetesKarbonAccountSpecType
    }

    def compile(cls):

        _type = getattr(cls, "type", "vanilla")
        _mcls = cls.k8s_subclasses.get(_type, None)
        if not _mcls:
            LOG.error("Unknown kubernetes spec type '{}' given.". format(_type))
            sys.exit(-1)

        _cls = _mcls(None, (Entity, ), cls.get_all_attrs())
        return _cls.compile()
        

def kubernetes_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return KubernetesAccountSpecType(name, bases, kwargs)


KubernetesAccountSpec = kubernetes_account_spec()


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
