from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY, ACCOUNT
from .utils import is_compile_secrets
from distutils.version import LooseVersion as LV
from calm.dsl.store.version import Version

LOG = get_logging_handle(__name__)

# AHV Account


class AhvAccountType(EntityType):
    __schema_name__ = "AhvAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.AHV

    def compile(cls):
        cdict = super().compile()

        # Adding this so that empty username is not in compiled account
        username = cdict.pop("username", "")
        if username:
            cdict["username"] = username

        # Handle password for basic_auth
        pswd = cdict.pop("password", "")
        if pswd:
            cdict["password"] = {
                "value": pswd if is_compile_secrets() else "",
                "attrs": {"is_secret_modified": True},
            }

        # Handle service_account for service_account auth
        service_account = cdict.pop("service_account", "")
        if service_account:
            cdict["service_account"] = {
                "value": service_account if is_compile_secrets() else "",
                "attrs": {"is_secret_modified": True},
            }

        # Set cred type if Calm version is >= 4.3.0
        calm_version = Version.get_version("Calm")
        if LV(calm_version) >= LV(ACCOUNT.SERVICE_ACCOUNT.FEATURE_MIN_VERSION):
            if service_account:
                cdict["cred_type"] = ACCOUNT.CRED_TYPE.SERVICE_ACCOUNT
            else:
                cdict["cred_type"] = ACCOUNT.CRED_TYPE.BASIC_AUTH

        return cdict


class AhvAccountValidator(PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.AHV):
    __default__ = None
    __kind__ = AhvAccountType


def ahv_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return AhvAccountType(name, bases, kwargs)


AhvAccountData = ahv_account()
