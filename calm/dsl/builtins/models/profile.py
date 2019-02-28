from .entity import EntityType, Entity
from .validator import PropertyValidator


# Profile

class ProfileType(EntityType):
    __schema_name__ = "Profile"


class ProfileValidator(PropertyValidator, openapi_type="profile"):
    __default__ = None
    __kind__ = ProfileType


def profile(**kwargs):
    name = getattr(ProfileType, "__schema_name__")
    bases = (Entity, )
    return ProfileType(name, bases, kwargs)


def profile_type(cls):
    name = cls.__name__
    bases = (Entity, )
    kwargs = dict(cls.__dict__) # class dict is mappingproxy
    return ProfileType(name, bases, kwargs)


Profile = profile()
