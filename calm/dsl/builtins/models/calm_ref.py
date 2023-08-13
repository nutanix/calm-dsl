import sys
import uuid
import json

from calm.dsl.db.table_config import AhvSubnetsCache
from calm.dsl.builtins.models.constants import NutanixDB as NutanixDBConst

from .entity import Entity, EntityType, EntityDict
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
class CalmRefDict(EntityDict):
    """Meta dict class for calm_ref_type"""

    @classmethod
    def _validate_attr(cls, vdict, name, value):
        """attrs validator for calm ref type class. Always true, as CalmRefType is base class for every ref, any attribute can be added to it."""
        return value


class CalmRefType(EntityType):
    """Metaclass for calm references"""

    __schema_name__ = "CalmRef"
    __openapi_type__ = "app_calm_ref"
    __prepare_dict__ = CalmRefDict

    def compile(cls):
        """compiles the calm_ref object"""

        ref_cls = getattr(cls, "__ref_cls__")
        user_attrs = cls.get_user_attrs()
        return ref_cls.compile(cls, **user_attrs)

    def __getitem__(cls, key):
        """return the vale in compiled class payload"""
        data = cls.compile()
        return data[key]

    @classmethod
    def decompile(mcls, cdict, context=[], prefix=""):
        """return the decompiled class"""

        cdict = mcls.pre_decompile(cdict, context=context, prefix=prefix)
        cls_mapping = Ref.get_cls_kind_mapping()
        ref_cls_kind = CACHE.API_ENTITY_KIND_MAP.get(cdict["kind"], cdict["kind"])

        entity_cls = cls_mapping.get(ref_cls_kind, None)
        if entity_cls and hasattr(entity_cls, "decompile"):
            return entity_cls.decompile(cdict)

        LOG.warning(
            "Ref not implemented for {}. Approaching name based entry in cache".format(
                ref_cls_kind
            )
        )
        return super().decompile(cdict, context, prefix)

    def get_ref_cls(cls):
        """return the ref cls of the calm_ref"""
        return getattr(cls, "__ref_cls__")


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

    @classmethod
    def get_cls_kind_mapping(cls):
        """return class kind mapping"""

        cls_mapping = dict()
        for _, rcls in cls.__dict__.items():
            try:
                rcls_kind = rcls.__ref_kind__
                cls_mapping[rcls_kind] = rcls
            except Exception:
                pass

        return cls_mapping

    class Subnet:
        __ref_kind__ = CACHE.ENTITY.AHV_SUBNET

        def __new__(cls, **kwargs):
            kwargs["__ref_cls__"] = cls
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):

            cluster = kwargs.get("cluster")
            vpc = kwargs.get("vpc")
            account_uuid = kwargs.get("account_uuid")
            if not account_uuid:
                try:
                    provider_obj = cls.__parent__
                    subnet_account = provider_obj.account_reference.get_dict()
                    account_uuid = subnet_account.get("uuid")

                except Exception:
                    pass

            LOG.debug("Searching for subnet with name: {}".format(name))
            subnet_cache_data = None
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

        @classmethod
        def decompile(cls, cdict):
            """return decompile class"""

            if cdict.get("uuid"):
                cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.AHV_SUBNET, uuid=cdict["uuid"]
                )

                if not cache_data:
                    LOG.error(
                        "Entity with type {} and uuid {} not found in cache. Please update cache".format(
                            CACHE.ENTITY.AHV_SUBNET, cdict["uuid"]
                        )
                    )
                    sys.exit(
                        "Invalid {} entity (uuid='')".format(
                            CACHE.ENTITY.AHV_SUBNET, cdict["uuid"]
                        )
                    )

                if cache_data.get("cluster_name"):
                    return cls.__new__(
                        cls,
                        name=cache_data["name"],
                        cluster=cache_data["cluster_name"],
                        account_uuid=cache_data["account_uuid"],
                    )

                elif cache_data.get("vpc_name"):
                    return cls.__new__(
                        cls,
                        name=cache_data["name"],
                        vpc=cache_data["vpc_name"],
                        account_uuid=cache_data["account_uuid"],
                    )

                return cls.__new__(
                    cls,
                    name=cache_data["name"],
                    account_uuid=cache_data["account_uuid"],
                )

            elif cdict.get("name"):
                return cls.__new__(cls, name=cdict["name"])

            LOG.error("Invalid reference data".format(json.dumps(cdict)))
            sys.exit("Invalid reference data".format(json.dumps(cdict)))

    class User:
        __ref_kind__ = CACHE.ENTITY.USER

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
        __ref_kind__ = CACHE.ENTITY.USER_GROUP

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
        __ref_kind__ = CACHE.ENTITY.ACCOUNT

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

        @classmethod
        def decompile(cls, cdict):
            """return decompile class"""

            if cdict.get("uuid"):
                cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.ACCOUNT, uuid=cdict["uuid"]
                )

                if not cache_data:
                    LOG.error(
                        "Entity with type {} and uuid {} not found in cache. Please update cache".format(
                            CACHE.ENTITY.ACCOUNT, cdict["uuid"]
                        )
                    )
                    sys.exit(
                        "Invalid {} entity (uuid='')".format(
                            CACHE.ENTITY.ACCOUNT, cdict["uuid"]
                        )
                    )

                return cls.__new__(cls, name=cache_data["name"])

            elif cdict.get("name"):
                return cls.__new__(cls, name=cdict["name"])

            LOG.error("Invalid reference data".format(json.dumps(cdict)))
            sys.exit("Invalid reference data".format(json.dumps(cdict)))

    class Role:
        __ref_kind__ = CACHE.ENTITY.ROLE

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
        __ref_kind__ = CACHE.ENTITY.PROJECT

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
        __ref_kind__ = CACHE.ENTITY.ENVIRONMENT

        def __new__(cls, **kwargs):

            kwargs["__ref_cls__"] = cls
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):
            """cls = CalmRef object"""

            project_name = kwargs.get("project_name")
            if not project_name:
                project_cache_data = common_helper.get_cur_context_project()
            else:
                project_cache_data = Cache.get_entity_data(
                    entity_type=CACHE.ENTITY.PROJECT, name=project_name
                )

            project_name = project_cache_data.get("name")
            project_uuid = project_cache_data.get("uuid")
            environment_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.ENVIRONMENT,
                name=name,
                project_uuid=project_uuid,
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

        @classmethod
        def decompile(cls, cdict):
            """return decompile class"""

            if cdict.get("uuid"):
                cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.ENVIRONMENT, uuid=cdict["uuid"]
                )

                if not cache_data:
                    LOG.error(
                        "Entity with type {} and uuid {} not found in cache. Please update cache".format(
                            CACHE.ENTITY.ENVIRONMENT, cdict["uuid"]
                        )
                    )
                    sys.exit(
                        "Invalid {} entity (uuid='')".format(
                            CACHE.ENTITY.ENVIRONMENT, cdict["uuid"]
                        )
                    )

                project_uuid = cache_data["project_uuid"]
                project_cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.PROJECT, uuid=project_uuid
                )

                return cls.__new__(
                    cls,
                    name=cache_data["name"],
                    project_name=project_cache_data["name"],
                )

            elif cdict.get("name"):
                return cls.__new__(cls, name=cdict["name"])

            LOG.error("Invalid reference data".format(json.dumps(cdict)))
            sys.exit("Invalid reference data".format(json.dumps(cdict)))

    class ResourceTypeAction:
        def __new__(cls, name, **kwargs):
            kwargs["__ref_cls__"] = cls
            rt_name = kwargs.get("resource_type_name", "")
            provider_name = kwargs.get("provider_name", "")
            if not provider_name:
                LOG.info("Provider name not passed, Using resource_type name for same")
                provider_name = rt_name

            if rt_name:
                res = common_helper.get_resource_type(rt_name, provider_name)
                resource_type_action_list = res["action_list"]
                resource_type_action_uuid = ""
                for resource_type_action in resource_type_action_list:
                    if resource_type_action["name"] == name:
                        resource_type_action_uuid = resource_type_action["uuid"]
                if resource_type_action_uuid == "":
                    LOG.error(
                        "No resource_type_action with name '{}' found".format(name)
                    )
                    sys.exit(-1)
                return {
                    "kind": "app_action",
                    "name": name,
                    "uuid": resource_type_action_uuid,
                }
            else:
                LOG.error(
                    "Resource type name not passed, please pass resource type name"
                )
                sys.exit(-1)

    class DirectoryService:
        __ref_kind__ = CACHE.ENTITY.DIRECTORY_SERVICE

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

    # VM ref do not interact with local cache
    class Vm:
        __ref_kind__ = "VM"

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

    class PolicyEvent:
        __ref_kind__ = CACHE.ENTITY.POLICY_EVENT

        def __new__(cls, name, **kwargs):

            ds_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.POLICY_EVENT, name=name
            )
            if not ds_cache_data:
                LOG.error(
                    "Policy Event {} not found. Please run: calm update cache".format(
                        name
                    )
                )
                if not name:
                    sys.exit("Policy event name not provided")
                sys.exit("Policy Event name={} not found".format(name))
            return {
                "kind": "policy_event",
                "name": name,
                "uuid": ds_cache_data["uuid"],
            }

    class PolicyActionType:
        __ref_kind__ = CACHE.ENTITY.POLICY_ACTION_TYPE

        def __new__(cls, name, **kwargs):

            ds_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.POLICY_ACTION_TYPE, name=name
            )
            if not ds_cache_data:
                LOG.error(
                    "Policy action type {} not found. Please run: calm update cache".format(
                        name
                    )
                )
                sys.exit("Policy action type name={} not found.".format(name))
            return {
                "kind": "policy_action_type",
                "name": name,
                "uuid": ds_cache_data["uuid"],
            }

    # RecoveryPoint ref do not interact with local cache
    class RecoveryPoint:
        __ref_kind__ = "vm_recovery_point"

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
        __ref_kind__ = CACHE.ENTITY.AHV_CLUSTER

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

        @classmethod
        def decompile(cls, cdict):
            """return decompile class"""

            if cdict.get("uuid"):
                cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.AHV_CLUSTER, uuid=cdict["uuid"]
                )

                if not cache_data:
                    LOG.error(
                        "Entity with type {} and uuid {} not found in cache. Please update cache".format(
                            CACHE.ENTITY.AHV_CLUSTER, cdict["uuid"]
                        )
                    )
                    sys.exit(
                        "Invalid {} entity (uuid='')".format(
                            CACHE.ENTITY.AHV_CLUSTER, cdict["uuid"]
                        )
                    )

                # TODO use foreign keys
                account_cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.ACCOUNT, uuid=cache_data["account_uuid"]
                )
                return cls.__new__(
                    cls,
                    name=cache_data["name"],
                    account_name=account_cache_data["name"],
                )

            elif cdict.get("name"):
                return cls.__new__(cls, name=cdict["name"])

            LOG.error("Invalid reference data".format(json.dumps(cdict)))
            sys.exit("Invalid reference data".format(json.dumps(cdict)))

    class Vpc:
        __ref_kind__ = CACHE.ENTITY.AHV_VPC

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
        __ref_kind__ = CACHE.ENTITY.RESOURCE_TYPE

        def __new__(cls, name, **kwargs):
            kwargs["__ref_cls__"] = cls
            kwargs["name"] = name
            return _calm_ref(**kwargs)

        def compile(cls, name, **kwargs):

            provider_name = kwargs.get("provider_name", "")
            if not provider_name:
                LOG.debug("Provider name not passed, Using resource_type name for same")
                provider_name = name

            if name:
                res = common_helper.get_resource_type(name, provider_name)
                resource_type_uuid = res["uuid"]
            else:
                LOG.error(
                    "Resource type name not passed, please pass resource type name"
                )
                sys.exit(-1)

            resource_type_ref = {
                "uuid": resource_type_uuid,
                "name": name,
                "kind": "resource_type",
            }

            return resource_type_ref

        @classmethod
        def decompile(cls, cdict):
            """return decompile class"""

            if cdict.get("uuid"):
                cache_data = Cache.get_entity_data_using_uuid(
                    entity_type=CACHE.ENTITY.RESOURCE_TYPE, uuid=cdict["uuid"]
                )

                if not cache_data:
                    LOG.error(
                        "Entity with type {} and uuid {} not found in cache. Please update cache".format(
                            CACHE.ENTITY.RESOURCE_TYPE, cdict["uuid"]
                        )
                    )
                    sys.exit(
                        "Invalid {} entity (uuid='')".format(
                            CACHE.ENTITY.RESOURCE_TYPE, cdict["uuid"]
                        )
                    )

                return cls.__new__(cls, name=cache_data["name"])

            elif cdict.get("name"):
                return cls.__new__(cls, name=cdict["name"])

            LOG.error("Invalid reference data".format(json.dumps(cdict)))
            sys.exit("Invalid reference data".format(json.dumps(cdict)))

    class Tunnel:
        __ref_kind__ = "tunnel"

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
                LOG.error("Tunnel name not passed, please pass Tunnel name")
                sys.exit(-1)

            tunnel_ref = {
                "uuid": tunnel_uuid,
                "name": name,
                "kind": "tunnel",
            }

            return tunnel_ref

    class NutanixDB:
        """Base Calm Ref Class for Nutanix DB entitites (Not Callable)"""

        def __new__(cls, *args, **kwargs):
            raise TypeError("'{}' is not callable".format(cls.__name__))

        class Database:
            """Base Calm Ref Class for Nutanix DB Database entities"""

            def __new__(cls, name, **kwargs):
                kwargs["__ref_cls__"] = cls
                kwargs["name"] = name
                return _calm_ref(**kwargs)

            def compile(cls, name, **kwargs):
                """
                defines compile for NDB Database Ref
                Args:
                    name(str): name of the database
                    kwargs: This includes account_name for NDB account
                Return:
                    (dict): corresponding profile dictionary
                """
                account_name = kwargs.get("account_name", "")
                if not account_name:
                    LOG.error(
                        "account_name is required NutanixDB Database compile, please pass account_name"
                    )
                    sys.exit(-1)

                _type = kwargs.get("type", "")
                if not _type:
                    LOG.error(
                        "type is required for NutanixDB Database compile, please pass type"
                    )
                    sys.exit(-1)

                cache_database_data = Cache.get_entity_data(
                    entity_type=CACHE.NDB
                    + CACHE.KEY_SEPARATOR
                    + CACHE.NDB_ENTITY.DATABASE,
                    name=name,
                    account_name=account_name,
                    type=_type,
                )

                if not cache_database_data:
                    LOG.error("No NDB Database with name '{}' found".format(name))
                    sys.exit(-1)

                return cache_database_data

        class Profile:
            """Base Calm Ref Class for Nutanix DB profile entitites (Not Callable)"""

            def __new__(cls, *args, **kwargs):
                raise TypeError("'{}' is not callable".format(cls.__name__))

            class Software:
                """Calm Ref Class for Nutanix DB software profile entity"""

                def __new__(cls, name, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB Software Profile Ref
                    Args:
                        name(str): name of the software profile
                        kwargs: This includes account_name for NDB account and engine of profile if any
                    Return:
                        (dict): corresponding profile dictionary
                    """
                    account_name = kwargs.pop("account_name", "")
                    return common_helper.get_ndb_profile(
                        name, NutanixDBConst.PROFILE.SOFTWARE, account_name, **kwargs
                    )

            class Software_Version:
                """Calm Ref Class for Nutanix DB software profile version entity"""

                def __new__(cls, name=None, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    return _calm_ref(**kwargs)

                def compile(cls, name=None, **kwargs):
                    """
                    defines compile for NDB Software Profile Version Ref
                    Args:
                        name(str): name of the software profile
                        kwargs: This includes account_name for NDB account, software profile name, and engine of profile if any
                    Return:
                        (dict): corresponding profile dictionary
                    """
                    software_name = kwargs.get("software_name", "")
                    if not software_name:
                        LOG.error(
                            "Software name is required for Software Version Profile compile, please pass Software name"
                        )
                        sys.exit(-1)

                    account_name = kwargs.pop("account_name", "")
                    software_profile = common_helper.get_ndb_profile(
                        software_name,
                        NutanixDBConst.PROFILE.SOFTWARE,
                        account_name,
                        **kwargs,
                    )
                    if name:
                        for version in software_profile["platform_data"]["versions"]:
                            if version["name"] == name:
                                return version["id"]

                        LOG.error(
                            "No NDB {} with name '{}' found for the software with name {}".format(
                                NutanixDBConst.PROFILE.SOFTWARE_PROFILE_VERSION,
                                name,
                                software_name,
                            )
                        )
                        sys.exit(-1)

                    return software_profile["latest_version_id"]

            class Network:
                """Calm Ref Class for Nutanix DB network profile entity"""

                def __new__(cls, name, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB Network Ref
                    Args:
                        name(str): name of the software profile
                        kwargs: This includes account_name for NDB account and engine of profile if any
                    Return:
                        (dict): corresponding profile dictionary
                    """
                    account_name = kwargs.pop("account_name", "")
                    return common_helper.get_ndb_profile(
                        name, NutanixDBConst.PROFILE.NETWORK, account_name, **kwargs
                    )

            class Compute:
                """Calm Ref Class for Nutanix DB compute profile entity"""

                def __new__(cls, name, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB Compute Ref
                    Args:
                        name(str): name of the software profile
                        kwargs: This includes account_name for NDB account and engine of profile if any
                    Return:
                        (dict): corresponding profile dictionary
                    """
                    account_name = kwargs.pop("account_name", "")
                    return common_helper.get_ndb_profile(
                        name, NutanixDBConst.PROFILE.COMPUTE, account_name, **kwargs
                    )

            class Database_Parameter:
                """Calm Ref Class for Nutanix DB database parameter profile entity"""

                def __new__(cls, name, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB Database_Paramter Ref
                    Args:
                        name(str): name of the software profile
                        kwargs: This includes account_name for NDB account and engine of profile if any
                    Return:
                        (dict): corresponding profile dictionary
                    """
                    account_name = kwargs.pop("account_name", "")
                    return common_helper.get_ndb_profile(
                        name,
                        NutanixDBConst.PROFILE.DATABASE_PARAMETER,
                        account_name,
                        **kwargs,
                    )

        class SLA:
            """Calm Ref Class for Nutanix DB sla entity"""

            def __new__(cls, name, **kwargs):
                kwargs["__ref_cls__"] = cls
                kwargs["name"] = name
                return _calm_ref(**kwargs)

            def compile(cls, name, **kwargs):
                """
                defines compile for NDB SLA Ref
                Args:
                    name(str): name of the software profile
                    kwargs: This includes account_name for NDB account
                Return:
                    (dict): corresponding profile dictionary
                """
                account_name = kwargs.get("account_name", "")
                if not account_name:
                    LOG.error(
                        "account_name is required NutanixDB SLA compile, please pass account_name"
                    )
                    sys.exit(-1)

                cache_sla_data = Cache.get_entity_data(
                    entity_type=CACHE.NDB + CACHE.KEY_SEPARATOR + CACHE.NDB_ENTITY.SLA,
                    name=name,
                    account_name=account_name,
                )

                if not cache_sla_data:
                    LOG.error("No NDB SLA with name '{}' found".format(name))
                    sys.exit(-1)

                return cache_sla_data

        class Cluster:
            """Calm Ref Class for Nutanix DB cluster entity"""

            def __new__(cls, name, **kwargs):
                kwargs["__ref_cls__"] = cls
                kwargs["name"] = name
                return _calm_ref(**kwargs)

            def compile(cls, name, **kwargs):
                """
                defines compile for NDB cluster Ref
                Args:
                    name(str): name of the software profile
                    kwargs: This includes account_name for NDB account
                Return:
                    (dict): corresponding profile dictionary
                """
                account_name = kwargs.get("account_name", "")
                if not account_name:
                    LOG.error(
                        "account_name is required NutanixDB Cluster compile, please pass account_name"
                    )
                    sys.exit(-1)

                cache_cluster_data = Cache.get_entity_data(
                    entity_type=CACHE.NDB
                    + CACHE.KEY_SEPARATOR
                    + CACHE.NDB_ENTITY.CLUSTER,
                    name=name,
                    account_name=account_name,
                )

                if not cache_cluster_data:
                    LOG.error("No NDB Cluster with name '{}' found".format(name))
                    sys.exit(-1)

                return cache_cluster_data

        class Snapshot:
            """Calm Ref Class for Nutanix DB snapshot entity"""

            def __new__(cls, name, **kwargs):
                kwargs["__ref_cls__"] = cls
                kwargs["name"] = name
                return _calm_ref(**kwargs)

            def compile(cls, name, **kwargs):
                """
                defines compile for NDB cluster Ref
                Args:
                    name(str): name of the snapshot
                    kwargs: This includes account_name for NDB account and time_machine_id if any
                Return:
                    (dict): corresponding profile dictionary
                """
                account_name = kwargs.get("account_name", "")
                time_machine_id = kwargs.get("time_machine_id", "")
                snapshot_timestamp = kwargs.get("snapshot_timestamp", "")
                if not account_name:
                    LOG.error(
                        "Account Name is required NutanixDB Snapshot compile, please pass Account Name"
                    )
                    sys.exit(
                        "Account Name is required NutanixDB Snapshot compile, please pass Account Name"
                    )

                if not snapshot_timestamp:
                    LOG.error(
                        "snapshot_timestamp is required NutanixDB Snapshot compile, please pass snapshot_timestamp"
                    )
                    sys.exit(
                        "snapshot_timestamp is required NutanixDB Snapshot compile, please pass snapshot_timestamp"
                    )
                cache_snapshot_data = Cache.get_entity_data(
                    entity_type=CACHE.NDB
                    + CACHE.KEY_SEPARATOR
                    + CACHE.NDB_ENTITY.SNAPSHOT,
                    name=name,
                    account_name=account_name,
                    time_machine_id=time_machine_id,
                    snapshot_timestamp=snapshot_timestamp,
                )

                if not cache_snapshot_data:
                    LOG.error(
                        "No NDB snapshot with name '{}' and timeStamp '{} found, Note: Timestamp is in UTC".format(
                            name, snapshot_timestamp
                        )
                    )
                    sys.exit(
                        "No NDB snapshot with name '{}' and timeStamp '{} found, Note: Timestamp is in UTC".format(
                            name, snapshot_timestamp
                        )
                    )

                return cache_snapshot_data

        class TimeMachine:
            """Calm Ref Class for Nutanix DB TimeMachine entity"""

            def __new__(cls, name, **kwargs):
                kwargs["__ref_cls__"] = cls
                kwargs["name"] = name
                return _calm_ref(**kwargs)

            def compile(cls, name, **kwargs):
                """
                Defines compile for NDB TimeMachine Ref

                Args:
                    name:   (str) Time Machine Name
                    kwargs: (Dict) Includes account_name for NDB account
                Return:
                    (Dict): corresponding Time Machine info
                """
                client = get_api_client()
                account_name = kwargs.get("account_name", "")
                _type = kwargs.get("type", "")
                if not account_name:
                    LOG.error("Account Name is required NutanixDB TimeMachine compile")
                    sys.exit("Account Name is required NutanixDB TimeMachine compile")

                cache_time_machine_data = Cache.get_entity_data(
                    entity_type=CACHE.NDB
                    + CACHE.KEY_SEPARATOR
                    + CACHE.NDB_ENTITY.TIME_MACHINE,
                    name=name,
                    account_name=account_name,
                    type=_type,
                )

                if not cache_time_machine_data:
                    LOG.error("No NDB Time Machine with name '{}' found".format(name))
                    sys.exit("No NDB Time Machine with name '{}' found".format(name))

                return cache_time_machine_data

        class Tag:
            """Base Calm Ref Class for Nutanix DB Tag entitites (Not Callable)"""

            def __new__(cls, *args, **kwargs):
                raise TypeError("'{}' is not callable".format(cls.__name__))

            class Database:
                """Calm Ref Class for Nutanix DB Database tag entity"""

                def __new__(cls, name, value, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    kwargs["value"] = value
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB Database Tag Ref
                    Args:
                        name(str): name of the Tag
                        kwargs: This includes account_name for NDB account and value of tag
                    Return:
                        (dict): corresponding tag dictionary
                    """
                    account_name = kwargs.get("account_name", "")
                    if not account_name:
                        LOG.error(
                            "account_name is required NutanixDB Database Tag compile, please pass account_name"
                        )
                        sys.exit(
                            "account_name is required NutanixDB Database Tag compile, please pass account_name"
                        )

                    tag = common_helper.get_ndb_tag(name, account_name, "DATABASE")
                    tag_dict = {
                        "tag_id": tag["uuid"],
                        "tag_name": name,
                        "value": kwargs.get("value", ""),
                    }
                    return tag_dict

            class TimeMachine:
                """Calm Ref Class for Nutanix DB TIME_MACHINE tag entity"""

                def __new__(cls, name, value, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    kwargs["value"] = value
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB TIME_MACHINE Tag Ref
                    Args:
                        name(str): name of the Tag
                        kwargs: This includes account_name for NDB account and value of tag
                    Return:
                        (dict): corresponding tag dictionary
                    """
                    account_name = kwargs.get("account_name", "")
                    if not account_name:
                        LOG.error(
                            "account_name is required NutanixDB TIME_MACHINE Tag compile, please pass account_name"
                        )
                        sys.exit(
                            "account_name is required NutanixDB TIME_MACHINE Tag compile, please pass account_name"
                        )

                    tag = common_helper.get_ndb_tag(name, account_name, "TIME_MACHINE")
                    tag_dict = {
                        "tag_id": tag["uuid"],
                        "tag_name": name,
                        "value": kwargs.get("value", ""),
                    }
                    return tag_dict

            class Clone:
                """Calm Ref Class for Nutanix DB CLONE tag entity"""

                def __new__(cls, name, value, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    kwargs["value"] = value
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB CLONE Tag Ref
                    Args:
                        name(str): name of the Tag
                        kwargs: This includes account_name for NDB account and value of tag
                    Return:
                        (dict): corresponding tag dictionary
                    """
                    account_name = kwargs.get("account_name", "")
                    if not account_name:
                        LOG.error(
                            "account_name is required NutanixDB CLONE Tag compile, please pass account_name"
                        )
                        sys.exit(
                            "account_name is required NutanixDB CLONE Tag compile, please pass account_name"
                        )

                    tag = common_helper.get_ndb_tag(name, account_name, "CLONE")
                    tag_dict = {
                        "tag_id": tag["uuid"],
                        "tag_name": name,
                        "value": kwargs.get("value", ""),
                    }
                    return tag_dict

            class DatabaseServer:
                """Calm Ref Class for Nutanix DB DATABASE_SERVER tag entity"""

                def __new__(cls, name, value, **kwargs):
                    kwargs["__ref_cls__"] = cls
                    kwargs["name"] = name
                    kwargs["value"] = value
                    return _calm_ref(**kwargs)

                def compile(cls, name, **kwargs):
                    """
                    defines compile for NDB DATABASE_SERVER Tag Ref
                    Args:
                        name(str): name of the Tag
                        kwargs: This includes account_name for NDB account and value of tag
                    Return:
                        (dict): corresponding tag dictionary
                    """
                    account_name = kwargs.get("account_name", "")
                    if not account_name:
                        LOG.error(
                            "account_name is required NutanixDB DATABASE_SERVER Tag compile, please pass account_name"
                        )
                        sys.exit(
                            "account_name is required NutanixDB DATABASE_SERVER Tag compile, please pass account_name"
                        )

                    tag = common_helper.get_ndb_tag(
                        name, account_name, "DATABASE_SERVER"
                    )
                    tag_dict = {
                        "tag_id": tag["uuid"],
                        "tag_name": name,
                        "value": kwargs.get("value", ""),
                    }
                    return tag_dict
