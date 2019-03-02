from .entity import EntityType, Entity
from .validator import PropertyValidator


# Profile

class ProfileType(EntityType):
    __schema_name__ = "Profile"
    __openapi_type__ = "app_profile"


class ProfileValidator(PropertyValidator, openapi_type="app_profile"):
    __default__ = None
    __kind__ = ProfileType


def profile(**kwargs):
    name = getattr(ProfileType, "__schema_name__")
    bases = (Entity, )
    return ProfileType(name, bases, kwargs)


Profile = profile()
