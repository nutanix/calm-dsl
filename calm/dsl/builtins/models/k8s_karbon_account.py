import sys

from .entity import EntityType, Entity

from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY
from calm.dsl.providers import get_provider

LOG = get_logging_handle(__name__)

# Kubernetes Karbon Account


class K8sKarbonAccountType(EntityType):
    __schema_name__ = "K8sKarbonAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.K8S_KARBON

    def compile(cls):
        cdict = super().compile()

        K8sProvider = get_provider("K8S_POD")
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


class K8sKarbonAccountValidator(
    PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.K8S_KARBON
):
    __default__ = None
    __kind__ = K8sKarbonAccountType


def k8s_karbon_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return K8sKarbonAccountType(name, bases, kwargs)


K8sKarbonAccountData = k8s_karbon_account()
