from .entity import EntityType, Entity
from .validator import PropertyValidator


# VMRef


class VMRefType(EntityType):
    __schema_name__ = "VMRef"
    __openapi_type__ = "vm_ref"


class VMRefValidator(PropertyValidator, openapi_type="vm_ref"):
    __default__ = None
    __kind__ = VMRefType


def _vm_ref(**kwargs):
    name = kwargs.get("name", None)
    uuid = kwargs.get("uuid", None)
    kwargs["kind"] = "vm"
    if not uuid:
        raise ValueError("UUID is required property")
    bases = (Entity,)
    return VMRefType(name, bases, kwargs)


VM = _vm_ref
