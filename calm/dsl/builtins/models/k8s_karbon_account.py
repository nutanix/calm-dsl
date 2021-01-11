import sys

from .entity import Entity
from .validator import PropertyValidator
from .account import AccountSpecType

from calm.dsl.constants import VM, PROVIDER
from calm.dsl.providers import get_provider
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


class KubernetesKarbonAccountSpecType(AccountSpecType):
    __schema_name__ = "KubernetesKarbonAccountSpec"
    __openapi_type__ = "kubernetes_karbon_account_spec"

    __provider_type__ = PROVIDER.NUTANIX.KARBON

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


def karbon_account_spec(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return KubernetesKarbonAccountSpecType(name, bases, kwargs)


KarbonAccountSpec = karbon_account_spec()

