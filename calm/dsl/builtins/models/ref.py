from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE


# Ref


class RefType(EntityType):
    __schema_name__ = "Ref"
    __openapi_type__ = "app_ref"

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        cdict = super().pre_decompile(cdict, context, prefix=prefix)

        # Class name for ref objects should always be taken randomly
        cdict["__name__"] = None

        return cdict

    def get_user_attrs(cls):
        """returns user attrs for ref class"""

        attrs = super().get_user_attrs()
        attrs.pop("__self__", None)  # Not a user attr for reference object

        return attrs


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
