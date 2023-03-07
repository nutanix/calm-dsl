import sys
import uuid

from calm.dsl.db.table_config import AhvSubnetsCache

from .entity import Entity, EntityType
from .validator import PropertyValidator
from .helper import common as common_helper

from .ahv_vm_cluster import AhvCluster
from .ahv_vm_vpc import AhvVpc

from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.api.handle import get_api_client
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# CalmRef


class CalmRefType(EntityType):
    """Metaclass for calm references"""

    __schema_name__ = "CalmRef"
    __openapi_type__ = "app_calm_ref"

    def compile(cls):
        """compiles the calm_ref object"""

        ref_cls = getattr(cls, "__ref_cls__")
        user_attrs = cls.get_user_attrs()
        return ref_cls.compile(cls, **user_attrs)

    def __getitem__(cls, key):
        """return the vale in compiled class payload"""
        data = cls.compile()
        return data[key]


class CalmRefValidator(PropertyValidator, openapi_type="app_calm_ref"):
    __default__ = None
    __kind__ = CalmRefType


def _calm_ref(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return CalmRefType(name, bases, kwargs)


class Ref:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Subnet:
        def __new__(cls, **kwargs):
            kwargs["__ref_cls__"] = cls
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):

            cluster = kwargs.get("cluster")
            vpc = kwargs.get("vpc")
            account_uuid = kwargs.get("account_uuid")
            subnet_cache_data = None
            try:
                provider_obj = cls.__parent__
                subnet_account = provider_obj.account_reference.get_dict()
                account_uuid = subnet_account.get("uuid")

            except Exception:
                pass

            LOG.debug("Searching for subnet with name: {}".format(name))
            subnet_cache_data = AhvSubnetsCache.get_entity_data(
                name, cluster=cluster, vpc=vpc, account_uuid=account_uuid
            )

            if not subnet_cache_data:
                raise Exception(
                    "AHV Subnet {} not found. Please run: calm update cache".format(
                        name
                    )
                )

            return {"kind": "subnet", "name": name, "uuid": subnet_cache_data["uuid"]}

    class User:
        def __new__(cls, name, **kwargs):

            directory = kwargs.get("directory") or ""
            display_name = kwargs.get("display_name") or ""
            user_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.USER,
                name=name,
                directory=directory,
                display_name=display_name,
            )

            if not user_cache_data:
                raise Exception(
                    "User {} not found. Please run: calm update cache".format(name)
                )

            return {"kind": "user", "name": name, "uuid": user_cache_data["uuid"]}

    class Group:
        def __new__(cls, name, **kwargs):

            directory = kwargs.get("directory") or ""
            display_name = kwargs.get("display_name") or ""
            user_group_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.USER_GROUP,
                name=name,
                directory=directory,
                display_name=display_name,
            )

            if not user_group_cache_data:
                raise Exception(
                    "User Group {} not found. Please run: calm update cache".format(
                        name
                    )
                )

            return {
                "kind": "user_group",
                "name": name,
                "uuid": user_group_cache_data["uuid"],
            }

    class Account:
        def __new__(cls, name, **kwargs):

            kwargs["__ref_cls__"] = cls
            kwargs["name"] = name
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):

            provider_type = kwargs.get("provider_type") or ""
            account_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.ACCOUNT,
                name=name,
                provider_type=provider_type,
            )

            if not account_cache_data:
                raise Exception(
                    "Account {} not found. Please run: calm update cache".format(name)
                )

            return {"kind": "account", "name": name, "uuid": account_cache_data["uuid"]}

    class Role:
        def __new__(cls, name, **kwargs):

            role_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.ROLE, name=name
            )
            if not role_cache_data:
                raise Exception(
                    "Role {} not found. Please run: calm update cache".format(name)
                )
            return {"kind": "role", "name": name, "uuid": role_cache_data["uuid"]}

    class Project:
        def __new__(cls, name, **kwargs):

            project_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.PROJECT, name=name
            )
            if not project_cache_data:
                raise Exception(
                    "Project {} not found. Please run: calm update cache".format(name)
                )
            return {"kind": "project", "name": name, "uuid": project_cache_data["uuid"]}

    class Environment:
        def __new__(cls, **kwargs):

            kwargs["__ref_cls__"] = cls
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):
            """cls = CalmRef object"""

            project_cache_data = common_helper.get_cur_context_project()
            project_name = project_cache_data.get("name")
            project_uuid = project_cache_data.get("uuid")
            environment_cache_data = Cache.get_entity_data(
                entity_type="environment", name=name, project_uuid=project_uuid
            )
            if not environment_cache_data:
                LOG.error(
                    "Environment '{}' not found in project '{}'. Please run: calm update cache".format(
                        name, project_name
                    )
                )
                sys.exit(-1)

            return {
                "kind": "environment",
                "name": name,
                "uuid": environment_cache_data["uuid"],
            }

    class DirectoryService:
        def __new__(cls, name, **kwargs):

            ds_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.DIRECTORY_SERVICE, name=name
            )
            if not ds_cache_data:
                raise Exception(
                    "Directory Service {} not found. Please run: calm update cache".format(
                        name
                    )
                )
            return {
                "kind": "directory_service",
                "name": name,
                "uuid": ds_cache_data["uuid"],
            }

    class Vm:
        def __new__(cls, **kwargs):

            kwargs["__ref_cls__"] = cls
            return _calm_ref(**kwargs)

        def compile(cls, name="", **kwargs):
            """cls = CalmRef object"""

            client = get_api_client()
            account_uuid = ""
            try:
                account_ref = cls.__parent__.attrs.get("account_reference", {})
                account_uuid = account_ref.get("uuid", "")
            except Exception as exp:
                pass

            vm_uuid = kwargs.get("uuid", "")

            if name:
                params = {"filter": "name=={}".format(name), "length": 250}
                res, err = client.account.vms_list(account_uuid, params)
                if err:
                    LOG.error(err)
                    sys.exit(-1)

                res = res.json()
                if res["metadata"]["total_matches"] == 0:
                    LOG.error("No vm with name '{}' found".format(name))
                    sys.exit(-1)

                elif res["metadata"]["total_matches"] > 1 and not vm_uuid:
                    LOG.error(
                        "Multiple vms with same name found. Please provide vm uuid"
                    )
                    sys.exit(-1)

                elif not vm_uuid:
                    vm_uuid = res["entities"][0]["status"]["uuid"]

            # TODO add valdiations on suppiled uuid
            vm_ref = {"uuid": vm_uuid, "kind": "vm"}

            # name is required parameter, else api will fail
            vm_ref["name"] = (
                name if name else "_VM_NAME_{}".format(str(uuid.uuid4())[:10])
            )

            return vm_ref

    class RecoveryPoint:
        def __new__(cls, **kwargs):

            kwargs["__ref_cls__"] = cls
            return _calm_ref(**kwargs)

        def compile(cls, name=None, **kwargs):

            cls_substrate = common_helper._walk_to_parent_with_given_type(
                cls, "SubstrateType"
            )
            account_uuid = (
                cls_substrate.get_referenced_account_uuid() if cls_substrate else ""
            )
            account_uuid = account_uuid or kwargs.get("account_uuid", "")
            if not account_uuid:
                LOG.error("Account uuid not found")
                sys.exit("Account not found for vm recovery point")

            vrs_uuid = kwargs.get("uuid", "")
            payload = {"filter": "account_uuid=={}".format(account_uuid)}
            if vrs_uuid:
                payload["filter"] += ";uuid=={}".format(vrs_uuid)
            else:
                payload["filter"] += ";name=={}".format(name)

            client = get_api_client()
            vrc_map = client.vm_recovery_point.get_name_uuid_map(payload)

            if not vrc_map:
                log_msg = "No recovery point found with " + (
                    "uuid='{}'".format(vrs_uuid)
                    if vrs_uuid
                    else "name='{}'".format(name)
                )
                LOG.error(log_msg)
                sys.exit("No recovery point found")

            # there will be single key
            vrc_name = list(vrc_map.keys())[0]
            vrc_uuid = vrc_map[vrc_name]

            if isinstance(vrc_uuid, list):
                LOG.error(
                    "Multiple recovery points found with name='{}'. Please provide uuid.".format(
                        vrc_name
                    )
                )
                LOG.debug("Found recovery point uuids: {}".format(vrc_uuid))
                sys.exit("Multiple recovery points found")

            return {
                "kind": "vm_recovery_point",
                "name": vrc_name,
                "uuid": vrc_uuid,
            }

    class Cluster:
        def __new__(cls, name=None, account_name=None, **kwargs):

            kwargs["__ref_cls__"] = cls
            kwargs["account_name"] = account_name
            kwargs["name"] = name
            return _calm_ref(**kwargs)

        def compile(cls, name=None, **kwargs):

            if name.startswith("@@{") and name.endswith("}@@"):
                return {"kind": "cluster", "uuid": name}
            account_name = kwargs.get("account_name", None)
            if account_name:
                cache_acc_data = Cache.get_entity_data(
                    CACHE.ENTITY.ACCOUNT, account_name
                )
                if not cache_acc_data:
                    LOG.error(
                        "Failed to find account with name: {}".format(account_name)
                    )
                    sys.exit("Account name={} not found.".format(account_name))

                # We found the account
                cache_cluster_data = Cache.get_entity_data(
                    CACHE.ENTITY.AHV_CLUSTER, name, account_uuid=cache_acc_data["uuid"]
                )
                if not cache_cluster_data:
                    LOG.error(
                        "Failed to find cluster with name: {}, account: {}".format(
                            name, account_name
                        )
                    )
                    sys.exit("Cluster name={} not found".format(name))
                return {
                    "kind": "cluster",
                    "name": cache_cluster_data["name"],
                    "uuid": cache_cluster_data["uuid"],
                }
            else:
                cdict = AhvCluster(name).compile()
                return {
                    "kind": "cluster",
                    "name": cdict["name"],
                    "uuid": cdict["uuid"],
                }

    class Vpc:
        def __new__(cls, name=None, account_name=None, **kwargs):

            kwargs["__ref_cls__"] = cls
            kwargs["account_name"] = account_name
            kwargs["name"] = name
            return _calm_ref(**kwargs)

        def compile(cls, name=None, **kwargs):

            account_name = kwargs.get("account_name", "")
            if account_name:

                cache_acc_data = Cache.get_entity_data(
                    CACHE.ENTITY.ACCOUNT, account_name
                )
                if not cache_acc_data:
                    LOG.error(
                        "Failed to find account with name: {}".format(account_name)
                    )
                    sys.exit("Account name={} not found.".format(account_name))

                # We found the account
                cache_vpc_data = Cache.get_entity_data(
                    CACHE.ENTITY.AHV_VPC, name, account_uuid=cache_acc_data["uuid"]
                )
                if not cache_vpc_data:
                    LOG.error(
                        "Failed to find vpc with name: {}, account: {}".format(
                            name, account_name
                        )
                    )
                    sys.exit("VPC name={} not found".format(name))
                return {
                    "kind": "vpc",
                    "name": cache_vpc_data["name"],
                    "uuid": cache_vpc_data["uuid"],
                }
            else:
                cdict = AhvVpc(name).compile()

                return {
                    "kind": "vpc",
                    "name": cdict["name"],
                    "uuid": cdict["uuid"],
                }

    class Resource_Type:
        def __new__(cls, name, **kwargs):
            kwargs["__ref_cls__"] = cls
            kwargs["name"] = name
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):

            client = get_api_client()

            if name:
                params = {"filter": "name=={}".format(name), "length": 250}
                res, err = client.resource_types.list(params)
                if err:
                    LOG.error(err)
                    sys.exit(-1)

                res = res.json()
                if res["metadata"]["total_matches"] == 0:
                    LOG.error("No vm with name '{}' found".format(name))
                    sys.exit(-1)

                elif res["metadata"]["total_matches"] > 1:
                    LOG.error(
                        "Multiple resource type with same name found. "
                        "Please provide resource type uuid"
                    )
                    sys.exit(-1)

                resource_type_uuid = res["entities"][0]["status"]["uuid"]
            else:
                LOG.error(
                    "Resource type name not passed, " "pls pass resource type name"
                )
                sys.exit(-1)

            resource_type_ref = {
                "uuid": resource_type_uuid,
                "name": name,
                "kind": "resource_type",
            }

            return resource_type_ref

    class Tunnel:
        def __new__(cls, name, **kwargs):
            kwargs["__ref_cls__"] = cls
            kwargs["name"] = name
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):
            tunnel_uuid = ""
            if name:
                cache_vpc_data = Cache.get_entity_data(
                    CACHE.ENTITY.AHV_VPC, None, tunnel_name=name
                )
                if not cache_vpc_data:
                    LOG.error("Failed to find Tunnel with name: {}".format(name))
                    sys.exit("Tunnel name={} not found".format(name))
                tunnel_uuid = cache_vpc_data.get("tunnel_uuid")
                LOG.debug("Tunnel UUID: {}".format(tunnel_uuid))
            else:
                LOG.error("Tunnel name not passed, " "pls pass Tunnel name")
                sys.exit(-1)

            tunnel_ref = {
                "uuid": tunnel_uuid,
                "name": name,
                "kind": "tunnel",
            }

            return tunnel_ref
