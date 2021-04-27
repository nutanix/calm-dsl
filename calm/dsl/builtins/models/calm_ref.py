import sys
import uuid

from .entity import Entity, EntityType
from .validator import PropertyValidator
from .helper import common as common_helper

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
            account_uuid = kwargs.get("account_uuid")

            try:
                provider_obj = cls.__parent__
                subnet_account = provider_obj.account_reference.get_dict()
                account_uuid = subnet_account.get("uuid")

            except Exception:
                pass

            subnet_cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.AHV_SUBNET,
                name=name,
                cluster=cluster,
                account_uuid=account_uuid,
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
            environment_cache_data = Cache.get_entity_data(
                entity_type="environment", name=name, project=project_name
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
