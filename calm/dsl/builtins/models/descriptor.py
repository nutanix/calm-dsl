from .entity import EntityType, Entity
from .validator import PropertyValidator


class DescriptorType(EntityType):
    __schema_name__ = "Descriptor"
    __openapi_type__ = "app_descriptor"


class DescriptorValidator(PropertyValidator, openapi_type="app_descriptor"):
    __default__ = None
    __kind__ = DescriptorType


def _descriptor(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return DescriptorType(name, bases, kwargs)


Descriptor = _descriptor()
