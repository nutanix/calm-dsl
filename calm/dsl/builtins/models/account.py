import sys
from .entity import EntityType, Entity
from .validator import PropertyValidator, get_property_validators
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import PROVIDER_RESOURCE, ACCOUNT_TYPE_MAP


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
        resource_type = getattr(cls, "__resource_type__")

        # Case for multiple k8s accounts
        if not provider_type and resource_type:
            return

        if provider_type not in cls.subclasses:
            cls.subclasses[provider_type] = {}

        cls.subclasses[provider_type][resource_type] = cls


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
        resource_type = cls.resource_type

        _spec_classes = AccountSpecType.subclasses

        if not _spec_classes.get(provider_type):
            LOG.error("Provider '{}' not registered".format(provider_type))
            sys.exit(-1)

        if not resource_type:
            resource_type = PROVIDER_RESOURCE.__default__[provider_type]

        if resource_type not in _spec_classes[provider_type]:
            LOG.error(
                "Resource Type '{}' for Provider '{}' not registered".format(
                    resource_type, provider_type
                )
            )
            sys.exit(-1)

        provider_spec_account = _spec_classes[provider_type][resource_type]

        pva_openapi_type = getattr(provider_spec_account, "__openapi_type__")
        if not pva_openapi_type:
            LOG.error("__openapi_type__ not defined for provider spec account")
            sys.exit(-1)

        ValidatorType = get_property_validators().get(pva_openapi_type)
        ValidatorType.validate(cls.spec, False)

        cdict = super().compile()

        # Add proper calm account
        cdict["type"] = ACCOUNT_TYPE_MAP[provider_type][resource_type]

        cdict.pop("resource_type", None)

        return cdict


class AccountValidator(PropertyValidator, openapi_type="account"):
    __default__ = None
    __kind__ = AccountType


def account(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AccountType(name, bases, kwargs)


Account = account()
