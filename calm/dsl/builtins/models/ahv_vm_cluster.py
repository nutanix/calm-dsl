import sys

from .entity import EntityType, Entity
from .helper import common as common_helper
from .validator import PropertyValidator
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache

LOG = get_logging_handle(__name__)


class AhvClusterType(EntityType):
    __schema_name__ = "AhvVmCluster"
    __openapi_type__ = "vm_ahv_cluster"

    def compile(cls):

        cdict = super().compile()

        cls_substrate = common_helper._walk_to_parent_with_given_type(
            cls, "SubstrateType"
        )
        account_uuid = (
            cls_substrate.get_referenced_account_uuid() if cls_substrate else ""
        )

        LOG.debug("Cluster  CDict: {}".format(cdict))

        project, project_whitelist = common_helper.get_project_with_pc_account()
        if not account_uuid:
            account_uuid = list(project_whitelist.keys())[0]

        cluster_name = cdict.get("name", "")
        cluster_data = Cache.get_entity_data(
            entity_type=CACHE.ENTITY.AHV_CLUSTER,
            name=cluster_name,
            account_uuid=account_uuid,
        )

        if not cluster_data:
            LOG.debug(
                "Ahv Cluster (name = '{}') not found in registered Nutanix PC account (uuid = '{}') "
                "in project (name = '{}')".format(
                    cluster_name, account_uuid, project["name"]
                )
            )
            LOG.error(
                "AHV Cluster {} not found. Please run: calm update cache".format(
                    cluster_name
                )
            )
            sys.exit(-1)

        project_data = common_helper.get_project(project["name"])
        LOG.debug("Project data: {}".format(project_data))
        cluster_list = (
            project_data.get("status", {})
            .get("resources", {})
            .get("cluster_reference_list", [])
        )
        for cluster in cluster_list:
            if cluster_data["uuid"] == cluster["uuid"]:
                break
        else:
            LOG.debug(
                "Ahv Cluster (name = '{}') in registered Nutanix PC account (uuid = '{}') "
                "not whitelisted in project (name = '{}')".format(
                    cluster_name, account_uuid, project["name"]
                )
            )
            LOG.error(
                "AHV Cluster {} not found. Please update project.".format(cluster_name)
            )
            sys.exit(-1)

        cdict = {"name": cluster_name, "uuid": cluster_data["uuid"]}

        return cdict


class AhvClusterValidator(PropertyValidator, openapi_type="vm_ahv_cluster"):
    __default__ = None
    __kind__ = AhvClusterType


def ahv_vm_cluster(name, **kwargs):
    bases = (Entity,)
    return AhvClusterType(name, bases, kwargs)


class AhvCluster:
    def __new__(cls, name=""):
        return ahv_vm_cluster(name)
