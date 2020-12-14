import sys
from .entity import EntityType, Entity
from .validator import PropertyValidator, get_property_validators
from calm.dsl.log import get_logging_handle


LOG = get_logging_handle(__name__)


# AccountData


class AccountDataType(EntityType):
    __schema_name__ = "AccountData"
    __openapi_type__ = "account_data"

    provider_data_accounts = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "__provider_type__"):
            raise TypeError("Provider account data does not have a __provider_type__")

        provider_type = getattr(cls, "__provider_type__")
        cls.provider_data_accounts[provider_type] = cls

    @classmethod
    def get_provider_data_accounts(cls):
        """ returns provider_data_accounts map"""
        return cls.provider_data_accounts


class AccountDataValidator(PropertyValidator, openapi_type="account_data"):
    __default__ = None
    __kind__ = AccountDataType


# AccountResource


class AccountResourceType(EntityType):
    __schema_name__ = "AccountResource"
    __openapi_type__ = "account_resource"

    def compile(cls):

        # Validating correct provider account data type provided
        provider_type = cls.type
        provider_data_account = AccountDataType.get_provider_data_accounts().get(
            provider_type
        )

        if not provider_data_account:
            LOG.error("Provider Account '{}' not registered".format(provider_type))
            sys.exit(-1)

        pva_openapi_type = getattr(provider_data_account, "__openapi_type__")
        if not pva_openapi_type:
            LOG.error("__openapi_type__ not defined for provider data account")
            sys.exit(1 - 1)

        ValidatorType = get_property_validators().get(pva_openapi_type)
        ValidatorType.validate(cls.data, False)

        return super().compile()


class AccountResourceValidator(PropertyValidator, openapi_type="account_resource"):
    __default__ = None
    __kind__ = AccountResourceType


def account_resource(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AccountResourceType(name, bases, kwargs)


AccountResource = account_resource()


# Account


class AccountType(EntityType):
    __schema_name__ = "Account"
    __openapi_type__ = "account"


class AccountValidator(PropertyValidator, openapi_type="account"):
    __default__ = None
    __kind__ = AccountType


def account(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AccountType(name, bases, kwargs)


Account = account()
