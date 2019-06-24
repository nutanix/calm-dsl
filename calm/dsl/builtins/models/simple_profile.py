from .entity import EntityType, Entity
from .validator import PropertyValidator


# Simple Profile


class SimpleProfileType(EntityType):
    __schema_name__ = "SimpleProfile"
    __openapi_type__ = "app_simple_profile"
    __has_dag_target__ = False

    def get_task_target(cls):
        return


class SimpleProfileValidator(PropertyValidator, openapi_type="app_simple_profile"):
    __default__ = None
    __kind__ = SimpleProfileType


def simple_profile(**kwargs):
    name = getattr(SimpleProfileType, "__schema_name__")
    bases = (Entity,)
    return SimpleProfileType(name, bases, kwargs)


SimpleProfile = simple_profile()
