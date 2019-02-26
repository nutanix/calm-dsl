from .entity import EntityType, Entity
from .validator import PropertyValidator


# Profile

class ProfileType(EntityType):
    __schema_name__ = "Profile"


class Profile(Entity, metaclass=ProfileType):
    pass


def profile(**kwargs):
    return ProfileType("", (Entity, ), kwargs)


class ProfileValidator(PropertyValidator, openapi_type="profile"):

    __default__ = None
    __kind__ = ProfileType
