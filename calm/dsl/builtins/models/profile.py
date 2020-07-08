from .entity import EntityType, Entity
from .validator import PropertyValidator


# Profile


class ProfileType(EntityType):
    __schema_name__ = "Profile"
    __openapi_type__ = "app_profile"
    __has_dag_target__ = False

    def get_task_target(cls):
        return

    def compile(cls):
        cdict = super().compile()
        # description attribute in profile gives bp launch error: https://jira.nutanix.com/browse/CALM-19380
        cdict.pop("description", None)
        return cdict


class ProfileValidator(PropertyValidator, openapi_type="app_profile"):
    __default__ = None
    __kind__ = ProfileType


def profile(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return ProfileType(name, bases, kwargs)


Profile = profile()
