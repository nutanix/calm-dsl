import sys
from .entity import EntityType, Entity
from .validator import PropertyValidator, get_property_validators
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# AccountData


class AccountSpecType(EntityType):
    __schema_name__ = "AccountSpec"
    __openapi_type__ = "account_spec"

    subclasses = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "__provider_type__"):
            raise TypeError("Provider account data does not have a __provider_type__")

        provider_type = getattr(cls, "__provider_type__")

        # Case for multiple k8s accounts
        if not provider_type:
            return

        cls.subclasses[provider_type] = cls


class AccountSpecValidator(PropertyValidator, openapi_type="account_spec"):
    __default__ = None
    __kind__ = AccountSpecType


# Account


class AccountType(EntityType):
    __schema_name__ = "Account"
    __openapi_type__ = "account"

    def compile(cls):

        # Validating correct provider account data type provided
        provider_type = cls.provider_type
        provider_spec_account = AccountSpecType.subclasses.get(provider_type)

        if not provider_spec_account:
            LOG.error("Provider Account '{}' not registered".format(provider_type))
            sys.exit(-1)

        pva_openapi_type = getattr(provider_spec_account, "__openapi_type__")
        if not pva_openapi_type:
            LOG.error("__openapi_type__ not defined for provider spec account")
            sys.exit(-1)

        ValidatorType = get_property_validators().get(pva_openapi_type)
        ValidatorType.validate(cls.spec, False)

        cdict = super().compile()

        if cdict["type"] in ["kubernetes_karbon", "kubernetes_vanilla"]:
            cdict["type"] = "kubernetes"

        return cdict


class AccountValidator(PropertyValidator, openapi_type="account"):
    __default__ = None
    __kind__ = AccountType


def account(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AccountType(name, bases, kwargs)


Account = account()
