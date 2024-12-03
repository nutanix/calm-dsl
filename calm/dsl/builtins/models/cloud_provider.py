import json
import sys

from calm.dsl.log import get_logging_handle
from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER, ACTION, CREDENTIAL

from .resource_type import ResourceType
from .entity import EntityType, Entity
from .validator import PropertyValidator

LOG = get_logging_handle(__name__)


class CloudProviderType(EntityType):
    __schema_name__ = "CloudProvider"
    __openapi_type__ = "cloud_provider"

    def compile(cls):
        cdict = super().compile()
        if len(cdict.get("auth_schema_list", [])) == 0:
            error = "Auth_schema is required for provider"
            LOG.error(error)
            sys.exit(error)

        if cdict.get("type", PROVIDER.TYPE.CUSTOM) != PROVIDER.TYPE.CUSTOM:
            error = "provider type is not '%s'" % (PROVIDER.TYPE.CUSTOM)
            LOG.error(error)
            sys.exit(error)

        action_list = cdict.get("action_list", [])
        if len(action_list) > 1:
            error = "Atmost one verify action can be added for provider"
            LOG.error(error)
            sys.exit(error)
        elif action_list:
            action = action_list[0]
            if str(action) != PROVIDER.VERIFY_ACTION_NAME:
                error = "Action should be named '%s'" % (PROVIDER.VERIFY_ACTION_NAME)
                LOG.error(error)
                sys.exit(error)

            if action.type != ACTION.TYPE.PROVIDER:
                error = "Provider Action should be of type '%s'" % (
                    ACTION.TYPE.PROVIDER
                )
                LOG.error(error)
                sys.exit(error)

        infra_type = cdict.get("infra_type", None)
        if infra_type is not None and infra_type not in PROVIDER.INFRA_TYPES:
            error = "Infra type should be one of %s" % (
                json.dumps(PROVIDER.INFRA_TYPES)
            )
            LOG.error(error)
            sys.exit(error)

        credentials = cdict.get("credential_definition_list", [])
        for cred in credentials:
            if cred.cred_class == CREDENTIAL.CRED_CLASS.DYNAMIC:
                error = "Provider cannot have dynamic credentials"
                LOG.error(error)
                sys.exit(error)

        # NOTE: Validation of test_account_variables >= (auth_schema_list + endpoint_schema.variables)
        # is not being done here because in some cases, endpoint variables are generated on backend &
        # are not accessible here. Hence, the validation will be done in backend & errors if any, will
        # be displayed here

        return cdict


class CloudProviderTypeValidator(PropertyValidator, openapi_type="cloud_provider"):
    __default__ = None
    __kind__ = CloudProviderType


def cloud_provider(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return CloudProviderType(name, bases, kwargs)


CloudProvider = cloud_provider()
