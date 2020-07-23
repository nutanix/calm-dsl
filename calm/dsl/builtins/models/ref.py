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
                    "AHV Subnet {} not found. Please run: calm update cache".format(name)
                )
        
            return {
                "kind": "subnet",
                "name": name,
                "uuid": subnet_cache_data["uuid"]
            }
    
    class User:
        def __new__(cls, name, **kwargs):

            directory = kwargs.get("directory") or ""
            display_name = kwargs.get("display_name") or ""
            user_cache_data = Cache.get_entity_data(
                entity_type="user",
                name=name,
                directory=directory,
                display_name=display_name
            )

            if not user_cache_data:
                raise Exception(
                    "User {} not found. Please run: calm update cache".format(name)
                )
            
            return {
                "kind": "user",
                "name": name,
                "uuid": user_cache_data["uuid"]
            }
    
    class Group:
        def __new__(cls, name, **kwargs):

            directory = kwargs.get("directory") or ""
            display_name = kwargs.get("display_name") or ""
            user_group_cache_data = Cache.get_entity_data(
                entity_type="user_group",
                name=name,
                directory=directory,
                display_name=display_name
            )

            if not user_group_cache_data:
                raise Exception(
                    "User Group {} not found. Please run: calm update cache".format(name)
                )
            
            return {
                "kind": "user",
                "name": name,
                "uuid": user_group_cache_data["uuid"]
            }
