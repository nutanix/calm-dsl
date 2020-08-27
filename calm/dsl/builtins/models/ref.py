from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache


# Ref


class RefType(EntityType):
    __schema_name__ = "Ref"
    __openapi_type__ = "app_ref"


class RefValidator(PropertyValidator, openapi_type="app_ref"):
    __default__ = None
    __kind__ = RefType


def _ref(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return RefType(name, bases, kwargs)


def ref(cls):

    if isinstance(cls, RefType):
        return cls

    return cls.get_ref()


class Ref:
    def __new__(cls, *args, **kwargs):
        raise TypeError("'{}' is not callable".format(cls.__name__))

    class Subnet:
        def __new__(cls, name, **kwargs):
            cluster = kwargs.get("cluster")
            account_uuid = kwargs.get("account_uuid")

            subnet_cache_data = Cache.get_entity_data(
                entity_type="ahv_subnet",
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
                entity_type="user",
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
                entity_type="user_group",
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

            provider_type = kwargs.get("provider_type") or ""
            account_cache_data = Cache.get_entity_data(
                entity_type="account", name=name, provider_type=provider_type
            )

            if not account_cache_data:
                raise Exception(
                    "Account {} not found. Please run: calm update cache".format(name)
                )

            return {"kind": "account", "name": name, "uuid": account_cache_data["uuid"]}

    class Role:
        def __new__(cls, name, **kwargs):

            role_cache_data = Cache.get_entity_data(entity_type="role", name=name)
            if not role_cache_data:
                raise Exception(
                    "Role {} not found. Please run: calm update cache".format(name)
                )
            return {"kind": "role", "name": name, "uuid": role_cache_data["uuid"]}

    class Project:
        def __new__(cls, name, **kwargs):

            project_cache_data = Cache.get_entity_data(entity_type="project", name=name)
            if not project_cache_data:
                raise Exception(
                    "Project {} not found. Please run: calm update cache".format(name)
                )
            return {"kind": "project", "name": name, "uuid": project_cache_data["uuid"]}

    class DirectoryService:
        def __new__(cls, name, **kwargs):

            ds_cache_data = Cache.get_entity_data(
                entity_type="directory_service", name=name
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
