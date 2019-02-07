from .entity import EntityType, Entity
from .validator import PropertyValidator
from .base import SCHEMAS


# Profile

class ProfileType(EntityType):
    __schema__ = SCHEMAS["Profile"]


class Profile(Entity, metaclass=ProfileType):
    pass


class ProfileValidator(PropertyValidator, openapi_type="profile"):

    __default__ = None
    __kind__ = ProfileType


class ProfileListValidator(ProfileValidator, openapi_type="profiles"):

    __default__ = []
