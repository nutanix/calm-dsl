from .entity import EntityType, Entity
from .validator import PropertyValidator


# Metadata


class MetadataType(EntityType):
    __schema_name__ = "Metadata"
    __openapi_type__ = "app_metadata"

    def compile(cls):
        cdict = super().compile()
        if not cdict.get("owner_reference", {}):
            cdict.pop("owner_reference", None)
        if not cdict.get("categories", {}):
            cdict.pop("categories", None)
        if not cdict.get("project_reference", {}):
            cdict.pop("project_reference", None)
        return cdict


class MetadataValidator(PropertyValidator, openapi_type="app_metadata"):
    __default__ = None
    __kind__ = MetadataType


def _metadata(**kwargs):
    bases = (Entity,)
    return MetadataType(None, bases, kwargs)


Metadata = _metadata()
