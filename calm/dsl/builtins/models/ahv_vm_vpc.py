import sys

from .entity import EntityType, Entity
from .helper import common as common_helper
from .validator import PropertyValidator
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle
from calm.dsl.store import Cache

LOG = get_logging_handle(__name__)


class AhvVpcType(EntityType):
    __schema_name__ = "AhvVmVpc"
    __openapi_type__ = "vm_ahv_vpc"

    def compile(cls):

        cdict = super().compile()
        LOG.debug("cdict parent: {}".format(cdict))
        cls_substrate = common_helper._walk_to_parent_with_given_type(
            cls, "SubstrateType"
        )
        account_uuid = (
            cls_substrate.get_referenced_account_uuid() if cls_substrate else ""
        )

        LOG.debug("Vpc  CDict: {}".format(cdict))

        project, project_whitelist = common_helper.get_project_with_pc_account()
        if not account_uuid:
            account_uuid = list(project_whitelist.keys())[0]

        vpc_name = cdict.get("name", "")
        vpc_data = Cache.get_entity_data(
            entity_type=CACHE.ENTITY.AHV_VPC,
            name=vpc_name,
            account_uuid=account_uuid,
        )
        LOG.debug("Account uuid: {}".format(account_uuid))
        if not vpc_data:
            LOG.debug(
                "Ahv Vpc (name = '{}') not found in registered Nutanix PC account (uuid = '{}') "
                "in project (name = '{}')".format(
                    vpc_name, account_uuid, project["name"]
                )
            )
            LOG.error(
                "AHV Vpc {} not found. Please run: calm update cache".format(vpc_name)
            )
            sys.exit(-1)

        project_data = common_helper.get_project(project["name"])
        LOG.debug("Cache data: {}".format(vpc_data))
        LOG.debug("Project data: {}".format(project_data))
        vpc_list = (
            project_data.get("status", {})
            .get("resources", {})
            .get("vpc_reference_list", [])
        )
        for vpc in vpc_list:
            if vpc_data["uuid"] == vpc["uuid"]:
                break
        else:
            LOG.debug(
                "Ahv Vpc (name = '{}') in registered Nutanix PC account (uuid = '{}') "
                "not whitelisted in project (name = '{}')".format(
                    vpc_name, account_uuid, project["name"]
                )
            )
            LOG.error("AHV Vpc {} not found. Please update project.".format(vpc_name))
            sys.exit(-1)

        cdict = {"name": vpc_name, "uuid": vpc_data["uuid"], "kind": "vpc"}

        return cdict


class AhvVpcValidator(PropertyValidator, openapi_type="vm_ahv_vpc"):
    __default__ = None
    __kind__ = AhvVpcType


def ahv_vm_vpc(name, **kwargs):
    bases = (Entity,)
    return AhvVpcType(name, bases, kwargs)


class AhvVpc:
    def __new__(cls, name=""):
        return ahv_vm_vpc(name)
