from .entity import EntityType, Entity
from .validator import PropertyValidator


class ProviderTestAccountType(EntityType):
    __schema_name__ = "ProviderTestAccount"
    __openapi_type__ = "provider_test_account"

    def compile(cls):
        cdict = super().compile()
        cdict["data"] = {"variable_list": cdict.pop("variable_list", [])}
        if not cdict.get("tunnel_reference", None):
            cdict.pop("tunnel_reference", None)

        return cdict

    @classmethod
    def pre_decompile(mcls, cdict, context, prefix=""):
        """Hook to modify cdict before decompile"""

        cdict["variable_list"] = cdict.get("data", {}).get("variable_list", [])
        return super(ProviderTestAccountType, mcls).pre_decompile(
            cdict, context, prefix=prefix
        )


class ProviderTestAccountValidator(
    PropertyValidator, openapi_type="provider_test_account"
):
    __default__ = None
    __kind__ = ProviderTestAccountType


def provider_test_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return ProviderTestAccountType(name, bases, kwargs)


ProviderTestAccount = provider_test_account
